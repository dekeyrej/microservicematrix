""" NFL server - reads data from ESPN scoreboard API """
# docker build --build-arg=MICROSERVICE=nfl -t 192.168.86.49:32000/nfl:registry .
# docker push 192.168.86.49:32000/nfl:registry
# kubectl rollout restart -n default deployment nfl

import json
import arrow
from pages.serverpage import ServerPage

class NFLServer(ServerPage):
    """ ... """
    def __init__(self, prod, period, path: str=None):
        """ ... """
        super().__init__(prod, period, path)
        self.clear_secrets()
        self.type = 'NFL'
        self.url = 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
        self.active = 0
        self.output = False

    def update(self):
        """ ... """
        now = arrow.now().to('US/Eastern')
        try:
            resp = self.fetch(self.url,'Fetching NFL games',now.format('MM/DD/YYYY hh:mm A ZZZ'))
        except json.decoder.JSONDecodeError:
            print("Bad response")
            resp = None
        ## JSONDecodeError or RequestsJSONDecodeError

        if resp:
            games = resp['events']
            self.active = 0
            data = {}
            data['type'] = self.type
            data['updated'] = now.format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = \
                now.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = []
            game_count = len(games)
            # dow = int(now.format('d'))
            next_start = now.shift(weekday=1)
            print(next_start)
            # pre_games = in_games = post_games = 0
            for game in games:
                data['values'].append(self.read_event(game))
                start_time = arrow.get(game['date']).to('US/Eastern')
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
            print(f'In progress games: {self.active}')
            # print(json.dumps(data,indent=1))
            # print(f'{type(self).__name__} updated.')
            # print('write data...')
            self.dba.write(data)
            # print('data written?')
            # write data to the database

    def read_event(self, event):
        """ ... """
        game = {}
        # game['id']    = event['id']
        game['date']  = arrow.get(event['date']).to('US/Eastern').format('ddd h:mm A')
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
                print(f"{game['possession']} has the ball.")
                game['position']       = situ.get('possessionText',"")
                game['downandyardage'] = situ.get('shortDownDistanceText',"")
                game['lastplay']       = situ['lastPlay']['type'].get('text',"")
            except:
                # game['possession'] = ""
                print("exception in situ")
        return game

if __name__ == '__main__':
    import os
    import dotenv

    dotenv.load_dotenv()

    try:
        PROD = os.environ["PROD"]
        SECRETS_PATH = os.environ["SECRETS_PATH"]
    except KeyError:
        PROD = '0'
        SECRETS_PATH = 'secrets.json'

    if PROD == '0':
        NFLServer(False, 59, SECRETS_PATH).run()
    else:
        NFLServer(True, 59).run()
