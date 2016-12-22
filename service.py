# -*- coding: utf-8 -*-

import os
import sys
import resources.lib.Itasa as Itasa
from phate89lib import staticutils, kodiutils
apiKey='4ffc34b31af2bca207b7256483e24aac'

SERIEPROFILEPATH = os.path.join(kodiutils.PATH_T,'resources', 'Serie.json')

if not kodiutils.isPlayingVideo():
    kodiutils.endScript(kodiutils.LANGUAGE(32007),0)

kodiutils.createAddonFolder()
params = staticutils.getParams()

oItasa=Itasa.Itasa(SERIEPROFILEPATH)
oItasa.setApiKey(apiKey)
oItasa.log = kodiutils.log

if params['action'] == 'search' or params['action'] == 'manualsearch':
    if not kodiutils.containsLanguage(params['languages'],{"ita"}):
        kodiutils.endScript(kodiutils.LANGUAGE(32005),0)

    episode = kodiutils.getEpisodeInfo()
    
    subs=None
    if 'searchstring' in params:
        subs=oItasa.searchSubtitlesByFileName(urllib.unquote(params['searchstring']))
        quality=staticutils.guessQuality(params['searchstring'])
    else:
        quality=staticutils.guessQuality(episode['filename'])
        onlineid = kodiutils.getShowID()    
        if onlineid:
            subs=oItasa.searchSubtitlesByTVDBID(onlineid,episode['season'],episode['episode'])
        if not subs and episode['tvshow']!='':
            subs=oItasa.searchSubtitlesByShowName(episode['tvshow'],episode['season'],episode['episode'])
        if not subs:
            subs=oItasa.searchSubtitlesByFileName(episode['filename'])
    if subs:
        for sub in subs:
            if sub['version'].lower()==quality:
                kodiutils.append_subtitle(sub['id'], sub['name'] + ' ' + sub['version'], True)
        for sub in subs:
            if sub['version'].lower()!=quality:
                kodiutils.append_subtitle(sub['id'], sub['name'] + ' ' + sub['version'], False)

elif params['action'] == 'download':
    oItasa.setUsername(kodiutils.getSetting( 'ITuser' ))
    oItasa.setPassword(kodiutils.getSetting( 'ITpass' ))
    if not oItasa.login():
        kodiutils.endScript(kodiutils.LANGUAGE(32004),0)
    lastindex=0
    if kodiutils.getSetting('lastSub')==params['subid']:
        lastindex=kodiutils.getSettingAsNum('lastIndex') + 1
    else:
        kodiutils.setSetting('lastSub', params['subid'])

    sub=oItasa.getFile(params['subid'],destPath=os.path.join(kodiutils.DATA_PATH_T, 'subtitles', '').decode('utf-8'),index=lastindex)
    if not sub:
        kodiutils.log(kodiutils.LANGUAGE(32009),0)
        sys.exit()

    kodiutils.addListItem(params=sub[1], isFolder=False)
    kodiutils.setSetting('lastIndex',sub[0])

kodiutils.endScript()    # send end of directory to XBMC