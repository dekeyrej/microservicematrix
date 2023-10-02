""" data structures to implement an efficient build mechanish """
services = ['aqi', 'events', 'garmin', 'github', 'jenkins', 'mlb', 'moon', 'mycal', 'nfl', 'weather']

reverse_dependencies = {
    "aqi.py": "aqi",
    "requirements-pandas.txt": "aqi",
    "events.py": "events",
    "garmin.py": "garmin",
    "github.py": "github",
    "jenkins.py": "jenkins",
    "mlb.py": "mlb",
    "moon.py": "moon",
    "mycal.py": "mycal",
    "nfl.py": "nfl",
    "Dockerfile": "all",
    "requirements.txt": "all",
    "weather.py": "weather"
}
