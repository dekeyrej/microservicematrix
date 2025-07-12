# dekeyrej-microservice

**Minimalist base class for microservice servers.**

`dekeyrej-microservice` is a lightweight Python package that provides a superclass `MicroService`—designed to orchestrate real-time data collection and visual display in homelab environments. It’s built for clarity, composability, and just enough abstraction to stay out of your way.

## ✨ Why dekeyrej-microservice?

This project grew out of a desire to keep things simple—but not simplistic. In a homelab where services talk over Redis, update displays via RGB matrices, and pull secrets from Vault or Kubernetes, `dekeyrej-microservice` offers a clean interface for:

- Scheduling periodic updates
- Fetching and publishing data

## 🧱 Core Components

### `MicroService`

A base class for microservices that:

- Reads secrets from Vault, Kubernetes, or environment
- Connects to Redis
- Periodically fetches data from external APIs
- Publishes updates via Redis pub/sub
- Supports liveness probes and production/development modes

<!-- ## 🌕 Example: Moon Phase Tracker

The `examples/moon_clock/` directory (coming soon) includes:

- `MoonServer`: Fetches sun/moon data from MET Norway’s API and publishes it
- `MoonDisplay`: Renders current time, moon phase, and next moonrise/set on an RGB matrix
- `clientdisplay.py`: Drives the LED panel and handles display cycling, pause/play, and override logic via Redis -->

## 📦 Installation

```bash
pip install dekeyrej-microservice
```

## 🛠️ Usage

```python
from microservice import MicroService

class MyServer(MicroService):
    def update(self):
        # Fetch data, publish to Redis
        pass
```

## 🔐 Secrets & Config
ServerPage supports multiple secret sources from `dekeyrej-secretmanager`:
- KubeVault - encrypted Kubernetes Secrets with Vault Transit decrypt
- Kubernetes Secrets
- Vault static keys - coming soon!
- Environment variables
- Local JSON files

## 🧪 Status
This project is under active development. Expect updates, refinements, and the occasional moonbeam.

## 📄 License
MIT License. See LICENSE for details.
