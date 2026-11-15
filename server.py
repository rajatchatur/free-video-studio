"""
Free Video Studio - local backend (Windows + macOS Apple Silicon).

Runs on your own machine. Nothing here needs a paid account.
  - Whisper (faster-whisper)  : speech-to-text -> captions
  - Openverse API             : free Creative Commons images and audio
  - earshot (optional CLI)    : generated sound effects, no downloads
  - Hyperframes (npx)         : HTML-based video renderer (Apache 2.0)
"""
import html
import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
PROJECTS = ROOT / "projects"
PROJECTS.mkdir(exist_ok=True)

app = FastAPI(title="Free Video Studio")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
app.mount("/files", StaticFiles(directory=PROJECTS), name="files")

_whisper = None


def project_dir(name: str) -> Path:
    safe = "".join(c for c in name if c.isalnum() or c in "-_") or "default"
    d = PROJECTS / safe
    (d / "assets").mkdir(parents=True, exist_ok=True)
    return d


def get_whisper():
    """Load Whisper once. 'base' is fast on an M1 or a basic PC; use 'small' for better accuracy."""
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        model_size = os.environ.get("WHISPER_MODEL", "base")
        _whisper = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _whisper


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/health")
def health():
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "node": shutil.which("node") is not None,
        "npx": shutil.which("npx") is not None,
        "earshot": shutil.which("earshot") is not None,
    }


@app.post("/api/upload/{project}")
async def upload(project: str, file: UploadFile = File(...)):
    d = project_dir(project)
    name = Path(file.filename).name
    with (d / "assets" / name).open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"path": f"assets/{name}"}


@app.get("/api/assets/{project}")
def list_assets(project: str):
    d = project_dir(project) / "assets"
    return sorted(p.name for p in d.iterdir() if p.is_file())


@app.post("/api/transcribe/{project}")
def transcribe(project: str, asset: str):
    src = project_dir(project) / asset
    if not src.exists():
        raise HTTPException(404, "asset not found")
    segments, info = get_whisper().transcribe(str(src), vad_filter=True)
    out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]
    (project_dir(project) / "transcript.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return {"language": info.language, "segments": out}


@app.get("/api/openverse/{kind}")
def openverse(kind: str, q: str, license: str = "cc0,by,by-sa"):
    """Search Openverse (free, open-license media). kind = images | audio."""
    if kind not in ("images", "audio"):
        raise HTTPException(400, "kind must be images or audio")
    r = httpx.get(
        f"https://api.openverse.org/v1/{kind}/",
        params={"q": q, "license": license, "page_size": 12},
        timeout=20,
    )
    r.raise_for_status()
    return [
        {
            "title": x.get("title"),
            "url": x.get("url"),
            "creator": x.get("creator"),
            "license": x.get("license"),
            "source_page": x.get("foreign_landing_url"),
        }
        for x in r.json().get("results", [])
    ]


@app.post("/api/fetch/{project}")
def fetch_asset(project: str, body: dict):
    """Download a result from Openverse and keep its credit line for the project."""
    url, name = body["url"], Path(body["name"]).name
    dest = project_dir(project) / "assets" / name
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    credits = project_dir(project) / "credits.json"
    entries = json.loads(credits.read_text()) if credits.exists() else []
    entries.append({"file": name, **{k: body.get(k) for k in ("title", "creator", "license", "source_page")}})
    credits.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return {"path": f"assets/{name}"}


@app.post("/api/sfx/{project}")
def make_sfx(project: str, body: dict):
    """
    Generate a sound effect with earshot (MIT, code-made sounds, no network).
    EARSHOT_CMD is a template you can change after running `earshot --help`.
    Default: earshot forge <name> --dir <out_dir>
    """
    template = os.environ.get("EARSHOT_CMD", "earshot forge {name} --dir {out_dir}")
    out_dir = project_dir(project) / "assets" / "sfx"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = template.format(name=shlex.quote(body["name"]), out_dir=shlex.quote(str(out_dir)))
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    if p.returncode:
        raise HTTPException(500, p.stderr[-2000:] or "earshot failed - check EARSHOT_CMD")
    return {"output_dir": f"assets/sfx", "log": p.stdout[-500:]}


def build_composition(name: str, body: dict) -> str:
    """Turn the editor's timeline JSON into a Hyperframes HTML composition."""
    W = int(body.get("width", 1920))
    H = int(body.get("height", 1080))
    D = float(body.get("duration", 10))
    parts = []
    for i, c in enumerate(body.get("clips", [])):
        parts.append(
            f'<video id="clip-{i}" data-start="{c["start"]}" data-duration="{c["duration"]}" '
            f'data-track-index="0" src="{html.escape(c["src"])}" muted playsinline></video>'
        )
    for i, a in enumerate(body.get("audio", [])):
        parts.append(
            f'<audio id="audio-{i}" data-start="{a["start"]}" data-duration="{a["duration"]}" '
            f'data-track-index="{2 + i}" src="{html.escape(a["src"])}"></audio>'
        )
    for i, t in enumerate(body.get("captions", [])):
        parts.append(
            f'<div id="cap-{i}" class="cap" data-start="{t["start"]}" data-duration="{t["duration"]}" '
            f'data-track-index="1">{html.escape(t["text"])}</div>'
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body {{ margin: 0; background: #000; }}
  #stage {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; background: #000; color: #fff;
            font-family: system-ui, sans-serif; }}
  video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  .cap {{ position: absolute; left: 5%; right: 5%; bottom: 8%; text-align: center;
          font-size: {max(24, H // 22)}px; font-weight: 700; text-shadow: 0 2px 8px #000; }}
</style></head>
<body>
<div id="stage" data-composition-id="{html.escape(name)}" data-start="0" data-width="{W}" data-height="{H}" data-duration="{D}">
{chr(10).join(parts)}
</div>
</body></html>"""


@app.post("/api/render/{project}")
def render(project: str, body: dict):
    pdir = project_dir(project)
    (pdir / "index.html").write_text(build_composition(project, body), encoding="utf-8")
    cmd = ["npx", "hyperframes", "render", "--quality", body.get("quality", "standard")]
    p = subprocess.run(cmd, cwd=pdir, capture_output=True, text=True,
                       shell=(os.name == "nt"), timeout=3600)
    if p.returncode:
        raise HTTPException(500, (p.stderr or p.stdout)[-3000:])
    renders = sorted((pdir / "renders").glob("*.mp4"), key=os.path.getmtime) if (pdir / "renders").exists() else []
    if not renders:
        raise HTTPException(500, "render finished but no MP4 found in renders/")
    return {"file": f"/files/{project}/renders/{renders[-1].name}"}


SCHEMA_HELP = """You edit a video timeline for a local video editor.
Reply with ONLY one JSON object, no prose, using these keys:
  width (int), height (int), duration (number, seconds),
  quality ("draft" | "standard" | "high"),
  clips:    [{"src": "assets/<file>", "start": number, "duration": number}],
  audio:    [{"src": "assets/<file>", "start": number, "duration": number}],
  captions: [{"start": number, "duration": number, "text": string}]
Rules:
- Times are seconds. Keep every item inside the total duration.
- Use only src paths that appear in the ASSETS list. Never invent files.
- You receive the CURRENT TIMELINE. Change only what the REQUEST asks for and keep the rest.
- If the REQUEST asks for captions, use the TRANSCRIPT timings when it is provided."""


def _ai_context(project: str):
    d = project_dir(project)
    assets = sorted(p.name for p in (d / "assets").iterdir() if p.is_file())
    tp = d / "transcript.json"
    transcript = tp.read_text(encoding="utf-8")[:6000] if tp.exists() else ""
    return assets, transcript


def _call_ollama(system: str, user: str) -> str:
    base = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    r = httpx.post(
        f"{base}/api/chat",
        json={
            "model": os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _call_gemini(system: str, user: str) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise HTTPException(500, "GEMINI_API_KEY is not set. Add it to your environment or use AI_PROVIDER=ollama.")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": key},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _validate_timeline(tl, assets):
    """Keep only well-formed items that point at real files. Returns (timeline, warnings)."""
    if not isinstance(tl, dict):
        raise ValueError("model did not return a JSON object")
    W = int(tl.get("width", 1920))
    H = int(tl.get("height", 1080))
    D = float(tl.get("duration", 10))
    quality = tl.get("quality", "standard")
    if quality not in ("draft", "standard", "high"):
        quality = "standard"
    known = {f"assets/{a}" for a in assets}
    warnings = []
    out = {"width": W, "height": H, "duration": D, "quality": quality, "clips": [], "audio": [], "captions": []}

    for key in ("clips", "audio"):
        for item in tl.get(key, []) or []:
            src = str(item.get("src", ""))
            if src not in known:
                warnings.append(f"{key}: dropped unknown file '{src}'")
                continue
            out[key].append({"src": src, "start": float(item.get("start", 0)),
                             "duration": float(item.get("duration", D))})

    for cap in tl.get("captions", []) or []:
        text = str(cap.get("text", "")).strip()
        if text:
            out["captions"].append({"start": float(cap.get("start", 0)),
                                    "duration": max(0.5, float(cap.get("duration", 2))), "text": text})
    return out, warnings


@app.post("/api/ai/timeline/{project}")
def ai_edit(project: str, body: dict):
    """Turn a plain-language request into an updated timeline. Nothing renders until you click Render."""
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "prompt is empty")
    assets, transcript = _ai_context(project)
    user = (
        f"REQUEST:\n{prompt}\n\n"
        f"ASSETS:\n{json.dumps(['assets/' + a for a in assets])}\n\n"
        f"TRANSCRIPT (may be empty):\n{transcript}\n\n"
        f"CURRENT TIMELINE:\n{json.dumps(body.get('timeline', {}))}"
    )
    provider = os.environ.get("AI_PROVIDER", "ollama").lower()
    try:
        raw = _call_gemini(SCHEMA_HELP, user) if provider == "gemini" else _call_ollama(SCHEMA_HELP, user)
    except httpx.ConnectError:
        raise HTTPException(503, "Ollama is not running. Start it (ollama serve) or set AI_PROVIDER=gemini.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"AI provider error: {e.response.text[:500]}")
    try:
        timeline, warnings = _validate_timeline(json.loads(raw), assets)
    except (ValueError, KeyError, TypeError) as e:
        raise HTTPException(502, f"model returned an invalid timeline: {e}")
    return {"timeline": timeline, "warnings": warnings, "provider": provider}


HF_BASE = "https://api.higgsfield.ai"
# Endpoint verified against docs.higgsfield.ai (Kling 2.6 Pro, text-to-video). Override with HIGGSFIELD_MODEL_PATH.
HF_MODEL_PATH = os.environ.get("HIGGSFIELD_MODEL_PATH", "kling-video/v2.6/pro/text-to-video")


@app.post("/api/higgsfield/{project}")
def higgsfield_generate(project: str, body: dict):
    """
    OPTIONAL paid add-on. Needs your own Higgsfield key (HIGGSFIELD_KEY_ID and HIGGSFIELD_KEY_SECRET).
    Generates a clip from a text prompt, waits for it, and saves it to assets/ with provenance in credits.json.
    Charges your Higgsfield account. The app cannot show the price because it is not in the public docs.
    """
    key_id = os.environ.get("HIGGSFIELD_KEY_ID")
    secret = os.environ.get("HIGGSFIELD_KEY_SECRET")
    if not key_id or not secret:
        raise HTTPException(500, "Higgsfield is not configured. Set HIGGSFIELD_KEY_ID and HIGGSFIELD_KEY_SECRET (paid service).")

    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "prompt is empty")
    duration = int(body.get("duration", 5))
    if duration not in (5, 10):
        raise HTTPException(400, "duration must be 5 or 10 seconds for this model")
    aspect = body.get("aspect_ratio", "16:9")
    if aspect not in ("16:9", "9:16", "1:1"):
        raise HTTPException(400, "aspect_ratio must be 16:9, 9:16 or 1:1")
    sound = body.get("sound", "off")
    if sound not in ("on", "off"):
        raise HTTPException(400, "sound must be on or off")

    auth = {"Authorization": f"Key {key_id}:{secret}"}
    payload = {"prompt": prompt, "duration": duration, "aspect_ratio": aspect, "sound": sound}
    try:
        r = httpx.post(f"{HF_BASE}/{HF_MODEL_PATH}",
                       headers={**auth, "Idempotency-Key": str(uuid.uuid4())},
                       json=payload, timeout=60)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"Higgsfield rejected the request: {e.response.text[:500]}")
    submitted = r.json()
    status_url = submitted["status_url"]
    request_id = submitted.get("request_id")

    deadline = time.time() + 900  # 15 minutes
    video_url = None
    while time.time() < deadline:
        s = httpx.get(status_url, headers=auth, timeout=30).json()
        st = s.get("status")
        if st == "completed":
            video_url = s["video"]["url"]
            break
        if st in ("failed", "nsfw", "canceled"):
            raise HTTPException(502, f"Higgsfield request {request_id} ended with status: {st}")
        time.sleep(5)
    if not video_url:
        raise HTTPException(504, f"Timed out waiting. Request id: {request_id}")

    name = f"hf-{request_id or uuid.uuid4().hex[:8]}.mp4"
    dest = project_dir(project) / "assets" / name
    with httpx.stream("GET", video_url, follow_redirects=True, timeout=300) as dl:
        dl.raise_for_status()
        with dest.open("wb") as f:
            for chunk in dl.iter_bytes():
                f.write(chunk)

    credits = project_dir(project) / "credits.json"
    entries = json.loads(credits.read_text()) if credits.exists() else []
    entries.append({"file": name, "source": "Higgsfield (generated)", "request_id": request_id,
                    "prompt": prompt, "license": "Higgsfield terms of service"})
    credits.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return {"path": f"assets/{name}", "request_id": request_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
