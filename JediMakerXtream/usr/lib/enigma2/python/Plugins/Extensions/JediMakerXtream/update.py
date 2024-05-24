#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _

from .plugin import skin_path, playlists_json, hdr, cfg, screenwidth

from . import buildxml as bx
from . import downloads
from . import globalfunctions as jfunc
from . import jedi_globals as glob

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from datetime import datetime
from enigma import eTimer

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

import json
import socket
import os
import sys

socket.setdefaulttimeout(5.0)

pythonVer = 2
if sys.version_info.major == 3:
    pythonVer = 3

if pythonVer == 3:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
else:
    from urllib2 import urlopen, Request, URLError


class JediMakerXtream_Update(Screen):

    def __init__(self, session, runtype):
        Screen.__init__(self, session)
        self.session = session
        self.runtype = runtype

        if os.path.isdir("/usr/lib/enigma2/python/Plugins/Extensions/EPGImport"):
            glob.has_epg_importer = True
            if not os.path.exists("/etc/epgimport"):
                os.makedirs("/etc/epgimport")
        else:
            glob.has_epg_importer = False

        if self.runtype == "manual":
            skin = os.path.join(skin_path, "progress.xml")
            with open(skin, "r") as f:
                self.skin = f.read()

        else:
            skin = """
                <screen name="Updater" position="0,0" size="1920,1080" backgroundColor="#ff000000" flags="wfNoBorder">
                    <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/JediMakerXtream/icons/JediMakerXtreamFHD.png" position="30,25" size="150,60" alphatest="blend" zPosition="4"  />
                    <eLabel position="180,30" size="360,50" backgroundColor="#10232323" transparent="0" zPosition="-1"/>
                    <widget name="status" position="210,30" size="300,50" font="Regular;24" foregroundColor="#ffffff" backgroundColor="#000000" valign="center" noWrap="1" transparent="1" zPosition="5" />
                </screen>"""

            if screenwidth.width() <= 1280:
                skin = """
                    <screen name="Updater" position="0,0" size="1280,720" backgroundColor="#ff000000" flags="wfNoBorder">
                        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/JediMakerXtream/icons/JediMakerXtream.png" position="20,16" size="100,40" alphatest="blend" zPosition="4" />
                        <eLabel position="120,20" size="240,32" backgroundColor="#10232323" transparent="0" zPosition="-1"/>
                        <widget name="status" position="140,20" size="200,32" font="Regular;16" foregroundColor="#ffffff" backgroundColor="#000000" valign="center" noWrap="1" transparent="1" zPosition="5" />
                    </screen>"""

            self.skin = skin

        Screen.setTitle(self, _("Updating Bouquets"))

        self["action"] = Label("")
        self["status"] = Label("")
        self["progress"] = ProgressBar()
        self["actions"] = ActionMap(["JediMakerXtreamActions"], {
            "cancel": self.keyCancel,
            "red": self.keyCancel
        }, -2)

        self.pause = 20
        self.job_bouquet_name = ""

        self.x = 0

        self.playlists_bouquets = []
        self.playlists_all = jfunc.getPlaylistJson()

        for playlist in self.playlists_all:
            if "bouquet_info" in playlist:
                self.playlists_bouquets.append(playlist)

        self.progresscount = len(self.playlists_bouquets)
        self.progresscurrent = 0
        self["progress"].setRange((0, self.progresscount))
        self["progress"].setValue(self.progresscurrent)

        self.rytec_ref = {}
        self.epg_alias_names = []

        if self.playlists_bouquets != []:
            self.start()
        else:
            self.close()

    def keyCancel(self):
        self.close()

    def nextjob(self, actiontext, function):
        self["action"].setText(actiontext)
        self.timer = eTimer()
        self.timer.start(self.pause, True)
        try:
            self.timer_conn = self.timer.timeout.connect(function)
        except:
            self.timer.callback.append(function)

    def start(self):
        if glob.epg_rytec_uk:
            self.nextjob(_("Downloading Rytec UK EPG data..."), self.downloadrytec)
        else:
            self.nextjob(_("Starting Update..."), self.loopPlaylists)

    def downloadrytec(self):
        self.rytec_ref, self.epg_alias_names = downloads.downloadrytec()
        self.nextjob(_("Starting Update..."), self.loopPlaylists)

    def loopPlaylists(self):
        if self.x < len(self.playlists_bouquets):
            self.catloop()
        else:
            if self.runtype == "manual":
                self.session.openWithCallback(self.done, MessageBox, str(len(self.playlists_bouquets)) + _(" Providers IPTV Updated"), MessageBox.TYPE_INFO, timeout=5)
            else:
                self.done()

    def catloop(self):
        self.category_num = 0
        self.firstrun = True
        glob.categories = []
        self.m3uValues = []
        self.valid = False
        glob.current_playlist = self.playlists_bouquets[self.x]

        self["progress"].setRange((0, self.progresscount))
        self["progress"].setValue(self.progresscurrent)
        self.progresscurrent += 1

        self["status"].setText(_("Updating Playlist %d of %d") % (self.progresscurrent, self.progresscount))
        self.nextjob(_("%s - Reading bouquet data...") % str(glob.name), self.readbouquetdata)

        self.x += 1

    def readbouquetdata(self):
        jfunc.readbouquetdata()

        self.address = glob.current_playlist["playlist_info"]["address"]
        self.playlisttype = glob.current_playlist["playlist_info"]["playlisttype"]

        if self.playlisttype != "local":
            self.protocol = glob.current_playlist["playlist_info"]["protocol"]
            self.xmltvprotocol = self.protocol
            self.domain = glob.current_playlist["playlist_info"]["domain"]
            self.port = str(glob.current_playlist["playlist_info"]["port"])
            if str(self.port).isdigit():
                self.host = str(self.protocol) + str(self.domain) + ":" + str(self.port) + "/"
                self.xmltvhost = str(self.xmltvprotocol) + str(self.domain) + ":" + str(self.port) + "/"
            else:
                self.host = str(self.protocol) + str(self.domain) + "/"
                self.xmltvhost = str(self.xmltvprotocol) + str(self.domain) + "/"

        if self.playlisttype == "xtream":
            self.username = glob.current_playlist["playlist_info"]["username"]
            self.password = glob.current_playlist["playlist_info"]["password"]
            self.type = glob.current_playlist["playlist_info"]["type"]
            self.output = glob.current_playlist["playlist_info"]["output"]

            self.player_api = str(self.host) + "player_api.php?username=" + str(self.username) + "&password=" + str(self.password)
            self.get_api = str(self.host) + "get.php?username=" + str(self.username) + "&password=" + str(self.password) + "&type=m3u_plus&output=" + str(self.output)

            glob.xmltv_address = str(self.xmltvhost) + "xmltv.php?username=" + str(self.username) + "&password=" + str(self.password)

            self.LiveCategoriesUrl = self.player_api + "&action=get_live_categories"
            self.VodCategoriesUrl = self.player_api + "&action=get_vod_categories"
            self.SeriesCategoriesUrl = self.player_api + "&action=get_series_categories"

            self.LiveStreamsUrl = self.player_api + "&action=get_live_streams"
            self.VodStreamsUrl = self.player_api + "&action=get_vod_streams"
            self.SeriesUrl = self.player_api + "&action=get_series"

        if self.playlisttype == "xtream":
            self.nextjob(_("%s - Checking URL still active...") % str(glob.name), self.checkactive)
        else:
            self.nextjob(_("%s - Download M3U Data...") % str(glob.name), self.getM3uCategories)

    def checkactive(self):
        response = None
        self.valid = False
        req = Request(self.player_api, headers=hdr)

        try:
            response = urlopen(req, timeout=5)
            self.valid = True
        except URLError as e:
            print(e)
            pass
        except socket.timeout as e:
            print(e)
            pass
        except:
            pass

        if self.valid:
            try:
                self.active = json.load(response)
                if "user_info" in self.active:
                    if self.active["user_info"]["auth"] == 1:
                        self.valid = True
                        glob.current_playlist['user_info'] = self.active['user_info']
                    else:
                        self.valid = False
                if 'server_info' in self.active:
                    glob.current_playlist['server_info'] = self.active['server_info']
            except:
                self.valid = False
                pass

        if self.valid:
            if glob.live:
                self["action"].setText("Downloading Live data")

                self.timer1 = eTimer()
                self.timer1.start(self.pause, True)
                try:
                    self.timer1_conn = self.timer1.timeout.connect(self.downloadLive)

                except:
                    self.timer1.callback.append(self.downloadLive)

            elif glob.vod:
                self["action"].setText("Downloading VOD data")

                self.timer2 = eTimer()
                self.timer2.start(self.pause, True)
                try:
                    self.timer2_conn = self.timer2.timeout.connect(self.downloadVod)
                except:
                    self.timer2.callback.append(self.downloadVod)

            elif glob.series:
                self["action"].setText("Downloading Series data")

                self.timer3 = eTimer()
                self.timer3.start(self.pause, True)
                try:
                    self.timer3_conn = self.timer3.timeout.connect(self.downloadSeries)
                except:
                    self.timer3.callback.append(self.downloadSeries)
        else:
            self.nextjob((""), self.loopPlaylists)

    def downloadLive(self):
        downloads.downloadlivecategories(self.LiveCategoriesUrl)
        downloads.downloadlivestreams(self.LiveStreamsUrl)
        if glob.vod:
            self.nextjob(_("%s - Downloading VOD data...") % str(glob.name), self.downloadVod)
        elif glob.series:
            self.nextjob(_("%s - Downloading Series data...") % str(glob.name), self.downloadSeries)
        else:
            self.nextjob(_("%s - Getting categories...") % str(glob.name), self.getcategories)

    def downloadVod(self):
        downloads.downloadvodcategories(self.VodCategoriesUrl)
        downloads.downloadvodstreams(self.VodStreamsUrl)
        if glob.series:
            self.nextjob(_("%s - Downloading Series data...") % str(glob.name), self.downloadSeries)
        else:
            self.nextjob(_("%s - Getting categories...") % str(glob.name), self.getcategories)

    def downloadSeries(self):
        downloads.downloadseriescategories(self.SeriesCategoriesUrl)
        downloads.downloadseriesstreams(self.SeriesUrl)
        self.nextjob(_("%s - Getting categories...") % str(glob.name), self.getcategories)

    def getM3uCategories(self):
        downloads.getM3uCategories(glob.live, glob.vod)
        self.nextjob(_("%s - Get selected categories...") % str(glob.name), self.getSelected)

    def getcategories(self):
        glob.categories = []
        jfunc.getcategories()
        self.nextjob(_("%s - Getting selection list") % str(glob.name), self.ignoredcategories)

    def ignoredcategories(self):
        if "bouquet_info" in glob.current_playlist and glob.current_playlist["bouquet_info"] != {}:
            jfunc.IgnoredCategories()
        self.nextjob(_("%s - Get selected categories...") % str(glob.name), self.getSelected)

    def getSelected(self):
        if self.playlisttype == "xtream":
            glob.selectedcategories = []
            glob.ignoredcategories = []

            for category in glob.categories:
                if category[3] is True:
                    glob.selectedcategories.append(category)
                elif category[3] is False:
                    glob.ignoredcategories.append(category)

            self.categories = glob.selectedcategories

        if glob.current_playlist["playlist_info"]["playlisttype"] != "xtream":
            self.categories = []

        if self.playlisttype == "xtream" and glob.series:
            self.nextjob(_("%s - Downloading Data...") % str(glob.name), self.downloadgetfile)
        else:
            self.nextjob(_("%s - Deleting existing bouquets...") % str(glob.name), self.deleteBouquets)

    def downloadgetfile(self):
        self.m3uValues = downloads.downloadgetfile(self.get_api)
        self.nextjob(_("%s - Deleting existing bouquets...") % str(glob.name), self.deleteBouquets)

    def deleteBouquets(self):
        jfunc.deleteBouquets()

        if self.playlisttype == "xtream":
            self.nextjob(_("%s - Building bouquets...") % str(glob.name), self.buildBouquets)
        else:
            self.nextjob(_("%s - Building M3U bouquets...") % str(glob.name), self.buildM3uBouquets)

    def buildBouquets(self):
        self.epg_name_list = []
        self.process_category()

    def process_category(self):
        self.category_num = 0
        while self.category_num < len(self.categories):
            category_name = self.categories[self.category_num][0]
            category_type = self.categories[self.category_num][1]
            category_id = self.categories[self.category_num][2]
            self.protocol = self.protocol.replace(":", "%3a")

            self.epg_name_list = jfunc.process_category(category_name, category_type, category_id, self.domain, self.port, self.username, self.password, self.protocol, self.output, glob.current_playlist, self.epg_alias_names, self.epg_name_list, self.rytec_ref, self.m3uValues)
            self.category_num += 1

        if glob.live and glob.has_epg_importer and glob.epg_provider and glob.xmltv_address != "":
            if glob.fixepg:
                bx.downloadXMLTV()
            bx.buildXMLTVChannelFile(self.epg_name_list)
            bx.buildXMLTVSourceFile()
            self.updateBouquetJsonFile()
            # jfunc.refreshBouquets()

        self.nextjob((""), self.loopPlaylists)

    def buildM3uBouquets(self):
        self.categories = []

        for x in glob.getm3ustreams:
            if x[0] != "":
                if [x[0], x[4]] not in self.categories:
                    self.categories.append([x[0], x[4]])

        if self.firstrun is True:
            self.epg_name_list = []

            self.unique_ref = cfg.unique.value

        self.firstrun = False

        if self.category_num < len(self.categories):
            self.m3u_process_category()

        else:
            if glob.live and glob.has_epg_importer and glob.epg_provider and glob.xmltv_address != "":
                bx.buildXMLTVChannelFile(self.epg_name_list)
                bx.buildXMLTVSourceFile()
                self.updateBouquetJsonFile()
                # jfunc.refreshBouquets()

            self.nextjob((""), self.loopPlaylists)

    def m3u_process_category(self):
        category_name = self.categories[self.category_num][0]
        category_type = self.categories[self.category_num][1]
        self.epg_name_list = jfunc.m3u_process_category(category_name, category_type, self.unique_ref, self.epg_name_list, glob.current_playlist)
        self.category_num += 1
        self.buildM3uBouquets()

    def updateBouquetJsonFile(self):
        if glob.live:
            glob.current_playlist["bouquet_info"]["live_update"] = datetime.now().strftime("%x  %X")

        if glob.vod:
            glob.current_playlist["bouquet_info"]["vod_update"] = datetime.now().strftime("%x  %X")

        if glob.series:
            glob.current_playlist["bouquet_info"]["series_update"] = datetime.now().strftime("%x  %X")

        # replace only amended bouquet
        for playlist in self.playlists_all:
            if glob.current_playlist["playlist_info"]["address"] == playlist["playlist_info"]["address"]:
                playlist = glob.current_playlist

        # output to file
        with open(playlists_json, "w") as f:
            json.dump(self.playlists_all, f)

    def done(self, answer=None):
        jfunc.refreshBouquets()
        self.close()
