""" data structures to implement an efficient build mechanish """
services = ['aqi', 'calendar', 'garmin', 'github', 'jenkins', 'mlb', 'moon', 'events', 'weather']

reverse_dependencies = {
    "aqi.py": "aqi",
    "requirements-pandas.txt": "aqi",
    "calendar.py": "calendar",
    "garmin.py": "garmin",
    "github.py": "github",
    "jenkins.py": "jenkins",
    "mlb.py": "mlb",
    "moon.py": "moon",
    "events.py": "events",
    "Dockerfile": "all",
    "requirements.txt": "all",
    "weather.py": "weather"
}
