# microservicematrix
Microservices Implementation of the matrix server

<b>Overall project intent</b>: Consume various local and internet data sources and display on a 128x64 pixel RGB LED matrix (quad sized tidbyt).

Microservice servers to feed a Software interface to the RGB Matrix is via the python bindings provided by https://github.com/hzeller/rpi-rgb-led-matrix. Bitmap fonts are from this repository as well.

Implemented by 'Strangling' the kubematrix code base - 
- Peeling off each of the 'servers'
- Making modifications as required to run standalone
- Creating a copy of the Dockerfile for each
- Testing, and when successful
- Commenting it out of the kubematrix monolith

Allow the way, pulled several (3) packages of code out and published them to PyPI dekeyrej-datasource, -securedict, and -pages

Current project (this repository): Refactor the server-side into several independent microservice servers to fetch data from various public and private data sources, and stores the results in a database.  The microservices are containerized, and the containers and database are run in a local kubernetes cluster.
- Display size: 128 x 64 pixels, 24-bit color (4 x 64x32 pixel panels in series)
- Microservices implemented.  Air Quality, Google Calendar, Garmin tracker, GitHub commit watcher, Jenkins build watcher, MLB, Moon/Sun data, 'Family' events, and Open Weather Map server (current, hourly, daily). All but (kubematrix) NFL/World Cup data sources are operational.
- Supports writing/reading SQLite, MongoDB, and Postgres-like databases (SQLite, Postgres and CockroachDB tested).
- (client in kubematrix) Python/RGBmatrix database client implemented. All but NFL/WC data classes operational.
- (client in kubematrix) Command line argument to allow running with or without an RGB Matrix attached (for testing).

Previous project: Refactor client/server to communicate via a database and run dataserver and database in a kubernetes cluster.
- Display size: 128 x 64 pixels, 24-bit color (4 x 64x32 pixel panels in series)
- Dataserver implemented.  All but NFL/World Cup data class operational.
- supports writing/reading SQLite, MongoDB, and Postgres-like databases (Postgres and CockroachDB tested).
- Python/RGBmatrix database client implemented. All but NFL/WC data classes operational.
- Command line argument to allow running with or without an RGB Matrix attached (for testing).

Previous project: Refactor client/server http transport to websocket-based. Added some browser based views for remote viewing
- Display size: 128 x 64 pixels, 24-bit color (4 x 64x32 pixel panels in series)
- Websocket server implemented.  All but MLB data class operational.
- Python/RGBmatrix websocket client implemented. All but MLB data class operational. Added command line argument to allow running with or without an RGB Matrix attached.
- HTML/JavaScript websocket client implemented for World Cup.

Previous version: Refactored mostly monolithic client with one external data server into a fully bifurcted client and dataserver.
- Display size: 128 x 64 pixels, 24-bit color (4 x 64x32 pixel panels in series)
- Local Data streams: Clock, 'Family' events
- Remote data stream: Google Calendar events, OpenWeatherMap current + forecast + hourly weather, Moon/Sun events, NFL, World Cup 2022

Previous version: Mostly monolithic client with one external data server
- Display size: 128 x 64 pixels, 24-bit color (4 x 64x32 pixel panels in series)
- Local Data streams: MLB, Clock, Google Calendar events, OpenWeatherMap current + forecast + hourly weather, Moon/Sun events
- Remote data stream: NFL (JSON-LD format takes quite a while to resolve)

Previous version: Fully monolithic display running on a Raspberry Pi 3A+
- Display size: 128 x 64 pixels, 24-bit color (4 x 64x32 pixel panels in series)
- Data streams: MLB, Clock, Google Calendar events, OpenWeatherMap current + forecast + hourly weather, Moon/Sun events (adapted from: Moon Phase Clock for Adafruit Matrix Portal - By Phillip Burgess)

Initial version: Fully monolithic display written in Circuit Python and running on a ESP32S3 microcontroller
- Display size: 64 x 32 pixels, 4-bit color
- Data stream: daily Boston Red Sox game
