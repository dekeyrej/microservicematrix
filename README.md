# 🎛️ microservicematrix

![MIT License](https://img.shields.io/github/license/dekeyrej/microservicematrix)
![Last Commit](https://img.shields.io/github/last-commit/dekeyrej/microservicematrix)
![Repo Size](https://img.shields.io/github/repo-size/dekeyrej/microservicematrix)

**microservicematrix** is a modular suite of Python-based microservices that collect, normalize, and publish data from various internet and local sources—designed for a 128×64 RGB LED matrix (Tidbyt-style) but decoupled for flexible display targets.

Extracted data is transformed and then published as `update` events via Redis `Pub/Sub`. Consumers like [matrixclient](https://github.com/dekeyrej/matrixclient) and [nodewebdisplay](https://github.com/dekeyrej/nodewebdisplay) render the content in real time or generate static BMPs for testing and archival.

All services are containerized for Kubernetes deployment and are tightly integrated with:

- 🔑 [`secretmanager`](https://github.com/dekeyrej/secretmanager) – secure, multi-source config management (available on [PyPI](https://pypi.org/project/dekeyrej-secretmanager))
- 🧩 [`MicroService`](microservice/README.md) – uniform abstraction for service logic and configuration

---

## 📋 Service Overview

Each service is a subclass of [`MicroService`](microservice/microservice.py), and can run as a long-lived process or invoked in one-shot mode. Configuration is sourced via [`secretmanager`](https://github.com/dekeyrej/secretmanager) and managed using Kubernetes secrets and YAML deployments.

| Service | Source File | Description | Data Source | Interval |
|---------|-------------|-------------|-------------|----------|
| AQI     | `aqi.py`    | Air quality index for configured Lat/Long | OpenWeatherMap        | 15 min   |
| Moon    | `moon.py`   | Moon phase, illumination %, sunrise/set, moonrise/set | MET Norway     | 1 hr     |
| Weather | `weather.py`| Current conditions and forecast (hourly/daily) | OpenWeatherMap     | 15 min   |
| MyCal   | `mycal.py`  | Personal calendar events (private feed) | Google Calendar      | 15 min   |
| Events  | `events.py` | Recurring family events (birthdays, anniversaries) | Static JSON or Google | 24 hr    |
| GitHub  | `github.py` | Repo activity, PR/build status         | GitHub API             | 30 min   |
| MLB     | `mlb.py`    | Baseball scores and daily schedule     | ESPN MLB API           | Variable*|
| NFL     | `nfl.py`    | Football scores and weekly schedule    | ESPN NFL API           | 5 min    |
| Garmin  | `garmin.py` | Personal Locator Beacon tracking       | Garmin location feed   | 1 hr     |

> **\*** _MLB polling logic:_  
> At **11:30 AM EDT**, the service checks the day's schedule. It then:
> - Sleeps until the first game starts  
> - Polls every 30 seconds during games  
> - Sleeps again after the final game ends

---

## 🚀 Quick Start (Dev)

Each service will run politely from the commandline - writing to its configured database and pushing Redis updates (if desired).

```bash
git clone https://github.com/dekeyrej/microservicematrix
cd microservicematrix
# normal virtual environment tasks
python moon.py
```

To build and push the container images you can either modify the github/workflows for your environment, or use `build.sh` and `builds.txt` in the utilities folders. `Build.sh` reads `builds.txt` (which is simply a list of the services to build) and builds an image and pushes it to the registry of your choice.

Once pushed, the microservices can be deployed with:

```bash
kubectl apply -f yaml/
```
Secrets can be passed via secrets.json, .env, Kubernetes secrets, or AES-256 encrypted Kubernetes secrets Vault Transit decrypted - depending on your SecretManager configuration.

### 🌐 Related Repositories
-  – [Service abstraction layer and CLI-ready page system](https://github.com/dekeyrej/plain_pages/blob/main/plain_pages/serverpage.py)
-  – [Lightweight multi-backend data access and persistence](https://github.com/dekeyrej/datasource)
-  – [Unified API for secrets from env, file, or Kubernetes](https://github.com/dekeyrej/secretmanager)
-  – [RGB LED matrix renderer (hardware and BMP mode)](https://github.com/dekeyrej/plain_pages/blob/main/plain_pages/displaypage.py)
-  – [Frontend for live display via SSE/Redis](https://github.com/dekeyrej/nodewebdisplay)
-  – [Homelab orchestration and provisioning roles/playbooks](https://github.com/dekeyrej/ansible)

<details>
<summary><strong>📜 Project Evolution</strong></summary>

- Initial – Single-service Red Sox game display on ESP32 with CircuitPython

- V1 – Monolithic Pi client with local and remote data streams

- V2 – Split into client/server with basic data transport

- V3 – WebSocket support and browser-based clients

- V4 – Migration to database-centric transport with Docker & Kubernetes

- Current – Modular Python microservices with CLI, Redis pub/sub, and multiple display targets
</details>
