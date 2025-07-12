""" ... """
import json
import xml.etree.ElementTree as ET
import arrow
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class GarminServer(MicroService):
    """ ... """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)
        self.type = 'Track'
        self.url = self.secrets['garmin_url']
        del self.secrets
        # self.last_track = self.lastest_track()
        self.dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW',
                     'SW','WSW','W','WNW','NW','NNW']

    def update(self):
        """ ... """
        tnow = arrow.now().to(self.timezone)
        resp = self.fetch_raw(self.url,"Fetching Ryan's Track",
                              tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        if resp is not None:
            data = {
                'type'   : 'Track',
                'updated': self.now_str(tnow, False),
                'valid'  : self.now_str(tnow.shift(seconds=self.update_period), True),
                'values' : {}
            }
            # json_str = json.dumps(data)
            # source = xmltodict.parse(resp.content)
    # track_data = source['kml']['Document']['Folder']['Placemark'][0]['ExtendedData']['Data']
            track_data = self.xml2dict(resp.content)
            if len(track_data) < 14:
                logging.error(f'Not enough data in track: {len(track_data)}')
                return
            logging.debug(json.dumps(track_data, indent=2))
            # track_time = arrow.get(track_data[ 2]['value'],'M/D/YYYY h:mm:ss A')
            # print(arrow.now().to('US/Eastern').format('M/D/YYYY h:mm:ss A'))
            logging.info(f'{type(self).__name__} updated.')
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
            logging.debug(json.dumps(data,indent=2))
            self.r.publish('update', json.dumps(data))
            logging.info(f'{type(self).__name__} updated.')
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

    # def lastest_track(self) -> arrow:
    #     """ query to return the latest track from tracks database """
    #     result = self.dba.read('Track')
    #     if result is not None:
    #         timestr = arrow.get(result['values']['Time'],'M/D/YYYY h:mm:ss A')
    #     else:
    #         timestr = arrow.now()
    #     return timestr

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

    period = int(os.environ.get("PERIOD", '600'))
    prod = os.environ.get("PROD", '0')
    if prod == '1':
        from config import secretcfg, secretdef
    else:
        from devconfig import secretcfg, secretdef

    logging.debug(f"Starting Events Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")
    # GarminServer(period).run()
    GarminServer(period, secretcfg, secretdef).run()
