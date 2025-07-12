# 🧩 Microservice Overview

Each service is a subclass of [MicroService](microservice/microservice.py), publishing `update` events via Redis `Pub/Sub`.

They can run continuously (recommended) or be instantiated in single-shot mode for isolated updates. Secrets and configuration are managed via [SecretManager](https://github.com/dekeyrej/secretmanager), with deployment defined in Kubernetes YAMLs.

| Service | Source File | Description | Data Source | Interval |
|---------|-------------|-------------|-------------|----------|
| AQI     | `aqi.py`    | Air quality index for configured Lat/Long | OpenWeatherMap        | 15 min   |
| Moon    | `moon.py`   | Moon phase, illumination %, sunrise/set, moonrise/set | MET Norway            | 1 hr     |
| Weather | `weather.py`| Current conditions and forecast (hourly/daily) | OpenWeatherMap     | 15 min   |
| Calendar   | `mycal.py`  | Personal calendar events (private feed) | Google Calendar        | 15 min   |
| Events  | `events.py` | Recurring family events (birthdays, anniversaries) | Static JSON or Google | 24 hr    |
| GitHub  | `github.py` | Repo activity, PR/build status         | GitHub API             | 30 min   |
| MLB     | `mlb.py`    | Baseball scores and daily schedule     | ESPN MLB API           | Variable*|
| NFL     | `nfl.py`    | Football scores and weekly schedule    | ESPN NFL API           | 5 min    |
| Garmin  | `garmin.py` | Personal Locator Beacon tracking       | Garmin location feed   | 1 hr     |

---

### ⚾ MLB Polling Logic

The MLB microservice follows a dynamic update cycle:

- **11:30 AM EDT** – wakes and checks the day’s schedule  
- **Pre-game** – sleeps until the first game starts  
- **During games** – polls every 30 seconds  
- **Post-game** – sleeps until 11:30 AM the next day

### 🧭 Related Repositories
-  – Flexible configuration reader for secrets and environment management
-  – This repo: multi-source data broadcaster for smart displays
-  – State-storer records broadcast updates
-  – API Server which feeds the Display renderer and Frontend  Webdisplay 
-  – Display renderer for RGB matrices and static BMP output
-  – Frontend WebDisplay for rendering data in real time
-  – Infrastructure automation for provisioning, deploying, and maintaining the stack
