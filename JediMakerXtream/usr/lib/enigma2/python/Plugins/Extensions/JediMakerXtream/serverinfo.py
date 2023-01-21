#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import jedi_globals as glob
from .plugin import skin_path
from .jediStaticText import StaticText

from Components.Label import Label
from Components.ActionMap import ActionMap
from datetime import datetime
from Screens.Screen import Screen

import json


class JediMakerXtream_UserInfo(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin = skin_path + "userinfo.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

        self.setup_title = _("User Information")

        self["authorised"] = Label("")
        self["status"] = Label("")
        self["expiry"] = Label("")
        self["created"] = Label("")
        self["trial"] = Label("")
        self["activeconn"] = Label("")
        self["maxconn"] = Label("")
        self["formats"] = Label("")
        self["realurl"] = Label("")
        self["timezone"] = Label("")
        self["serveroffset"] = Label("")

        # fake labels for skin text translations
        t_status = _("Status:")
        t_istrial = _("Is Trial:")
        t_activeconnections = _("Active Connections:")
        t_maxconnections = _("Max Connections:")
        t_createdat = _("Created At:")
        t_expirydate = _("Expiry Date:")
        t_allowedformats = _("Allowed Output Formats:")
        t_realurl = _("Real URL:")
        t_timezone = _("Timezone:")
        t_serveroffset = _("Server Offset:")

        self["actions"] = ActionMap(["JediMakerXtreamActions"], {
            "ok": self.quit,
            "cancel": self.quit,
            "red": self.quit,
            "menu": self.quit}, -2)

        self["key_red"] = StaticText(_("Back"))
        self["key_green"] = StaticText(_("OK"))

        self.onFirstExecBegin.append(self.createUserSetup)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def createUserSetup(self):
        if "auth" in glob.current_playlist["user_info"]:
            self["authorised"].setText(str(glob.current_playlist["user_info"]["auth"]))

        if "status" in glob.current_playlist["user_info"]:
            self["status"].setText(str(glob.current_playlist["user_info"]["status"]))

        if "exp_date" in glob.current_playlist["user_info"]:
            try:
                self["expiry"].setText(str(datetime.fromtimestamp(int(glob.current_playlist["user_info"]["exp_date"])).strftime("%d-%m-%Y  %H:%M")))
            except:
                self["expiry"].setText("Null")

        if "created_at" in glob.current_playlist["user_info"]:
            try:
                self["created"].setText(str(datetime.fromtimestamp(int(glob.current_playlist["user_info"]["created_at"])).strftime("%d-%m-%Y  %H:%M")))
            except:
                self["created"].setText("Null")

        if "is_trial" in glob.current_playlist["user_info"]:
            self["trial"].setText(str(glob.current_playlist["user_info"]["is_trial"]))

        if "active_cons" in glob.current_playlist["user_info"]:
            self["activeconn"].setText(str(glob.current_playlist["user_info"]["active_cons"]))

        if "max_connections" in glob.current_playlist["user_info"]:
            self["maxconn"].setText(str(glob.current_playlist["user_info"]["max_connections"]))

        if "allowed_output_formats" in glob.current_playlist["user_info"]:
            self["formats"].setText(str(json.dumps(glob.current_playlist["user_info"]["allowed_output_formats"])).lstrip("[").rstrip("]"))

        if "url" in glob.current_playlist["server_info"]:
            self["realurl"].setText(str(glob.current_playlist["server_info"]["url"]))

        if "timezone" in glob.current_playlist["server_info"]:
            self["timezone"].setText(str(glob.current_playlist["server_info"]["timezone"]))

        """
        if "serveroffset" in glob.current_playlist["settings"]:
            self["serveroffset"].setText(str(glob.current_playlist["settings"]["serveroffset"]))
            """

    def quit(self):
        self.close()
