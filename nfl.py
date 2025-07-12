""" NFL server - reads data from ESPN scoreboard API """
# docker build --build-arg=MICROSERVICE=nfl -t 192.168.86.49:32000/nfl:registry .
# docker push 192.168.86.49:32000/nfl:registry
# kubectl rollout restart -n default deployment nfl

import json
import arrow
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class NFLServer(MicroService):
    """ ... """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)
        del self.secrets
        self.type = 'NFL'
        self.url = 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
        self.active = 0
        self.output = False

    def update(self):
        """ ... """
        now = arrow.now().to(self.timezone)
        try:
            resp = self.fetch(self.url,'Fetching NFL games',now.format('MM/DD/YYYY hh:mm A ZZZ'))
        except json.decoder.JSONDecodeError:
            logging.error("Bad response")
            resp = None
        ## JSONDecodeError or RequestsJSONDecodeError

        if resp:
            games = resp['events']
            seasonid = int(resp['leagues'][0]['season']['type']['id'])
            weekid = int(resp['week']['number'])
            tnow = arrow.now().to(self.timezone)
            self.active = 0
            data = {
                'type': self.type,
                'updated': self.now_str(tnow, False),
                'valid': self.now_str(tnow.shift(seconds=self.update_period), True),
                'values': {
                    'seasontype': resp['leagues'][0]['season']['type']['name'],
                    'weekname': resp['leagues'][0]['calendar'][seasonid -1 ]['entries'][weekid - 1]['label'],
                    'events': []
                }
            }
            game_count = len(games)
            # dow = int(now.format('d'))
            next_start = now.shift(weekday=1)
            logging.info(f'Next start: {next_start}')
            # pre_games = in_games = post_games = 0
            for game in games:
                data['values']['events'].append(self.read_event(game))
                start_time = arrow.get(game['date']).to(self.timezone)
                status = game['competitions'][0]['status']['type']['state']
                if status == 'in' or (status == 'pre' and start_time < now):  ### now have to account for postponed :-/
                    # if self.output: print(f'   in active {id}')
                    self.update_period = 59
                elif status == 'pre':
                    # if self.output: print(f'   in pre   {id}')
                    if now <= start_time < next_start:
                        # if self.output: print(f'      in next_start {id}')
                        next_start = start_time

            if self.update_period != 59: self.update_period = min((next_start - now).seconds, 15 * 60)
            logging.debug(f'In progress games: {self.active}')
            # print(json.dumps(data,indent=1)) # uncomment for local testing
            # print(f'{type(self).__name__} updated.')
            # print('write data...')
            self.r.publish('update', json.dumps(data))  # comment out for local testing
            # print('data written?')
            # write data to the database

    def read_event(self, event):
        """ ... """
        game = {}
        # game['id']    = event['id']
        game['date']  = arrow.get(event['date']).to(self.timezone).format('ddd h:mm A')
        game['fulldate']  = event['date']
        game['week']  = event['week']['number']
        game['state'] = event['competitions'][0]['status']['type']['state']   # 'pre', 'in', 'post'
        home          = event['competitions'][0]['competitors'][0]
        game['homeabrv']   = home['team']['abbreviation']
        game['homeid']     = home['team']['id']
        # hcolor             = home['team'].get('color','FFFFFF')
        # game['homecolor']  = f"#{home['team']['color']}"
        game['homecolor']  = f"#{home['team'].get('color','FFFFFF')}"
        game['homelogo']   = home['team']['logo']
        if home.get('records',None):
            game['homerecord'] = home['records'][0].get('summary','')
        else:
            game['homerecord'] = ''
        game['homescore']  = home['score']
        away          = event['competitions'][0]['competitors'][1]
        game['awayabrv'] = away['team']['abbreviation']
        game['awayid']     = away['team']['id']
        game['awaycolor']= f"#{away['team'].get('color','FFFFFF')}"
        game['awaylogo']   = away['team']['logo']
        if away.get('records',None):
            game['awayrecord'] = away['records'][0].get('summary','')
        else:
            game['awayrecord'] = ''
        # game['awayrecord'] = away['records'][0].get('summary','')
        game['awayscore']  = away['score']
        if game['state'] == 'in':
            stat = event['competitions'][0]['status']
            self.active += 1
            game['period'] = stat.get('period',"")
            game['clock']  = stat.get('displayClock',"")
            try:
                if game['clock'] == '00:00' and game['period'] == 2:
                    game['period'] = 'Halftime'
                elif game['period'] == 1:
                    game['period'] = '1st Qtr'
                elif game['period'] == 2:
                    game['period'] = '2nd Qtr'
                elif game['period'] == 3:
                    game['period'] = '3rd Qtr'
                elif game['period'] == 4:
                    game['period'] = '4th Qtr'
                elif game['period'] > 4:
                    game['period'] = 'OT'
            except:
                print("exception in stat")
            situ = event['competitions'][0]['situation']
            try:
                if situ['possession'] == game['homeid']:
                    # print('home')
                    game['possession'] = game['homeabrv']  # who is in posession
                    # print(f"{game['homeabrv']} has the ball...")
                else:
                    # print(away)
                    game['possession'] = game['awayabrv']
                    # print(f"{game['awayabrv']} has the ball...")
                logging.debug(f"{game['possession']} has the ball.")
                game['position']       = situ.get('possessionText',"")
                game['downandyardage'] = situ.get('shortDownDistanceText',"")
                game['lastplay']       = situ['lastPlay']['type'].get('text',"")
            except:
                # game['possession'] = ""
                logging.error("exception in situ")
        return game

if __name__ == '__main__':
    import os

    period = int(os.environ.get("PERIOD", '600'))
    prod = os.environ.get("PROD", '0')
    if prod == '1':
        from config import secretcfg, secretdef
    else:
        from devconfig import secretcfg, secretdef

    logging.debug(f"Starting Events Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")

    NFLServer(period, secretcfg, secretdef).run()
    