
# pyworxcloud Data Collector

Standalone, web-based data collector built on top of the pyworxcloud library.

This project collects live data from Positec mower cloud services for:
- Worx Landroid
- Kress
- LandXcape

## Facts

- Credentials are NEVER stored
- Credentials are used only in memory
- Credentials are discarded immediately when a session ends
- Data collection is explicit and session-based
- Each session is isolated
- Data is stored locally and can be downloaded as ZIP

## Requirements

- Docker
- Docker Compose v2

## Running

```bash
docker compose up -d --build
```

## Access

The web UI is available at:

```
http://<host>:8088
```

## Storage

Collected data is stored under:

```
./data/sessions/
```

This directory is mapped as a persistent volume.

## Security model

- No credential persistence
- No background access after session stop
- No hidden data collection
