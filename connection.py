#!/usr/bin/python3

import time
from datetime import datetime,timedelta
from Cassiopeia.errors import InvalidRates,InvalidServerRegion
from Cassiopeia.requests.sessions import Session

class APIRateMeter:
    '''An instance of this class can be used to track requests to the LoL API by
    specific API keys in order to limit the rate at which requests are made to
    the API according to Riot's rules on rate limiting.'''

    default_rate = ( (10,timedelta(seconds=10)), (500,timedelta(minutes=10)) )

    _tracked_keys = {}
    # _tracked_keys has the format:
    # _tracked_keys
    #       apikey
    #           rates - api access rates to obey
    #           maxdelta - longest rate to check, used for cleaning
    #           requestTimestamps - list of timestamps when this key was used

    def __init__(self,apikey,rates=None):
        #If not tracked, set up tracking
        if apikey not in APIRateMeter._tracked_keys.keys():
            #Make sure they are valid rates, or raise an error
            if not rates:
                rates = APIRateMeter.default_rate
            self._validaterates(rates)
            APIRateMeter._tracked_keys[apikey] = {'rates':rates,
                                                'maxdelta':max(rate[1] for rate in rates),
                                                'requestTimestamps':[]}
        else:
            #If already tracked and new rates provided, update the rates
            if rates:
                self._validaterates(rates)
                APIRateMeter._tracked_keys[apikey] = {'rates':rates,
                                                'maxdelta':max(rate[1] for rate in rates),
                                                'requestTimestamps':APIRateMeter._tracked_keys[apikey]['requestTimestamps']}

        #Finally, set up the instance to know which key it tracks
        self.key = apikey

    def check(self):
        '''Returns true if no rate has been exceeded. Does not count as an API
        access itself.'''
        rates = APIRateMeter._tracked_keys[self.key]['rates']
        timestamps = APIRateMeter._tracked_keys[self.key]['requestTimestamps']
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
        timestamps = [ts for ts in timestamps if (ts - datetime.now()) < maxdelta]
        APIRateMeter._tracked_keys[self.key]['requestTimestamps'] = timestamps

    @staticmethod        
    def _validaterates(rates):
        if rates:
            try:
                for r in rates:
                    if not isinstance(r[0],int):
                        raise InvalidRates
                    if not isinstance(r[1],timedelta):
                        raise InvalidRates
            except IndexError:
                raise InvalidRates

class RiotAPISession(Session):
    '''RiotAPISession'''

    REGIONS = {'br':'br.api.pvp.net',
            'eune':'eune.api.pvp.net',
            'euw':'euw.api.pvp.net',
            'kr':'kr.api.pvp.net',
            'lan':'las.api.pvp.net',
            'las':'las.api.pvp.net',
            'na':'na.api.pvp.net',
            'oce':'oce.api.pvp.net',
            'ru':'ru.api.pvp.net',
            'tr':'tr.api.pvp.net'}

    def __init__(self,apikey,region):
        self.apikey = apikey
        if region in RiotAPISession.REGIONS.keys():
            self.region = region
        else:
            raise InvalidServerRegion

        self.ratemeter = APIRateMeter(self.apikey)

        super().__init__()

    def get(self,endpoint,params={},ratelimited=True):
        '''Takes care of all the busy work that needs to be done every time the
        LoL API is called such triggering the rate limiter, passing the API key
        as a parameter, and picking the correct region server.'''
        params['api_key'] = self.apikey
        if ratelimited:
            self.ratemeter.access()
        req = super().get('https://' + RiotAPISession.REGIONS[self.region] +
                endpoint,params=params)
        return req

    def champion(self,championid=None,freeToPlay=False):
        '''Returns information about champions. Can be given a champion id to
        get information on a specific champion, or if given no championId, will
        return a list of all champions. If freeToPlay is True, will only return
        champions that are currently free to play.'''
        if championid:
            query = '/api/lol/{region}/v1.2/champion/{championid}'
            query = query.format(championid=championid,region=self.region)
        else:
            query = '/api/lol/{region}/v1.2/champion'
            query = query.format(region=self.region)
        p = {}
        if freeToPlay:
            p['freeToPlay'] = 'True'

        return self.get(query,params=p).json()

    def game(self,summonerid):
        '''Returns a list of up to 10 most recent games by summonerId.'''
        query = '/api/lol/{region}/v1.3/game/by-summoner/{summonerId}/recent'
        query = query.format(region=self.region,summonerId=summonerid)
        return self.get(query).json()

    def league_by_summoner(self,summonerids,summoneronly=False):
        '''Gets ranked league information by summoner ID. summonerids should be
        a list of up to 40 summonerids. If summoneronly is True, will only
        return league information on the specific summoner. Otherwise, it will
        return information for that summoner's entire league.'''
        if summoneronly:
            query = '/api/lol/{region}/v2.4/league/by-summoner/{summonerIds}/entry'
        else:
            query = '/api/lol/{region}/v2.4/league/by-summoner/{summonerIds}'
        query = query.format(summonerIds=summonerids,region=self.region)
        return self.get(query).json()

    def league_by_team(self,teamids,teamonly=False):
        '''Gets ranked league information by team ID. teamids should be
        a list of up to 40 teamids. If teamonly is True, will only
        return league information on the specific team. Otherwise, it will
        return information for that team's entire league.'''
        if teamonly:
            query = '/api/lol/{region}/v2.4/league/by-team/{teamIds}/entry'
        else:
            query = '/api/lol/{region}/v2.4/league/by-team/{teamIds}'
        query = query.format(teamIds=teamids,region=self.region)
        return self.get(query).json()

    def challenger_league(self):
        '''Returns all information on the challenger league.'''
        query = '/api/lol/{region}/v2.4/league/challenger'
        query = query.format(region=self.region)
        return self.get(query).json()

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
