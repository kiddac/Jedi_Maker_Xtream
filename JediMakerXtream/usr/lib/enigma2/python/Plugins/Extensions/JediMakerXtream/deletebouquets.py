#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import globalfunctions as jfunc
from . import jedi_globals as glob

from .plugin import skin_path, playlists_json
from .jediStaticText import StaticText

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List

from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap

import json
import os
import re


class JediMakerXtream_DeleteBouquets(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, "bouquets.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        self.setup_title = _("Delete Bouquets")

        self.startList = []
        self.drawList = []
        self["list"] = List(self.drawList)

        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Delete"))
        self["key_yellow"] = StaticText(_("Invert"))
        self["key_blue"] = StaticText(_("Clear All"))
        self["key_info"] = StaticText("")
        self["description"] = Label(_("Select all the iptv bouquets you wish to delete. \nPress OK to invert the selection"))
        self["lab1"] = Label("")

        self.playlists_all = jfunc.getPlaylistJson()

        self.onLayoutFinish.append(self.__layoutFinished)

        self["actions"] = ActionMap(["JediMakerXtreamActions"], {
            "red": self.keyCancel,
            "green": self.deleteBouquets,
            "yellow": self.toggleAllSelection,
            "blue": self.clearAllSelection,
            "cancel": self.keyCancel,
            "ok": self.toggleSelection
        }, -2)

        self.getStartList()
        self.refresh()

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def buildListEntry(self, name, index, enabled):
        if enabled:
            pixmap = LoadPixmap(cached=True, path=os.path.join(skin_path, "images/lock_on.png"))
        else:
            pixmap = LoadPixmap(cached=True, path=os.path.join(skin_path, "images/lock_off.png"))
        return (pixmap, str(name), index, enabled)

    def getStartList(self):
        for playlist in self.playlists_all:
            if "bouquet_info" in playlist and "oldname" in playlist["bouquet_info"]:
                self.startList.append([str(playlist["bouquet_info"]["oldname"]), playlist["playlist_info"]["index"], False])

        self.drawList = [self.buildListEntry(x[0], x[1], x[2]) for x in self.startList]
        self["list"].setList(self.drawList)

    def refresh(self):
        self.drawList = []
        self.drawList = [self.buildListEntry(x[0], x[1], x[2]) for x in self.startList]
        self["list"].updateList(self.drawList)

    def toggleSelection(self):
        if len(self["list"].list) > 0:
            idx = self["list"].getIndex()
            self.startList[idx][2] = not self.startList[idx][2]
            self.refresh()

    def toggleAllSelection(self):
        for idx, item in enumerate(self["list"].list):
            self.startList[idx][2] = not self.startList[idx][2]
        self.refresh()

    def getSelectionsList(self):
        return [item[0] for item in self.startList if item[2]]

    def clearAllSelection(self):
        for idx, item in enumerate(self["list"].list):
            self.startList[idx][2] = False
        self.refresh()

    def keyCancel(self):
        self.close()

    def deleteBouquets(self):
        selectedBouquetList = self.getSelectionsList()

        for x in selectedBouquetList:
            bouquet_name = x

            safeName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", str(bouquet_name))
            safeName = re.sub(r" ", "_", safeName)
            safeName = re.sub(r"_+", "_", safeName)

            with open("/etc/enigma2/bouquets.tv", "r+") as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if "jedimakerxtream_live_" + str(safeName) + "_" in line or \
                            "jedimakerxtream_vod_" + str(safeName) + "_" in line or \
                            "jedimakerxtream_series_" + str(safeName) + "_" in line or \
                            "jedimakerxtream_" + str(safeName) in line or \
                            "jmx_live_" + str(safeName) + "_" in line or \
                            "jmx_vod_" + str(safeName) + "_" in line or \
                            "jmx_series_" + str(safeName) + "_" in line or \
                            "jmx_" + str(safeName) in line:
                        continue
                    f.write(line)
                f.truncate()

            jfunc.purge("/etc/enigma2", "jedimakerxtream_live_" + str(safeName) + "_")
            jfunc.purge("/etc/enigma2", "jedimakerxtream_vod_" + str(safeName) + "_")
            jfunc.purge("/etc/enigma2", "jedimakerxtream_series_" + str(safeName) + "_")
            jfunc.purge("/etc/enigma2", "jmx_live_" + str(safeName) + "_")
            jfunc.purge("/etc/enigma2", "jmx_vod_" + str(safeName) + "_")
            jfunc.purge("/etc/enigma2", "jmx_series_" + str(safeName) + "_")
            jfunc.purge("/etc/enigma2", str(safeName) + str(".tv"))

            if glob.has_epg_importer:
                jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeName) + ".channels.xml")
                jfunc.purge("/etc/epgimport", "jmx." + str(safeName) + ".channels.xml")

                # remove sources from source file
                sourcefile = "/etc/epgimport/jedimakerxtream.sources.xml"

                if os.path.isfile(sourcefile):

                    import xml.etree.ElementTree as ET
                    tree = ET.parse(sourcefile)
                    root = tree.getroot()

                    for elem in root.iter():
                        for child in list(elem):
                            description = ""
                            if child.tag == "source":
                                try:
                                    description = child.find("description").text
                                    if safeName in description:
                                        elem.remove(child)
                                except:
                                    pass

                    tree.write(sourcefile)

            self.deleteBouquetFile(bouquet_name)
            glob.firstrun = 0
            glob.current_selection = 0
            glob.current_playlist = []
            jfunc.refreshBouquets()
        self.close()

    def deleteBouquetFile(self, bouquet_name):
        for playlist in self.playlists_all:
            if "bouquet_info" in playlist and "name" in playlist["bouquet_info"]:
                if playlist["bouquet_info"]["name"] == bouquet_name:
                    del playlist["bouquet_info"]

        glob.bouquets_exist = False
        for playlist in self.playlists_all:
            if "bouquet_info" in playlist:
                glob.bouquets_exist = True
                break

        if glob.bouquets_exist is False:
            jfunc.resetUnique()

        # delete leftover empty dicts
        self.playlists_all = [_f for _f in self.playlists_all if _f]

        with open(playlists_json, "w") as f:
            json.dump(self.playlists_all, f)
