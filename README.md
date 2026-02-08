
# pyworxcloud Collector

A complete, standalone web-based collector for pyworxcloud.

## Features
- Web UI with explicit consent
- Session-based capture lifecycle
- Automatic expiry
- Transparent raw JSON storage
- ZIP export per session
- Docker-ready

## Security
- Credentials are never persisted
- All data collection is explicit and visible
- Sessions are time-limited

## Run
docker build -t pyworxcloud-collector .
docker run -p 8080:8080 pyworxcloud-collector
