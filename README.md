
# pyworxcloud Collector (Production)

Standalone web-based collector with live pyworxcloud integration.

## Features
- Live login to Worx/Positec via pyworxcloud
- Session-based capture
- Periodic polling of mower status
- Transparent JSON storage
- ZIP export per session
- Docker + docker-compose ready
- Persistent storage via volume mapping

## Run
docker-compose up -d
Open http://localhost:8080

## Storage
All collected data is stored under ./data/sessions/
