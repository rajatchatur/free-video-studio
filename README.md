# Free Video Studio

A local, free video editor that runs on Windows and on MacBook M1/M2/M3. Nothing needs a paid account or a credit card.

## What it uses

| Part | Source | License | Role |
|---|---|---|---|
| Hyperframes | github.com/heygen-com/hyperframes | Apache 2.0 | Renders HTML compositions to MP4 |
| Hyperframes skills (`three`, `gsap`, `hyperframes-media`) | same repo, `npx skills add heygen-com/hyperframes` | Apache 2.0 | Three.js scenes, animation, TTS and transcription helpers |
| Motion skills | github.com/iart-ai/motion-skills (about 50 skills in 14 packs) | check repo | Motion-graphics prompts and patterns |
| Claude motion toolkit | github.com/whaleyxbt/claude-motion | check repo | Motion design layer with a sound engine |
| Whisper | faster-whisper (github.com/SYSTRAN/faster-whisper) | MIT | Speech-to-text captions |
| Openverse | api.openverse.org | open-license media | Free CC0 / CC-BY images and audio |
| earshot | github.com/Leonxlnx/earshot | MIT | Code-made sound effects, no downloads |
| FFmpeg | ffmpeg.org (installed by winget or brew) | LGPL/GPL | Media decoding and encoding |

Not verified: I could not find a GitHub repo called "realsfx", and I could not confirm an exact repo for "awesome claude videos skills". The closest matches I found were the community list github.com/frostant/awesome-claude-skills and the real-recording sound sets that earshot uses (Freesound, CC0). Send me the exact URLs if you have them and I will wire them in.

## Free AI models for this setup

| Job | Model | Runs on | Notes |
|---|---|---|---|
| Captions | Whisper `base` (fast) or `small` (better) | CPU, both platforms | Set with `WHISPER_MODEL` |
| Voiceover | Kokoro-82M (Apache 2.0) | CPU | Used by the `hyperframes-media` skill |
| Background removal | u2net | CPU | Used by the `hyperframes-media` skill |
| Scripting and captions text, local | Qwen2.5 7B or Llama 3.2 3B via Ollama | M1 16 GB or a PC with 16 GB RAM | Free, offline, `ollama pull qwen2.5:7b` |
| Free hosted tokens (optional) | Google AI Studio (Gemini free tier), Groq free tier, OpenRouter `:free` models, Hugging Face Inference free credits | Cloud | Limits change often. Check each site before you rely on one |

Free-tier limits and model names change. Re-check the sites above before you depend on them.

## Setup on macOS (M1 or later)

1. Open Terminal and install Xcode Command Line Tools if asked: `xcode-select --install`
2. Unzip the project and open Terminal inside the folder.
3. Run:
   ```bash
   chmod +x scripts/*.sh
   ./scripts/setup_mac.sh
   ```
4. Start the studio: `./scripts/run_mac.sh`
5. Open http://127.0.0.1:8000

Apple Silicon notes: faster-whisper runs on the CPU, which is fast enough for `base` and `small`. For faster transcription on M1 you can later swap in whisper.cpp, which uses Metal.

## Setup on Windows 10 or 11

1. Open PowerShell and allow the scripts for this session:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
2. Unzip the project, then in the folder run `.\scripts\setup_windows.ps1`. It installs FFmpeg, Node.js LTS, Python 3.12 and Git with winget.
3. Close PowerShell, open it again, and run `.\scripts\setup_windows.ps1` a second time to finish the Python and skills steps.
4. Start the studio: `.\scripts\run_windows.ps1`
5. Open http://127.0.0.1:8000

## Using the studio

1. Set a project name and upload a clip, image or audio file.
2. Transcribe a clip, then click "Use as captions" to add the lines to the timeline.
3. Search Openverse for free images or audio, and click Add. Each download adds its credit to `credits.json`.
4. Edit the timeline JSON (clips, audio, captions, duration).
5. Click Render MP4. The file appears in `projects/<name>/renders/`.

## Editing by prompt (built into the app)

Panel 5 takes a plain-language request, such as "trim to 8 seconds and add captions from the transcript". The app sends the request, the current timeline, the asset list and any transcript to a model, and writes the updated timeline back into the editor. You review it, then click Render.

Free options:
- **Ollama (default, local, offline)**: install from ollama.com, then run `ollama pull qwen2.5:7b`. Ollama must be running (`ollama serve`). Use `OLLAMA_MODEL` to change the model.
- **Gemini (free tier, cloud)**: create a key in Google AI Studio, then set `AI_PROVIDER=gemini` and `GEMINI_API_KEY=...`. Optionally set `GEMINI_MODEL`. Free-tier limits change, so check the site.

On Windows, set the variables in PowerShell before running, for example `$env:AI_PROVIDER="gemini"; $env:GEMINI_API_KEY="..."`. On macOS, use `export` in Terminal, or add the lines to `scripts/run_mac.sh`.

Limits: the model only edits the timeline. It can't create new effects. Small local models sometimes make timing mistakes, so always check the JSON before you render. Invalid output is rejected with an error, and files it invents are dropped with a warning.

## Generating clips with Higgsfield (optional, paid)

Panel 6 sends a text prompt to Higgsfield's API (Kling 2.6 Pro, text-to-video) and saves the result into `assets/`. Setup:

1. Create an account and key pair in the Higgsfield Console (console.higgsfield.ai).
2. Set the two credentials in your environment, never in the browser:
   - Windows PowerShell: `$env:HIGGSFIELD_KEY_ID="..."; $env:HIGGSFIELD_KEY_SECRET="..."`
   - macOS Terminal: `export HIGGSFIELD_KEY_ID="..."; export HIGGSFIELD_KEY_SECRET="..."`
3. Restart the studio. Generation uses your Higgsfield credits, and the public docs don't list the price per clip, so check the console before you generate a lot.

The clip's prompt and request ID are saved in `credits.json`. The model's endpoint is set in `HIGGSFIELD_MODEL_PATH` if you want a different one from the Higgsfield docs.

This is the only part of the app that is not free. Everything else runs without an account.

## Using Claude to build more

Once the skills are installed, open Claude Code in the project folder and ask, for example:
- "Using /hyperframes, add a 3D Three.js title card for the first 3 seconds."
- "Using /hyperframes-media, make a voiceover from captions/script.txt with Kokoro."

## Known limits (honest notes)

- I wrote this without running it end to end. Package installs are blocked in my sandbox, so please run `npx hyperframes lint` on a test project and report any error. The composition markup follows the Hyperframes examples, but check it against their current docs.
- The earshot command in `server.py` (`EARSHOT_CMD`) is a placeholder. Run `earshot --help` and set the correct command.
- Render time depends on your machine. A 30-second 1080p video can take several minutes on an M1 or a basic PC.
