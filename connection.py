#!/usr/bin/python3

import time
from datetime import datetime,timedelta
from errors import InvalidRates
from Cassiopeia.requests.sessions import Session

class APIRateMeter:
    '''An instance of this class can be used to track requests to the LoL API by
    specific API keys in order to limit the rate at which requests are made to
    the API according to Riot's rules on rate limiting.'''

    default_rate = ( (10,timedelta(seconds=10)), (500,timedelta=(minutes=10)) )

    _tracked_keys = {}
    # _tracked_keys has the format:
    # _tracked_keys
    #       apikey
    #           rates - api access rates to obey
    #           maxdelta - longest rate to check, used for cleaning
    #           requestTimestamps - list of timestamps when this key was used

    def __init__(self,apikey,rates=None):
        #If not tracked, set up tracking
        if apikey not in _tracked_keys.keys():
            #Make sure they are valid rates, or raise an error
            if not rates:
                rates = default_rate
            if not self._validaterates(rates):
                raise InvalidRates
            APIRateMeter._tracked_keys[apikey] = {'rates':rates,
                                                'maxdelta':max(rate[1] for rate in rates),
                                                'requestTimestamps':[]}
        else:
            #If already tracked and new rates provided, update the rates
            if rates:
                if not self._validaterates(rates):
                    raise InvalidRates
                APIRateMeter._tracked_keys[apikey] = {'rates':rates,
                                                'maxdelta':max(rate[1] for rate in rates),
                                                'requestTimestamps':APIRateMeter._tracked_keys[apikey]['requestTimestamps']}

        #Finally, set up the instance to know which key it tracks
        self.key = apikey

    def check(self):
        '''Returns true if no rate has been exceeded. Does not count as an API
        access itself.'''
        rates = APIRateMeter._tracked_keys[self.key]['rates']
        timestamps = APIRateMeter.tracked_keys[self.key]['requestTimestamps']
        for rate in rates:
            callcount = len([stamp for stamp in timestamps if stamp - datetime.now() < rate[1]])
            if  callcount >= rate[0]:
                return False
        return True

    def access(self,blocking=True,clean=True):
        '''Call to log an access to the API. If blocking is True, the method
        will block if the rate limit has been exceeded until it believes that
        enough time has passed that the API should no longer be blocked.
        If clean is True, this method also calls APIRateMeter.cleantimestamps.'''
        if blocking:
            while not self.check():
                time.sleep(0.01)
        if clean:
            self.cleantimestamps()
        APIRateMeter._tracked_keys[self.key]['requestTimestamps'].append(datetime.now())

    def cleantimestamps(self):
        '''Removes all timestamps that are greater than the longest rate since
        they no longer need to be tracked.'''
        timestamps = APIRateMeter._tracked_keys[self.key]['requestTimestamps']
        maxdelta = APIRateMeter._tracked_keys[self.key]['maxdelta']
        timestamps = [ts for ts in timestamps if ts - datetime.now > maxdelta]
        APIRateMeter._tracked_keys[self.key]['requestTimestamps'] = timestamps

    @staticmethod        
    def _validaterates(rates):
        if rates:
            try:
                for r in rates:
                    if not isinstance(r[0]),int):
                        return False
                    if not isinstance(r[1]),timedelta):
                        return False
            except IndexError:
                return False
        else:
            return True


class RiotAPISession(Session):
    '''RiotAPISession'''

    def __init__(self,apikey,region):
        self.apikey = apikey

    @staticmethod
    def _validate_region(region):
        pass

#champion-v1.2 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/{region}/v1.2/champion' #Retrieve all champions. (REST)
'/api/lol/{region}/v1.2/champion/{id}' #Retrieve champion by ID. (REST)
#game-v1.3 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/{region}/v1.3/game/by-summoner/{summonerId}/recent' #Get recent games by summoner ID. (REST)
#league-v2.4 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/{region}/v2.4/league/by-summoner/{summonerIds}' #Get leagues mapped by summoner ID for a given list of summoner IDs. (REST)
'/api/lol/{region}/v2.4/league/by-summoner/{summonerIds}/entry' #Get league entries mapped by summoner ID for a given list of summoner IDs. (REST)
'/api/lol/{region}/v2.4/league/by-team/{teamIds}' #Get leagues mapped by team ID for a given list of team IDs. (REST)
'/api/lol/{region}/v2.4/league/by-team/{teamIds}/entry' #Get league entries mapped by team ID for a given list of team IDs. (REST)
'/api/lol/{region}/v2.4/league/challenger' #Get challenger tier leagues. (REST)
#lol-static-data-v1.2 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/static-data/{region}/v1.2/champion' #Retrieves champion list. (REST)
'/api/lol/static-data/{region}/v1.2/champion/{id}' #Retrieves a champion by its id. (REST)
'/api/lol/static-data/{region}/v1.2/item' #Retrieves item list. (REST)
'/api/lol/static-data/{region}/v1.2/item/{id}' #Retrieves item by its unique id. (REST)
'/api/lol/static-data/{region}/v1.2/mastery' #Retrieves mastery list. (REST)
'/api/lol/static-data/{region}/v1.2/mastery/{id}' #Retrieves mastery item by its unique id. (REST)
'/api/lol/static-data/{region}/v1.2/realm' #Retrieve realm data. (REST)
'/api/lol/static-data/{region}/v1.2/rune' #Retrieves rune list. (REST)
'/api/lol/static-data/{region}/v1.2/rune/{id}' #Retrieves rune by its unique id. (REST)
'/api/lol/static-data/{region}/v1.2/summoner-spell' #Retrieves summoner spell list. (REST)
'/api/lol/static-data/{region}/v1.2/summoner-spell/{id}' #Retrieves summoner spell by its unique id. (REST)
'/api/lol/static-data/{region}/v1.2/versions' #Retrieve version data. (REST)
#stats-v1.3 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/{region}/v1.3/stats/by-summoner/{summonerId}/ranked' #Get ranked stats by summoner ID. (REST)
'/api/lol/{region}/v1.3/stats/by-summoner/{summonerId}/summary' #Get player stats summaries by summoner ID. (REST)
#summoner-v1.4 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/{region}/v1.4/summoner/by-name/{summonerNames}' #Get summoner objects mapped by standardized summoner name for a given list of summoner names. (REST)
'/api/lol/{region}/v1.4/summoner/{summonerIds}' #Get summoner objects mapped by summoner ID for a given list of summoner IDs. (REST)
'/api/lol/{region}/v1.4/summoner/{summonerIds}/masteries' #Get mastery pages mapped by summoner ID for a given list of summoner IDs (REST)
'/api/lol/{region}/v1.4/summoner/{summonerIds}/name' #Get summoner names mapped by summoner ID for a given list of summoner IDs. (REST)
'/api/lol/{region}/v1.4/summoner/{summonerIds}/runes' #Get rune pages mapped by summoner ID for a given list of summoner IDs. (REST)
#team-v2.3 [BR, EUNE, EUW, KR, LAN, LAS, NA, OCE, RU, TR] Show/Hide List OperationsExpand Operations
'/api/lol/{region}/v2.3/team/by-summoner/{summonerIds}' #Get teams mapped by summoner ID for a given list of summoner IDs. (REST)
'/api/lol/{region}/v2.3/team/{teamIds}' #Get teams mapped by team ID for a given list of team IDs. (REST)
