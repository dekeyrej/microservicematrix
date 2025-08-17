""" data structures to implement an efficient build mechanism """
services = ['aqi', 'events', 'garmin', 'github', 'mlb',
            'moon', 'mycal', 'nfl', 'weather']

reverse_dependencies = {
    "aqi.py": "aqi",
    "utilities/ca.crt": "all",
    "events.py": "events",
    "garmin.py": "garmin",
    "github.py": "github",
    "mlb.py": "mlb",
    "moon.py": "moon",
    "mycal.py": "mycal",
    "nfl.py": "nfl",
    "Dockerfile": "all",
    "requirements.txt": "all",
    "weather.py": "weather",
    "microservice/microservice.py": "all"
}
