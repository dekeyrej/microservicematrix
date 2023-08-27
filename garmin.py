""" ... """
import xml.etree.ElementTree as ET
import arrow

from pages.serverpage import ServerPage

class GarminServer(ServerPage):
    """ ... """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.clear_secrets()
        self.type = 'Track'
        self.url = 'https://inreach.garmin.com/Feed/Share/RyanTrollip'
        self.last_track = self.lastest_track()
        self.dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW',
                     'SW','WSW','W','WNW','NW','NNW']

    def update(self):
        """ ... """
        tnow = arrow.now().to('US/Eastern')
        resp = self.fetch_raw(self.url,"Fetching Ryan's Track",
                              tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        if resp is not None:
            data = {}
            data['type'] = 'Track'
            data['updated'] = tnow.format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = \
                tnow.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = {}
            # json_str = json.dumps(data)
            # source = xmltodict.parse(resp.content)
    # track_data = source['kml']['Document']['Folder']['Placemark'][0]['ExtendedData']['Data']
            track_data = self.xml2dict(resp.content)
            # print(track_data)
            # track_time = arrow.get(track_data[ 2]['value'],'M/D/YYYY h:mm:ss A')
            # print(arrow.now().to('US/Eastern').format('M/D/YYYY h:mm:ss A'))
            print(f'{type(self).__name__} updated.')
            # if track_time > self.last_track:
            #     self.last_track = track_time
            # fields = [2,3,8,9,11,12,13] # [time, name, lat, long, vel, course, gps]
            data['values'][track_data[ 2]['@name']] = track_data[ 2]['value'] # Local Time
            data['values'][track_data[ 3]['@name']] = track_data[ 3]['value'] # Track Name
            data['values'][track_data[ 8]['@name']] = track_data[ 8]['value'] # Latitude
            data['values'][track_data[ 9]['@name']] = track_data[ 9]['value'] # Longitude
            data['values'][track_data[11]['@name']] = \
                self.velocity_to_kts(track_data[11]['value']) # Velocity in km/h --> kts
            data['values'][track_data[12]['@name']] = \
                self.course(track_data[12]['value']) # Course degrees converted to compass pts
            data['values'][track_data[13]['@name']] = track_data[13]['value'] # Valid GPS Fix?
            # print(json.dumps(data, indent=2))
            self.dba.write(data)
            # also dump the track to the tracks database
            ## this may not be portable for CockroachDB ##
            # self.dba["tracks"]["ryan"].insert_one(data['track'])

    def velocity_to_kts(self, velstr: str) -> float:
        """ parses string - extracting velocity in km/h and converts to nm/h (kts) """
        return float(int(float(velstr.split(" ")[0]) / 1.852 * 100.0)) / 100.0

    def course(self, crsstr:str ) -> float:
        """ course string contains heading in degrees """
        return self.deg_to_dir(float(crsstr.split(" ")[0]))

    def deg_to_dir(self, deg: float) -> str:
        """ converts degrees to 'compass points' """
        return self.dirs[round(deg/22.5) % 16]

    def lastest_track(self) -> arrow:
        """ query to return the latest track from tracks database """
        result = self.dba.read('Track')
        if result is not None:
            timestr = arrow.get(result['values']['Time'],'M/D/YYYY h:mm:ss A')
        else:
            timestr = arrow.now()
        return timestr

    def xml2dict(self,data):
        """ strips values from Garmin inReach kml data and returns them in an array """
        output = []
        tree = ET.fromstring(data)
        # print(tree)
        for child in tree.iter('{http://www.opengis.net/kml/2.2}ExtendedData'):
            for cdata in child:
                output.append({'@name': cdata.get('name'), 'value': cdata[0].text})
        return output

if __name__ == '__main__':
    import os
    import dotenv

    dotenv.load_dotenv()

    try:
        PROD = os.environ["PROD"]
        SECRETS_PATH = os.environ["SECRETS_PATH"]
    except KeyError:
        pass

    if PROD == '1':
        GarminServer(True, 601).run()
    else:
        GarminServer(False, 601, SECRETS_PATH).run()
