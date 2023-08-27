""" Data used by aqiserver.py """
# OWM also returns "no" and "nh3", but I have no guidance for them
pollutants = ["o3", "pm2_5", "pm10", "co", "so2", "no2"]
"""
https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
"""
pollutant_measures = {
    "o3":    {"name": "Ozone", "weight": 47.998, "units": "ppb",   "decimals": 0}, 
    "pm2_5": {"name": "Particulate Matter (2.5 microns)", "weight": 1, "units": "ug/m3", 
              "decimals": 1}, 
    "pm10":  {"name": "Particulate Matter (10 microns)", "weight": 1, "units": "ug/m3", 
              "decimals": 0}, 
    "co":    {"name": "Carbon Monoxide", "weight": 28.01, "units": "ppm",   "decimals": 1}, 
    "so2":   {"name": "Sulfur Dioxide", "weight": 64.065, "units": "ppb",   "decimals": 0}, 
    "no2":   {"name": "Nitrogen Dioxide", "weight": 46.006, "units": "ppb",   "decimals": 0}
}

dfindex = ["1", "2", "3", "4", "5", "6"]
"""
https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
"""
aqidata = {
    "aqi_adjective": ["Good", "Moderate", "Unhealthy for Sensitive Groups", 
                      "Unhealthy", "Very Unhealthy", "Hazardous"], 
    "aqi_color":     ["(0,228,0)", "(255,255,0)", "(255,126,0)", 
                      "(255,0,0)", "(143,63,151)", "(126,0,35)"], 
    "aqi_low":  [0, 51, 101, 151, 201, 301], 
    "aqi_high": [50, 100, 150, 200, 300, 500], 
    "o3_low":  [0, 55, 71, 86, 106, 201], 
    "o3_high": [54, 70, 85, 105, 200, 500], 
    "pm2_5_low":  [0, 12.1, 35.5, 55.5, 150.5, 250.5], 
    "pm2_5_high": [12, 35.4, 55.4, 150.4, 250.4, 500.4], 
    "pm10_low":  [0, 55, 155, 255, 355, 425], 
    "pm10_high": [54, 154, 254, 354, 424, 604], 
    "co_low":  [0, 4.5, 9.5, 12.5, 15.5, 30.5], 
    "co_high": [4.4, 9.4, 12.4, 15.4, 30.4, 50.4], 
    "so2_low":  [0, 36, 76, 186, 305, 605], 
    "so2_high": [35, 75, 184, 304, 604, 1004], 
    "no2_low":  [0, 54, 101, 361, 650, 1250], 
    "no2_high": [53, 100, 360, 649, 1249, 2049]
}
