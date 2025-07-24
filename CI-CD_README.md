# 🛠️ Smart CI for Microservices, the Minimalist Way

## 1. Why This Exists

- The motivation: avoid duplicative Dockerfiles and wasteful builds

- The philosophy: modular design, resource respect, and DX clarity

“I hate duplicate files that differ by one word. I dislike wasting build minutes or developer attention on unchanged services. So I built a CI workflow that thinks before it builds.”

## 2. Design Overview

- One Dockerfile powered by --build-arg per service

- Microservice list inferred from file changes

- Custom utility: latest_and_last_successful.py pulls from GitHub API to compare commits

- GHCR authentication and repo linkage handled cleanly

## 3. Workflow Details

- `build_apps.yaml` triggers on workflow_dispatch (or push, optionally)

- Step 1: Determine modified services

- Step 2: Conditionally run a build matrix

- Step 3: Push each tagged image to GHCR

## 4. Developer Ergonomics

- Built-in debug toggles via DEBUG_FORCE_APPS

- Easy override support for manual dispatches

- Environment variables and summary logs for CI transparency

## 5. GHCR Quirks and Solutions

- GHCR permissions post-publication

- Package visibility and repo linkage

- Clean slate strategy for old image versions

## 6. Lessons Learned

- Don’t assume SHA shortening will behave

- GitHub runners need full clone depth for diffing

- Treat CI as code — make it self-aware, testable, and respectful of its environment

## 7. Future Ideas

- Composite GitHub Action for reusable diff+build orchestration

- Scheduled health builds

- Slack/webhook notifications for deployment rollouts

[GitHub Gist](https://gist.github.com/dekeyrej/cc209ffe55eab3dc99ce5198f61c100b)