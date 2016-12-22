#!/usr/bin/env python
# -*- coding: utf-8 -*-
from phate89lib import rutils
import os, sys
if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

class Itasa(rutils.RUtils):

    USERAGENT="ItaSA Python Plugin"
    ITASA={}
    URL="https://www.italiansubs.net/"
    APIURL="https://api.italiansubs.net/api/rest/"
    AUTHCODE=""
    COOKIES=[]
    DEFPARAMS={}
    DEFPARAMS['format']="json"
    __USER=""
    __PASS=""

    #per salvare il tvdb id delle serie
    UPDATEFILE=True
    __SERIE={}
    __SERIEPATH=''
    __LOADED=False

    def __init__(self, filepath=''):
        self.setUserAgent(self.USERAGENT)
        if filepath=='' or not os.path.isfile(filepath):
            self.__LOADED=True
        else:
            self.__SERIEPATH=filepath

    def setUsername(self, user):
        self.__USER = user;
    def setPassword(self, passw):
        self.__PASS = passw;
    def setApiKey(self, apikey):
        if apikey:
            self.DEFPARAMS['apikey'] = apikey
    def getUsername(self):
        return self.__USER;
    def getPassword(self):
        return self.__PASS;

    def __getPage(self,url,params={},post={},addDefault=True):
        return self.createRequest(url, params, post, addDefault=addDefault)

    def __getJson(self,url,params={},post={}):
        jsn = self.getJson(self.APIURL+url,params,post)
        if jsn:
            self.log('apertura pagina riuscita',4)
            if 'root' in jsn and 'status' in jsn['root'] and jsn['root']['status'] == 'fail':
                self.log('errore nella richiesta: '+jsn['root']['error']['message'],4)
                return False
            for firstEntry in jsn.values():
                for secondEntry in firstEntry.values():
                    for key, item in secondEntry.iteritems():
                        if key == 'news':
                            #check if has a news subitem to determine if it's a list of news or a single news
                            for k in item:
                                if k == 'news':
                                    key='newss'
                                break
                        if key in [ 'show', 'subtitle', 'user', 'news' ]:
                            return item
                        elif key in [ 'shows', 'subtitles', 'episodes', 'newss' ]:
                            if len(item) == 0:
                                return []
                            output = item.values()
                            if 'next' in secondEntry and secondEntry['next'] != '':
                                nx=self.__getJsonFromUrl(secondEntry['next'])
                                if nx:
                                    output.extend(nx)
                            return output
            self.log('errore durante il parsing della pagina json',4)
        return False;
    
    def isLogged(self, checkSite=False):
        self.log("controllo se l'utente è loggato",3)
        bLogin=self.loginAPI()
        if bLogin:
            if checkSite:
                return self.__loggedToSite()
            else:
                self.log('l\'utente è loggato',4)
                return True
        self.log('l\'utente non è loggato',4)
        return False
    
    def __loggedPage(self,page):
        if (page):
            return 'logouticon.png' in page.text
        return false
    
    def __loggedToSite(self,sPost={}):
        return self.__loggedPage(self.__getPage(self.URL,post=sPost,addDefault=False))

    def loginSite(self):
        self.log('tento il login al sito principale',4)
        html_data = self.createRequest(self.URL,addDefault=False)
        if not html_data:
            self.log('errore aprendo la pagina',4)
            return False

        if self.__loggedPage(html_data):
            self.log('login al sito principale effettuato con successo',4)
            return True

        page = self.getSoupFromRes(html_data)
        #form
        txtinput = page.findAll('form', {'name':'login'})

        ## cerca tra gli elementi di tipo hidden/submit nel form login
        listform = ["submit","hidden"]
        dForm={}
        for elem in txtinput[0].findAll('input',{'type':listform}):
            dForm[elem['name']]=elem['value']  

        dForm['username']=self.getUsername()
        dForm['passwd']=self.getPassword()

        ## login sito
        if self.__loggedToSite(dForm):
            self.log('login al sito principale effettuato con successo',4)
            return True
        self.log('login al sito principale fallito',4)
        return False
    
    def getShowList(self):
        return self.__getJson('shows')
        
    def getShowDetails(self,id):
            return self.__getJson('shows/'+str(id),)

    def getShowThumb(self,id):
        res = self.__getPage(self.APIURL + "shows/{id}/folderThumb".format(id=id))
        if (res):
            return res.raw
        return False

    def searchShows(self,q):
            return self.__getJson('shows/search',{ 'q': q, 'page': 1 })
        
    def getNextEpisodes(self):
        return self.__getJson('shows/nextepisodes')

    def getShowSubtitles(self,id,version=''):
        return self.__getJson('subtitles',{ 'show_id': id, 'version': version, 'page': 1 })

    def getSubtitleDetails(self,id):
        return self.__getJson('subtitles/'+str(id))

    def searchSubtitles(self,id,q,version=''):
        return self.__getJson('subtitles/search',{ 'show_id': id, 'q': q, 'version': version, 'page': 1 })

    def loginAPI(self):
        self.log('tento il login con le api',4)
        login=self.__getJson('users/login',{ 'username': self.getUsername(), 'password': self.getPassword() })
        if login and 'authcode' in login:
            self.AUTHCODE = login['authcode']
            self.log('login con le api effettuato con successo',4)
            return True
        self.log('login con le api fallito',4)
        return False

    def getUserDetailsFromAuth(self,authcode):
        return self.__getJson('users/',{ 'authcode': authcode })

    def getLoggedUserDetails(self):
        if self.loginAPI():
            return self.getUserDetailsFromAuth(self.AUTHCODE)
        return False

    def getUserDetails(self,id):
        if self.loginAPI():
            return self.__getJson('users/'+str(id),{ 'authcode': self.AUTHCODE })
        return False

    def login(self):
        if self.loginAPI() and self.loginSite():
            return True
        return False

    def __saveTVDBIds(self):
        if self.UPDATEFILE:
            #save thetvdb ids
            self.log('salvo id thetvdb nel file {path}'.format(path=self.__SERIEPATH),3)
            if self.__SERIEPATH!='':
                self.log('salvo id thetvdb nel file {path}'.format(path=self.__SERIEPATH),3)
                with open(self.__SERIEPATH, 'w') as outfile:
                    json.dump(self.__SERIE, outfile)
                self.log('id thetvdb salvati con successo',4)
        
    def __loadTVDBIds(self):
        if not self.__LOADED:
            self.log('carico id thetvdb nel file {path}'.format(path=self.__SERIEPATH),3)
            #open the json file and load the series
            with open(self.__SERIEPATH) as datafile:
                self.__SERIE=json.load(datafile)
            self.__LOADED=True
            self.log('id thetvdb caricati con successo',4)
    
    def addTVDBIds(self, ids):
        self.log('aggiungo id thetvdb'.format(path=self.__SERIEPATH),3)
        self.__loadTVDBIds()
        changed=False
        for key,value in ids:
            if not key in self.__SERIE:
                self.__SERIE[key]=value
                changed=True
        self.log('id thetvdb aggiunti con successo'.format(path=self.__SERIEPATH),4)
        if changed:
            self.__saveTVDBIds()
    
    def updateTVDBIDs(self,pauseController=None):
        self.__loadTVDBIds()
        self.log('cerco nuovi id thetvdb'.format(path=self.__SERIEPATH),1)
        __SERIE=self.getShowList()
        if __SERIE:
            itasaIDs=self.__SERIE.values()
            print __SERIE
            for s in __SERIE:
                if pauseController:
                    while pauseController.isPaused():
                        self.log('esecuzione in pausa',4)
                        time.sleep(1)
                    if pauseController.isStopped():
                        self.log('aggiornamento interrotto... salvo ed esco',1)
                        self.__saveTVDBIds()
                        return
                if not s['id'] in itasaIDs:
                    sInfo=self.getShowDetails(s['id'])
                    if sInfo:
                        self.__SERIE[sInfo['id_tvdb']]=s['id']
            self.log('ricerca nuovi id thetvdb completata con successo',4)
        self.__saveTVDBIds()
        
    def __getShowIDbyTVDBId(self,tvdbId):
        self.log('cerco __SERIE con id {tvdbId}'.format(tvdbId=tvdbId),1)
        self.__loadTVDBIds()
        if tvdbId in self.__SERIE:
            self.log('__SERIE trovata',4)
            return self.__SERIE[tvdbId]
        self.updateTVDBIDs()
        if tvdbId in self.__SERIE:
            self.log('__SERIE trovata',4)
            return self.__SERIE[tvdbId]
        else:
            self.log("__SERIE tv con id {tvdbId} non trovata".format(tvdbId=tvdbId),1)
        return False
    
    def __getSubtitlesFromIDAndEpisode(self,showID,season,episode,quality=''):
        sepisodio=str(season)+'x'+str(episode).zfill(2)
        subtitles=self.searchSubtitles(showID,sepisodio)
        if quality=='' or not subtitles:
            return subtitles
        quality=quality.lower()
        subs=[]
        for sub in subtitles:
            if sub['version'].lower()==quality:
                subs.append(sub)
        return subs

    def searchSubtitlesByTVDBID(self,tvdbId,episode,password,quality=''):
        showID=self.__getShowIDbyTVDBId(str(tvdbId))
        if not showID:
            self.log('nessuna __SERIE trovata con questo tvdb id',1)
            return False
        return self.__getSubtitlesFromIDAndEpisode(showID,episode,password,quality)

    def searchSubtitlesByShowName(self,name,episode,password,quality=''):
        shows=self.searchShows(name)
        if not shows:
            if shows == False:
                self.log('nessuna __SERIE trovata con questo nome',1)
            return shows
        return self.__getSubtitlesFromIDAndEpisode(shows[0]['id'],episode,password,quality)

        sepisodio=str(episode)+'x'+str(password).zfill(2)

    def searchSubtitlesByFileName(self,sFileName,quality=''):
        self.log('cerco i sottotitoli dal nome file '+sFileName,1)
        tvshow, season, episode = staticutils.parseFileName(sFileName)
        if not tvshow:
            self.log('nome file non riconosciuto come valido episodio di serie tv',1)
            return False
        return self.searchSubtitlesByShowName(tvshow,season,episode,quality)
        
    def getFile(self,id,destPath='',index=0):
        return self.getFileExtracted(self.APIURL + 'subtitles/download',{ 'authcode': self.AUTHCODE, 'subtitle_id': id}, dataPath=destPath, index=index)