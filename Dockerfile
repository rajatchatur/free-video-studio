# Free Video Studio - runs the same on Windows, macOS and Linux.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WHISPER_MODEL=base \
    HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium

# System tools: FFmpeg for video, Node.js 22 for Hyperframes
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates gnupg chromium fonts-liberation \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Hyperframes renderer (pinned so the image behaves the same every time)
RUN npm install -g hyperframes@0.9.58

# Python packages (faster-whisper and av are installed together so they match)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt faster-whisper av

# Download the speech model at build time so the first transcription works offline
RUN python -c "import os; from faster_whisper import WhisperModel; WhisperModel(os.environ['WHISPER_MODEL'], device='cpu', compute_type='int8')"

COPY . .

EXPOSE 8000
CMD ["python", "server.py"]
