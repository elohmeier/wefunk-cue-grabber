#!/usr/bin/python3

'''
Created on Feb 26, 2015

@author: enno
'''

import argparse
import os
import urllib.request
from lxml import html
from datetime import datetime, timedelta
import re
import json

WEFUNK_SHOW_BASE_URL = 'http://www.wefunkradio.com/show/'

class Client:
    def ExtractShowInfos(self, url):    
        httpResponse = urllib.request.urlopen(url)
        htmlContent = httpResponse.read()
        htmlTree = html.fromstring(htmlContent)
        
        htmlShows = htmlTree.xpath("//a[contains(@class,\"show-item\")]")
        
        parsedShows = []
        
        for htmlShow in htmlShows:
            showNumber = re.findall('\d+', htmlShow.attrib['href'])[0]
            showDate = datetime.strptime(htmlShow.attrib['id'], 'sp_%Y-%m-%d')        
            parsedShows.append(ShowInfo(showNumber, showDate))    
        return parsedShows
    
    
    def ExtractTrackList(self, show):
        httpResponse = urllib.request.urlopen(show.getShowUrl())
        htmlContentBytes = httpResponse.read()
        htmlContent = htmlContentBytes.decode(httpResponse.headers.get_content_charset())
        htmlTree = html.fromstring(htmlContentBytes)
    
        plItemLst = htmlTree.xpath('//ul[@class="playlistregular"]//div[@class="content"]//div')
        trackExtraRegex = re.findall('(?<=var trackextra \\= )[^;]+(?=;)', htmlContent)
        tracksRegex = re.findall('(?<=var tracks \\= )[^;]+(?=;)', htmlContent)
        
        jsonTrackExtraLst = json.loads(trackExtraRegex[0])
        jsonTrackList = json.loads(tracksRegex[0])
        jsonTrackMsPosLst = jsonTrackList['tracks']
    
        trackList = []
    
        for index, trackExtra in enumerate(jsonTrackExtraLst):
            track = jsonTrackMsPosLst[index]        
            mspos = timedelta(milliseconds = track['mspos'])
            
            if index == 0:
                trackList.append(Track(1, "WEFUNK RADIO", "intro", mspos))
            else:
                artist = trackExtra[0]['a'] if len(trackExtra) > 0 and 'a' in trackExtra[0] else ''
                title = trackExtra[0]['t'] if len(trackExtra) > 0 and 't' in trackExtra[0] else ''
                
                plText = html.tostring(plItemLst[index]).decode(httpResponse.headers.get_content_charset())
                
                if "<strong>talk</strong> (over " in plText:
                    trackList.append(Track(index + 1, "WEFUNK RADIO", "talk (over " + artist + " - " + title + ")", mspos))
                else:
                    trackList.append(Track(index + 1, artist, title, mspos))       
            
        return trackList
    
    
    def CreateCueSheet(self, show):
        tracks = self.ExtractTrackList(show)
        cue = CueSheet("HipHop", show.showDate.strftime('%Y'), "WEFUNK RADIO", "WEFUNK SHOW #" + show.showNumber, show.getMp3LqFilename())
        
        for track in tracks:
            cue.addTrack(track)
    
        return cue



class Track(object):    
    def __init__(self, nr, artist, title, startsAt):
        self.nr = nr
        self.artist = artist
        self.title = title
        self.startsAt = startsAt
        


class ShowInfo:
    def __init__(self, showNumber, showDate):
        self.showNumber = showNumber
        self.showDate = showDate

    def getMp3LqFilename(self):
        return 'WeFunk_Show_' + self.showNumber + '_' + self.showDate.strftime('%Y-%m-%d') + '.mp3'

    def getShowUrl(self):
        return WEFUNK_SHOW_BASE_URL + self.showDate.strftime('%Y-%m-%d')
        
    
    
class CueSheet:
    def __init__(self, genre, year, performer, title, fileName):
        self.genre = genre
        self.year = year
        self.performer = performer
        self.title = title
        self.fileName = fileName
        self.tracks = []
        
        
    def addTrack(self, track):
        self.tracks.append(track)        
        
        
    def saveToFile(self, path):    
        f = open(path, 'w')
        
        f.write("TITLE \"{0}\"".format(self.title))
        f.write("\nPERFORMER \"{0}\"".format(self.performer))
        f.write("\nREM Year  : {0}".format(self.year))
        f.write("\nREM Genre : {0}".format(self.genre))
        f.write("\nFILE \"{0}\" MP3".format(self.fileName))
        
        for track in self.tracks:
            
            secondsRest = (track.startsAt - timedelta(minutes = int(track.startsAt / timedelta(minutes = 1))))
            milisecondsRest = (track.startsAt - timedelta(seconds = int(track.startsAt / timedelta(seconds = 1)))) / timedelta(milliseconds = 1)
            frame = milisecondsRest/1000.0*75
            
            f.write("\n\tTRACK {0:02d} AUDIO".format(track.nr))
            f.write("\n\t\tTITLE \"" + track.title + "\"")
            f.write("\n\t\tPERFORMER \"" + track.artist + "\"")
            f.write("\n\t\tINDEX 01 {0:02d}:{1:02d}:{2:02d}".format(
                                                                    int(track.startsAt / timedelta(minutes = 1)),
                                                                    int(secondsRest / timedelta(seconds = 1)),
                                                                    int(frame)))        
        f.close()
        
    






parser = argparse.ArgumentParser(description="downloads show information for WEFUNK RADIO shows. existing cue sheets are overwritten")
parser.add_argument("-u", "--url", default="http://www.wefunkradio.com/shows/", help="url where to load the shows from, defaults to newest shows page")
parser.add_argument("-o", "--output-dir", default=os.getcwd(), help="output directory for cue-sheets, defaults to working directory")
args = parser.parse_args()


client = Client()

print("searching for shows on \"{0}\". \nuse --url parameter for older shows, e.g. \"--url http://www.wefunkradio.com/shows/450\"".format(args.url))
shows = client.ExtractShowInfos(args.url)

#shows = client.ExtractShowInfos("http://www.wefunkradio.com/shows/800")
#shows = client.ExtractShowInfos("http://www.wefunkradio.com/shows/450")


print("found {0} shows on page!".format(len(shows)))
print("saving cue sheets to " + args.output_dir)

for show in shows:
    cue = client.CreateCueSheet(show)
    cue.saveToFile(os.path.join(args.output_dir, show.getMp3LqFilename().replace('.mp3', '.cue')))
    print('created cue-sheet for #' + show.showNumber)


print("finished")



