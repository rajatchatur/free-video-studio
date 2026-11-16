# Free Video Studio: Usage Guide

Free Video Studio is a local video editor. It runs on your own computer, on Windows 10/11 or a MacBook with M1/M2/M3, and you open it in a browser at http://127.0.0.1:8000. No paid account or credit card is needed, except for the optional Higgsfield clip generator.

## 1. Before you start

- Windows: run `scripts\setup_windows.ps1` once. Run it a second time after the first run finishes, so the Python and skill steps complete. See the README for the exact commands.
- macOS: run `scripts/setup_mac.sh` once.
- Optional AI editing: install Ollama from ollama.com and run `ollama pull qwen2.5:7b`. Or get a free Gemini key from Google AI Studio.

## 2. Start the studio

- Windows (PowerShell, in the project folder):
  ```powershell
  .\scripts\run_windows.ps1
  ```
- macOS (Terminal, in the project folder):
  ```bash
  ./scripts/run_mac.sh
  ```

Then open http://127.0.0.1:8000 in your browser. Keep the terminal window open while you work.

## 3. Create a project and add media

1. Enter a project name.
2. Upload a video, image or audio file.
3. Your files are stored in `projects/<name>/` and `assets/`.

## 4. Add captions

1. Transcribe your clip. Captions use Whisper (`base` for speed, `small` for better accuracy, set with `WHISPER_MODEL`).
2. Click **Use as captions** to add the lines to the timeline.

## 5. Add free images and sounds

1. Search Openverse for free CC0 or CC-BY images and audio.
2. Click **Add**. The credit for each item is saved to `credits.json`. Keep this file if you publish your video.

## 6. Edit the timeline

The timeline is a JSON file. You can change:
- clips (start, end, position)
- audio
- captions
- total duration

## 7. Edit by prompt (panel 5)

Type a plain-language request, such as:
- `trim to 8 seconds and add captions from the transcript`

The app sends your request, the timeline, the asset list and any transcript to the AI model. It then writes the updated timeline into the editor.

1. Review the changed timeline.
2. Click **Render** when it looks right.

Tips:
- The AI can only edit the timeline. It cannot invent new effects.
- Small local models sometimes make timing mistakes, so check the JSON before you render.
- Invalid AI output is rejected with an error, and files it makes up are dropped with a warning.

To change the AI provider:
- **Ollama (default, offline):** run `ollama serve`. Change the model with `OLLAMA_MODEL`.
- **Gemini (free tier, online):** set `AI_PROVIDER=gemini` and `GEMINI_API_KEY`. Free limits change, so check Google AI Studio.

On Windows, set the variables in PowerShell before you start the studio:
```powershell
$env:AI_PROVIDER="gemini"; $env:GEMINI_API_KEY="your-key"
```
On macOS, use `export` in Terminal.

## 8. Generate clips with Higgsfield (panel 6, optional, paid)

1. Create an account and key pair in the Higgsfield Console (console.higgsfield.ai).
2. Set the credentials in your environment, not in the browser:
   - Windows: `$env:HIGGSFIELD_KEY_ID="..."; $env:HIGGSFIELD_KEY_SECRET="..."`
   - macOS: `export HIGGSFIELD_KEY_ID="..."; export HIGGSFIELD_KEY_SECRET="..."`
3. Restart the studio. Type a text prompt and generate. The clip is saved to `assets/`.

Generation uses your Higgsfield credits. Check the price in the console before you generate many clips. The prompt and request ID are saved in `credits.json`.

## 9. Render the video

1. Click **Render MP4**.
2. Find the file in `projects/<name>/renders/`.

Render time depends on your computer. A 30-second 1080p video can take several minutes on an M1 or a basic PC.

## 10. Troubleshooting

| Problem | What to do |
|---|---|
| Studio doesn't open | Check that the terminal shows it is running, then reopen http://127.0.0.1:8000. |
| Setup script fails | Run the setup script again. On Windows, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first. |
| AI edit does nothing | Check that Ollama is running (`ollama serve`) or that your Gemini key is set. |
| Invalid timeline after an AI edit | Ask again with a simpler request, or fix the JSON by hand. |
| Earshot sound effects fail | The `EARSHOT_CMD` setting in `server.py` is a placeholder. Run `earshot --help` and set the correct command. |
| Render is very slow | Use a shorter clip or a lower resolution. |

## 11. Notes

- This guide follows the project README. The project has not been tested end to end, so run a short test project first and report any errors.
- Keep your API keys out of the project files. Set them as environment variables only.

## 12. Ubuntu setup (22.04 or 24.04, untested)

The project includes setup scripts for macOS and Windows only. These are the manual steps for Ubuntu. I haven't run them on Ubuntu, so report any error you see.

1. Install the system packages:
   ```bash
   sudo apt update
   sudo apt install -y ffmpeg git python3.12 python3.12-venv
   ```
   On Ubuntu 22.04, `python3.12` may not be in the default repositories. Add the deadsnakes PPA first: `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update`.
2. Install Node.js 22 LTS. Use NodeSource, or any method that gives Node 22 or newer:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
   sudo apt install -y nodejs
   ```
3. Open a terminal in the project folder and create the Python environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Install the Hyperframes skills (free):
   ```bash
   npx --yes hyperframes doctor || true
   npx skills add heygen-com/hyperframes
   ```
5. Start the studio:
   ```bash
   source .venv/bin/activate
   export WHISPER_MODEL=base
   python server.py
   ```
6. Open http://127.0.0.1:8000 in your browser and keep the terminal open.

Ubuntu notes:
- The Whisper model downloads on first use, so the first transcription needs an internet connection.
- To use Ollama for AI editing, install it from ollama.com, run `ollama pull qwen2.5:7b`, and keep `ollama serve` running in another terminal.
- To start the studio again later, run only steps 5 and 6.

## 13. Ubuntu quick commands (untested)

Run these in a terminal inside the project folder. Replace `~/free-video-studio` with the folder where you unzipped or cloned the project.

**Start the studio**
```bash
cd ~/free-video-studio
source .venv/bin/activate
export WHISPER_MODEL=base
python server.py
```
Then open http://127.0.0.1:8000 in Firefox or Chrome.

**Stop the studio**
Press `Ctrl+C` in the terminal where it is running.

**Start the optional Ollama AI (for prompt editing)**
Open a second terminal and run:
```bash
ollama serve
```
Leave it running. In the first terminal, start the studio as above.

**Check that Ollama has the model**
```bash
ollama list
```
If `qwen2.5:7b` is missing, run `ollama pull qwen2.5:7b`.

**Make a video, step by step in the browser**
1. Enter a project name and upload a clip.
2. Transcribe it, then click **Use as captions** (optional).
3. Type a request in panel 5, such as `trim to 8 seconds and add captions`, and let the AI update the timeline. Check the JSON.
4. Click **Render MP4**.
5. Find the video in `projects/<your-project>/renders/`:
   ```bash
   ls ~/free-video-studio/projects/<your-project>/renders/
   ```

**Set a Higgsfield key (optional, paid)**
Set the keys in the terminal before starting the studio:
```bash
export HIGGSFIELD_KEY_ID="your-id"
export HIGGSFIELD_KEY_SECRET="your-secret"
```

**Use Gemini instead of Ollama (optional, free tier)**
```bash
export AI_PROVIDER=gemini
export GEMINI_API_KEY="your-key"
```
