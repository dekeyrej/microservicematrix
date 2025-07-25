""" ... """
# docker build --build-arg=MICROSERVICE=mlb --build-arg=PANDAS=False -t 192.168.86.49:32000/mlb:registry .
# docker push 192.168.86.49:32000/mlb:registry
# kubectl rollout restart -n default deployment mlb
from typing import Mapping
import arrow
import json
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class MLBServer(MicroService):
    """ ... """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)
        logging.info(self.secrets)
        del self.secrets
        self.type = 'MLB'
        self.url = 'http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard'

    def update(self):
        """ ... """
        tnow = arrow.now().to(self.timezone)
        resp = self.fetch(self.url,'Fetching MLB games',tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        if resp is not None:
            games = resp['events']
            data = {
                'type': self.type,
                'updated': self.now_str(tnow, False),
                'valid': self.now_str(tnow.shift(seconds=self.update_period), True),
                'values': []
            }

            game_count = len(games)
            pre_games = in_games = post_games = 0

            next_start_time = tnow.replace(hour=23,minute=59,second=59)
            for gam in games:
                game, start_time = self.load_game(gam) #, tnow)
                # if start_time < next_start_time and start_time >= tnow:
                # if tnow <= start_time < next_start_time:
                #     next_start_time = start_time
                status = game['status']
                if status == 'post':
                    post_games += 1
                elif status == 'in':
                    in_games += 1
                else:
                    pre_games += 1
                    if tnow <= start_time < next_start_time:
                        next_start_time = start_time

                data['values'].append(game)
            # print(json.dumps(data,indent=2))

            # Calculate 'nextValid' time
            if game_count == 0 or (in_games == 0 and post_games == game_count):
                # sleep until noon today/tomorrow
                if tnow.hour <= 11:
                    next_valid = tnow.replace(hour=11,minute=30,second=0) # 11:30 AM today
                else:
                    next_valid = tnow.shift(days=+1).replace(hour=11,minute=30,second=0)
                    # 11:30 AM tomorrow
                self.update_period = (next_valid - tnow).seconds
            elif in_games > 0:
                next_valid = \
                    tnow.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A Z')
                self.update_period = 29
            else:
                # sleep until the start of the first game
                next_valid = next_start_time
                self.update_period = min((next_valid - tnow).seconds, 15*60)
        #         print(next_sleep)
#             self.update_rate = next_sleep # seconds between updates
            data['valid'] = next_valid.format('MM/DD/YYYY h:mm:ss A Z')
            logging.info(f'{type(self).__name__} updated.')
            self.r.publish('update', json.dumps(data))

    def load_game(self, game: dict) -> tuple[dict, str]:
        """ ... """
        values = {}
        # next_start_time = tnow.replace(hour=23,minute=59,second=59)
        values['id']         = game['id']
        start_time = arrow.get(game['date'],'YYYY-MM-DD[T]HH:mmZ').to(self.timezone)
        # if start_time < next_start_time and start_time >= tnow:
        # if tnow <= start_time < next_start_time:
        #     next_start_time = start_time
        values['startTime']  = start_time.format('MM/DD/YYYY h:mm A Z')
        values['seasonType'] = game['season']['slug']
        comp                 = game['competitions'][0]
        values.update(self.away_values(comp))
        values.update(self.home_values(comp))
        values.update(self.scores(comp))
        return values, start_time
        # return values, next_start_time

    def home_values(self, competition: Mapping) -> Mapping:
        """ ... """
        values = {}
        values['homeAbbreviation'] = competition['competitors'][0]['team']['abbreviation']
        try:
            values['homeColor']        = competition['competitors'][0]['team']['color']
            values['homeRecord']       = competition['competitors'][0]['records'][0]['summary']
        except KeyError:
            values['homeColor']        = '000000'
            values['homeRecord']       = ''
        values['homeLogo']         = competition['competitors'][0]['team']['logo']

        return values

    def away_values(self, competition: Mapping) -> Mapping:
        """ ... """
        values = {}
        values['awayAbbreviation'] = competition['competitors'][1]['team']['abbreviation']
        try:
            values['awayColor']        = competition['competitors'][1]['team']['color']
            values['awayRecord']       = competition['competitors'][1]['records'][0]['summary']
        except KeyError:
            values['awayColor']        = '000000'
            values['awayRecord']       = ''
        values['awayLogo']         = competition['competitors'][1]['team']['logo']

        return values

    def scores(self, competition: Mapping) -> Mapping:
        """ ... """
        values = {}
        values['status'] = status  = competition['status']['type']['state']
        if status == 'post':
            values['awayScore']    = competition['competitors'][1]['score']
            values['homeScore']    = competition['competitors'][0]['score']
            values['awayHits']     = competition['competitors'][1]['hits']
            values['homeHits']     = competition['competitors'][0]['hits']
            values['awayErrors']   = competition['competitors'][1]['errors']
            values['homeErrors']   = competition['competitors'][0]['errors']
        elif status == 'in':
            values['awayScore']    = competition['competitors'][1]['score']
            values['homeScore']    = competition['competitors'][0]['score']
            values['awayHits']     = competition['competitors'][1]['hits']
            values['homeHits']     = competition['competitors'][0]['hits']
            values['awayErrors']   = competition['competitors'][1]['errors']
            values['homeErrors']   = competition['competitors'][0]['errors']
            values['inning']       = competition['status']['period']
            values['inningState']  = competition['status']['type']['shortDetail'][0:3]
            if values['inningState'] in ['Top', 'Bot']:
                # Top, Mid, Bot, End
                values.update(self.situation(competition))
            try:
                values['lastPlay']     = competition['situation']['lastPlay']['text']
            except KeyError:
                values['lastPlay'] = ''

        return values

    def situation(self, competition: Mapping) -> Mapping:
        """ ... """
        values = {}
        situation = competition['situation']
        values['balls']        = situation.get('balls',0)
        values['strikes']      = situation.get('strikes',0)
        values['outs']         = situation.get('outs',0)
        values['onFirst']      = situation.get('onFirst',False)
        values['onSecond']     = situation.get('onSecond',False)
        values['onThird']      = situation.get('onThird',False)
        # values['pitcher']      = situation['pitcher']['athlete']['shortName']
        # values['batter']       = situation['batter']['athlete']['shortName']
        return values


if __name__ == '__main__':
    import os

    period = int(os.environ.get("PERIOD", '600'))
    prod = os.environ.get("PROD", '0')
    if prod == '1':
        from config import secretcfg, secretdef
    else:
        from devconfig import secretcfg, secretdef

    logging.debug(f"Starting Events Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")
    MLBServer(period, secretcfg, secretdef).run()
