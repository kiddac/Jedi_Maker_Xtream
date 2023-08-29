#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import jedi_globals as glob

from .plugin import skin_path, cfg, hdr, screenwidth
from .jediStaticText import StaticText

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List
from enigma import eServiceReference
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from datetime import datetime

import base64
import calendar
import json
import re
import os
import socket
import sys
import time

pythonVer = 2
if sys.version_info.major == 3:
    pythonVer = 3

if pythonVer == 3:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
else:
    from urllib2 import urlopen, Request, URLError


def downloadSimpleData():
    refurl = ""
    refstream = ""
    glob.refstreamnum = ""
    glob.username = ""
    glob.password = ""
    glob.domain = ""
    error_message = ""
    isCatchupChannel = False

    refurl = glob.currentref.getPath()
    # http://domain.xyx:0000/live/user/pass/12345.ts

    if refurl != "":
        refstream = refurl.split("/")[-1]
        # 12345.ts

        glob.refstreamnum = int("".join(filter(str.isdigit, refstream)))
        # 12345

        # get domain, username, password from path
        match1 = False
        if re.search(r"(https|http):\/\/[^\/]+\/(live|movie|series)\/[^\/]+\/[^\/]+\/\d+(\.m3u8|\.ts|$)", refurl) is not None:
            match1 = True

        match2 = False
        if re.search(r"(https|http):\/\/[^\/]+\/[^\/]+\/[^\/]+\/\d+(\.m3u8|\.ts|$)", refurl) is not None:
            match2 = True

        if match1:
            glob.username = re.search(r"[^\/]+(?=\/[^\/]+\/\d+\.)", refurl).group()
            glob.password = re.search(r"[^\/]+(?=\/\d+\.)", refurl).group()
            glob.domain = re.search(r"(https|http):\/\/[^\/]+", refurl).group()

        elif match2:
            glob.username = re.search(r"[^\/]+(?=\/[^\/]+\/[^\/]+$)", refurl).group()
            glob.password = re.search(r"[^\/]+(?=\/[^\/]+$)", refurl).group()
            glob.domain = re.search(r"(https|http):\/\/[^\/]+", refurl).group()

        simpleurl = "%s/player_api.php?username=%s&password=%s&action=get_simple_data_table&stream_id=%s" % (glob.domain, glob.username, glob.password, glob.refstreamnum)
        getLiveStreams = "%s/player_api.php?username=%s&password=%s&action=get_live_streams" % (glob.domain, glob.username, glob.password)

        response = ""

        req = Request(getLiveStreams, headers=hdr)

        try:
            response = urlopen(req)

        except URLError as e:
            print(e)

        except socket.timeout as e:
            print(e)

        except:
            print("\n ***** download Live Streams unknown error")

        if response != "":
            liveStreams = json.load(response)

            isCatchupChannel = False
            for channel in liveStreams:
                if channel["stream_id"] == glob.refstreamnum:
                    if int(channel["tv_archive"]) == 1:
                        isCatchupChannel = True
                        break

        if isCatchupChannel:

            response = ""
            req = Request(simpleurl, headers=hdr)

            try:
                response = urlopen(req)

            except URLError as e:
                print(e)
                pass

            except socket.timeout as e:
                print(e)
                pass

            except:
                print("\n ***** downloadSimpleData unknown error")
                pass

            if response != "":
                simple_data_table = json.load(response)

                glob.archive = []
                hasarchive = False
                if "epg_listings" in simple_data_table:
                    for listing in simple_data_table["epg_listings"]:
                        if "has_archive" in listing:
                            if listing["has_archive"] == 1:
                                hasarchive = True
                                glob.archive.append(listing)

                if hasarchive:
                    glob.dates = []
                    for listing in glob.archive:
                        date = datetime.strptime(listing["start"], "%Y-%m-%d %H:%M:%S")
                        day = calendar.day_abbr[date.weekday()]
                        start = ["%s\t%s" % (day, date.strftime("%d/%m/%Y")), date.strftime("%Y-%m-%d")]

                        if start not in glob.dates:
                            glob.dates.append(start)

                    dates_count = len(glob.dates)

                    glob.dates.append([(_("All %s days")) % dates_count, "0000-00-00"])

                    return error_message, True
                else:
                    glob.archive = []

                    numberofdays = 7
                    currentDate = datetime.combine(datetime.date.today(), datetime.min.time())

                    manualArchiveStartDate = currentDate + datetime.timedelta(days=-numberofdays)
                    glob.dates = []

                    for x in range(0, numberofdays):
                        manualDay = calendar.day_abbr[manualArchiveStartDate.weekday()]
                        manualStart = ["%s\t%s" % (manualDay, manualArchiveStartDate.strftime("%d/%m/%Y")), manualArchiveStartDate.strftime("%Y-%m-%d")]
                        glob.dates.append(manualStart)
                        aStart = manualArchiveStartDate

                        for y in range(0, 24):
                            aEnd = (aStart + datetime.timedelta(hours=1))
                            aStartString = aStart.strftime("%Y-%m-%d %H:%M:%S")
                            aEndString = aEnd.strftime("%Y-%m-%d %H:%M:%S")
                            aStart_timestamp = aStart.strftime("%s")
                            aStop_timestamp = aEnd.strftime("%s")
                            listing = {"start": aStartString, "end": aEndString, "start_timestamp": aStart_timestamp, "stop_timestamp": aStop_timestamp, "title": "UHJvZ3JhbSBEYXRhIE5vdCBBdmFpbGFibGU=", "description": "UHJvZ3JhbSBEYXRhIE5vdCBBdmFpbGFibGU="}
                            glob.archive.append(listing)
                            aStart = (aStart + datetime.timedelta(hours=1))

                        manualArchiveStartDate = manualArchiveStartDate + datetime.timedelta(days=1)

                    glob.dates.append([(_("Program Data Not Available")), "9999-99-99"])
                    return error_message, True

            else:
                error_message = _("Error: Downloading data error.")
                return error_message, False

        else:
            error_message = _("Channel has no TV Archive.")
            return error_message, False


class JediMakerXtream_Catchup(Screen):

    def __init__(self, session):

        skin = """
            <screen name="JediCatchup" position="center,center" size="600,600" >

                <widget source="newlist" render="Listbox" position="0,0" size="600,504" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
                    <convert type="TemplatedMultiContent">
                        {"template": [
                            MultiContentEntryText(pos = (15, 0), size = (570, 45), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 0 is the name
                        ],
                    "fonts": [gFont("jediregular", 36)],
                    "itemHeight": 54
                    }
                    </convert>
                </widget>

            </screen>"""

        if screenwidth.width() <= 1280:
            skin = """
                <screen name="JediCatchup" position="center,center" size="400,400" >
                    <widget source="newlist" render="Listbox" position="0,0" size="400,336" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
                        <convert type="TemplatedMultiContent">
                            {"template": [
                                MultiContentEntryText(pos = (10, 0), size = (380, 30), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 0 is the name
                            ],
                        "fonts": [gFont("jediregular", 24)],
                        "itemHeight": 36
                        }
                        </convert>
                    </widget>
                </screen>"""

        Screen.__init__(self, session)
        self.session = session

        self.skin = skin

        self.list = []
        self.catchup_all = []
        self.currentSelection = 0

        self["newlist"] = List(self.list)

        self["actions"] = ActionMap(["JediMakerXtreamActions"], {
            "ok": self.openSelected,
            "cancel": self.quit,
        }, -2)

        self.setup_title = ""
        self.createSetup()
        self["newlist"].onSelectionChanged.append(self.getCurrentEntry)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def getCurrentEntry(self):
        self.currentSelection = self["newlist"].getIndex()

    def quit(self):
        self.close()

    def openSelected(self):
        self.returnValue = self["newlist"].getCurrent()[1]
        if self.returnValue is not None:
            self.getSelectedDateData()
        return

    def createSetup(self):
        self.list = []

        self.setup_title = "%s" % glob.name.lstrip(cfg.catchupprefix.value)
        for date in glob.dates:
            self.list.append((str(date[0]), str(date[1])))

        # self["newlist"].list = self.list.reverse()
        self.list.reverse()
        self["newlist"].setList(self.list)

    def getSelectedDateData(self):
        selectedArchive = []

        if self.returnValue == "9999-99-99":
            return
        if self.returnValue == "0000-00-00":
            selectedArchive = glob.archive
        else:
            for listing in glob.archive:
                if "start" in listing:
                    if listing["start"].startswith(str(self.returnValue)):
                        selectedArchive.append(listing)

        self.session.open(JediMakerXtream_Catchup_Listings, selectedArchive)


class JediMakerXtream_Catchup_Listings(Screen):
    def __init__(self, session, archive):

        Screen.__init__(self, session)
        self.session = session

        skin = os.path.join(skin_path, "catchup.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self.archive = archive
        self.setup_title = _("TV Archive: %s" % glob.name.lstrip(cfg.catchupprefix.value))

        self.list = []
        self.catchup_all = []
        self["list"] = List(self.list)
        self["description"] = Label("")
        self["actions"] = ActionMap(["JediMakerXtreamActions"], {
            "ok": self.play,
            "cancel": self.quit,
            "red": self.quit,
        }, -2)

        self["key_red"] = StaticText(_("Close"))
        self.getlistings()
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        if self.list != []:
            self.getCurrentEntry()

    def quit(self):
        self.close()

    def getlistings(self):

        epg_title = ""
        epg_description = ""

        shift = 0

        start = ""
        start_timestamp_o = ""

        end = ""
        stop_timestamp_o = ""

        start_timestamp = ""
        start_timestamp_datestamp = ""

        stop_timestamp = ""
        stop_timestamp_datestamp = ""

        epg_date_all = ""
        epg_time_all = ""

        catchupstart = ""
        catchupend = ""

        epg_duration = ""

        self.index = 0
        for listing in self.archive:

            if "title" in listing:
                epg_title = base64.b64decode(listing["title"]).decode("utf-8")

            if "description" in listing:
                epg_description = base64.b64decode(listing["description"]).decode("utf-8")

            shift = int(glob.catchupshift)

            if "start" in listing:
                start = listing["start"]
                start_timestamp_o = int(time.mktime(time.strptime(start, "%Y-%m-%d %H:%M:%S")))

            if "end" in listing:
                end = listing["end"]
                stop_timestamp_o = int(time.mktime(time.strptime(end, "%Y-%m-%d %H:%M:%S")))

            if "start_timestamp" in listing:
                start_timestamp = int(listing["start_timestamp"])
                start_timestamp_datestamp = datetime.fromtimestamp(start_timestamp)

            if "stop_timestamp" in listing:
                stop_timestamp = int(listing["stop_timestamp"])
                stop_timestamp_datestamp = datetime.fromtimestamp(stop_timestamp)

            epg_date_all = "%s %s" % (start_timestamp_datestamp.strftime("%a"), start_timestamp_datestamp.strftime("%d/%m"))

            epg_time_all = "%s - %s" % (start_timestamp_datestamp.strftime("%H:%M"), stop_timestamp_datestamp.strftime("%H:%M"))

            catchupstart = int(cfg.catchupstart.getValue())
            catchupend = int(cfg.catchupend.getValue())

            start_timestamp_o -= (catchupstart * 60)
            stop_timestamp_o += (catchupend * 60)

            epg_duration = int(stop_timestamp_o - start_timestamp_o) / 60

            start_timestamp_o += (shift * 60 * 60)

            url_datestring = str((datetime.fromtimestamp(start_timestamp_o).strftime("%Y-%m-%d %H:%M:%S")).replace(":", "-").replace(" ", ":"))[0:16]

            self.catchup_all.append([self.index, str(epg_date_all), str(epg_time_all), str(epg_title), str(epg_description), str(url_datestring), str(epg_duration)])

            self.index += 1

        self.createSetup()

    def createSetup(self):
        self.list = []

        self.catchup_all.reverse()
        for listing in self.catchup_all:
            self.list.append((str(listing[0]), str(listing[1]), str(listing[2]), str(listing[3]), str(listing[4]), str(listing[5]), str(listing[6])))

        self["list"].setList(self.list)

        if self.list != []:
            self["list"].onSelectionChanged.append(self.getCurrentEntry)

    def play(self):
        playurl = "%s/streaming/timeshift.php?username=%s&password=%s&stream=%s&start=%s&duration=%s" % (glob.domain, glob.username, glob.password, glob.refstreamnum, self.catchup_all[self.currentSelection][5], self.catchup_all[self.currentSelection][6])
        streamtype = 4097
        sref = eServiceReference(streamtype, 0, playurl)
        sref.setName(self.catchup_all[self.currentSelection][3])
        self.session.open(MoviePlayer, sref)

    def getCurrentEntry(self):
        self.currentSelection = self["list"].getIndex()
        self["description"].setText(self.catchup_all[self.currentSelection][4])
