#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import jedi_globals as glob

from Components.ActionMap import HelpableActionMap
from Components.config import config, ConfigSelection, ConfigNumber, ConfigClock, ConfigDirectory, ConfigSubsection, ConfigYesNo, ConfigSelectionNumber
from enigma import eTimer, eServiceReference, getDesktop, addFont
from Plugins.Plugin import PluginDescriptor
from Screens.EpgSelection import EPGSelection
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference

import twisted.python.runtime

try:
    from multiprocessing.pool import ThreadPool
    hasMultiprocessing = True
except:
    hasMultiprocessing = False

try:
    from concurrent.futures import ThreadPoolExecutor
    if twisted.python.runtime.platform.supportsThreads():
        hasConcurrent = True
    else:
        hasConcurrent = False
except:
    hasConcurrent = False

import os
import shutil
import sys

pythonFull = float(str(sys.version_info.major) + "." + str(sys.version_info.minor))
pythonVer = sys.version_info.major

isDreambox = False
if os.path.exists("/usr/bin/apt-get"):
    isDreambox = True

with open("/usr/lib/enigma2/python/Plugins/Extensions/JediMakerXtream/version.txt", "r") as f:
    version = f.readline()

screenwidth = getDesktop(0).size()

dir_etc = "/etc/enigma2/jediplaylists/"
dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/JediMakerXtream/"

if screenwidth.width() == 2560:
    skin_directory = os.path.join(dir_plugins, "skin/uhd/")
elif screenwidth.width() > 1280:
    skin_directory = os.path.join(dir_plugins, "skin/fhd/")
else:
    skin_directory = os.path.join(dir_plugins, "skin/hd/")

folders = os.listdir(skin_directory)
streamtype_choices = [("1", "DVB(1)"), ("4097", "IPTV(4097)")]

if os.path.exists("/usr/bin/gstplayer"):
    streamtype_choices.append(("5001", "GStreamer(5001)"))

if os.path.exists("/usr/bin/exteplayer3"):
    streamtype_choices.append(("5002", "ExtePlayer(5002)"))

if os.path.exists("/usr/bin/apt-get"):
    streamtype_choices.append(("8193", "GStreamer(8193)"))

config.plugins.JediMakerXtream = ConfigSubsection()
cfg = config.plugins.JediMakerXtream
cfg.livetype = ConfigSelection(default="4097", choices=streamtype_choices)
cfg.location = ConfigDirectory(default=dir_etc)
cfg.m3ulocation = ConfigDirectory(default=dir_etc)
cfg.main = ConfigYesNo(default=True)
cfg.unique = ConfigNumber()
cfg.usershow = ConfigSelection(default="domain", choices=[("domain", _("Domain")), ("domainconn", _("Domain | Connections"))])
cfg.enabled = ConfigYesNo(default=False)
cfg.wakeup = ConfigClock(default=((7 * 60) + 9) * 60)  # 7:00
cfg.skin = ConfigSelection(default="default", choices=folders)
cfg.bouquet_id = ConfigNumber()
cfg.timeout = ConfigSelectionNumber(1, 20, 1, default=10, wraparound=True)
cfg.catchup = ConfigYesNo(default=False)
cfg.catchupprefix = ConfigSelection(default="~", choices=[("~", "~"), ("!", "!"), ("#", "#"), ("-", "-"), ("<", "<"), ("^", "^")])
cfg.catchupstart = ConfigSelectionNumber(0, 30, 1, default=0, wraparound=True)
cfg.catchupend = ConfigSelectionNumber(0, 30, 1, default=0, wraparound=True)
cfg.groups = ConfigYesNo(default=False)

skin_path = os.path.join(skin_directory, cfg.skin.value)

# create folder for working files
if not os.path.exists(dir_etc):
    os.makedirs(dir_etc)

playlists_json = os.path.join(dir_etc, "playlist_all_new.json")
playlist_file = os.path.join(dir_etc, "playlists.txt")

print("*** playlist_file ***", playlist_file)

if cfg.location.value:
    print("*** location true ***")
    playlist_file = os.path.join(cfg.location.value, "playlists.txt")

print("*** playlist_file ***", playlist_file)

# check if playlists.txt file exists in specified location
if not os.path.isfile(playlist_file):
    open(playlist_file, "a").close()

# check if playlists.json file exists in specified location
if not os.path.isfile(playlists_json):
    open(playlists_json, "a").close()

rytec_url = "http://www.xmltvepg.nl/rytec.channels.xml.xz"
rytec_file = os.path.join(dir_etc, "rytec.channels.xml.xz")
alias_file = os.path.join(dir_etc, "alias.txt")
sat28_file = os.path.join(dir_etc, "28.2e.txt")

font_folder = os.path.join(dir_plugins, "fonts/")

"""
hdr = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"Accept-Language": "en-GB,en;q=0.5",
"Accept-Encoding": "gzip, deflate",
}
"""

hdr = {"User-Agent": "Enigma2 - JediMakerXtream Plugin"}

if os.path.isdir("/usr/lib/enigma2/python/Plugins/Extensions/EPGImport"):
    glob.has_epg_importer = True
    if not os.path.exists("/etc/epgimport"):
        os.makedirs("/etc/epgimport")
else:
    glob.has_epg_importer = False
    glob.epg_provider = False

# try and override epgimport settings
try:
    config.plugins.epgimport.import_onlybouquet.value = False
    config.plugins.epgimport.import_onlybouquet.save()
except Exception as e:
    print(e)

# remove dodgy versions of my plugin
if os.path.isdir("/usr/lib/enigma2/python/Plugins/Extensions/XStreamityPro/"):
    try:
        shutil.rmtree("/usr/lib/enigma2/python/Plugins/Extensions/XStreamityPro/")
    except Exception as e:
        print(e)


def main(session, **kwargs):
    from . import mainmenu
    session.open(mainmenu.JediMakerXtream_MainMenu)
    return


def mainmenu(menu_id, **kwargs):
    if menu_id == "mainmenu":
        return [(_("Jedi Maker Xtream"), main, "JediMakerXtream", 49)]
    else:
        return []


def extensionsmenu(session, **kwargs):
    from . import mainmenu
    session.open(mainmenu.JediMakerXtream_MainMenu)
    return


vixEPG = False
try:
    from Screens.EpgSelectionGrid import EPGSelectionGrid
    vixEPG = True
except Exception as e:
    print(e)


autoStartTimer = None


class AutoStartTimer:
    def __init__(self, session):
        self.session = session
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.onTimer)
        except:
            self.timer.callback.append(self.onTimer)
        self.update()

    def getWakeTime(self):
        import time
        if cfg.enabled.value:
            clock = cfg.wakeup.value
            nowt = time.time()
            now = time.localtime(nowt)
            return int(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, clock[0], clock[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
        else:
            return -1

    def update(self, atLeast=0):
        import time
        self.timer.stop()
        wake = self.getWakeTime()
        nowtime = time.time()
        if wake > 0:
            if wake < nowtime + atLeast:
                # Tomorrow.
                wake += 24 * 3600
            next = wake - int(nowtime)
            if next > 3600:
                next = 3600
            if next <= 0:
                next = 60
            self.timer.startLongTimer(next)
        else:
            wake = -1
        return wake

    def onTimer(self):
        import time
        self.timer.stop()
        now = int(time.time())
        wake = self.getWakeTime()
        atLeast = 0
        if abs(wake - now) < 60:
            self.runUpdate()
            atLeast = 60
        self.update(atLeast)

    def runUpdate(self):
        print("\n *********** Updating Jedi Bouquets************ \n")
        from . import update
        self.session.open(update.JediMakerXtream_Update, "auto")


def autostart(reason, session=None, **kwargs):

    if session is not None:
        global jediEPGSelection__init__
        jediEPGSelection__init__ = EPGSelection.__init__

        if vixEPG:
            global jediEPGSelectionGrid__init__
            jediEPGSelectionGrid__init__ = EPGSelectionGrid.__init__

            try:
                check = EPGSelectionGrid.togglePIG
                EPGSelectionGrid.__init__ = EPGSelectionVIX__init__
                EPGSelectionGrid.showJediCatchup = showJediCatchup
                EPGSelectionGrid.playOriginalChannel = playOriginalChannel
            except AttributeError:
                print("******** VIX check failed *****")
        else:
            try:
                check = EPGSelection.setPiPService
                EPGSelection.__init__ = EPGSelectionVTi__init__
            except AttributeError:
                print("******** VTI check failed *****")
                try:
                    check = EPGSelection.togglePIG
                    EPGSelection.__init__ = EPGSelectionATV__init__
                except AttributeError:
                    print("******** ATV check failed *****")
                    try:
                        check = EPGSelection.runPlugin
                        EPGSelection.__init__ = EPGSelectionPLI__init__
                    except AttributeError:
                        print("******** PLI check failed *****")
                        EPGSelection.__init__ = EPGSelection__init__

            EPGSelection.showJediCatchup = showJediCatchup
            EPGSelection.playOriginalChannel = playOriginalChannel

    global autoStartTimer
    if reason == 0:
        if session is not None:
            if autoStartTimer is None:
                autoStartTimer = AutoStartTimer(session)
    return


def EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
    print("**** EPGSelection ****")
    jediEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
    self["jediCatchupAction"] = HelpableActionMap(self, "JediCatchupActions", {
        "catchup": self.showJediCatchup,
    })


def EPGSelectionVTi__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, isEPGBar=None, switchBouquet=None, EPGNumberZap=None, togglePiP=None):
    print("**** EPGSelectionVTi ****")
    jediEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, isEPGBar, switchBouquet, EPGNumberZap, togglePiP)
    self["jediCatchupAction"] = HelpableActionMap(self, "JediCatchupActions", {
        "catchup": self.showJediCatchup,
    })


def EPGSelectionATV__init__(self, session, service=None, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, EPGtype=None, StartBouquet=None, StartRef=None, bouquets=None):
    print("**** EPGSelectionATV ****")
    jediEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, EPGtype, StartBouquet, StartRef, bouquets)
    if EPGtype != "vertical":
        self["jediCatchupAction"] = HelpableActionMap(self, "JediCatchupActions", {
            "catchup": self.showJediCatchup,
        })


def EPGSelectionVIX__init__(self, session, zapFunc, startBouquet, startRef, bouquets, timeFocus=None, isInfobar=False):
    print("**** EPGSelectionVIX ****")
    jediEPGSelectionGrid__init__(self, session, zapFunc, startBouquet, startRef, bouquets, timeFocus, isInfobar)
    self["jediCatchupAction"] = HelpableActionMap(self, "JediCatchupActions", {
        "catchup": self.showJediCatchup,
    })


def EPGSelectionPLI__init__(self, session, service=None, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, parent=None):
    print("**** EPGSelectionPLI ****")
    jediEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, parent)
    self["jediCatchupAction"] = HelpableActionMap(self, "JediCatchupActions", {
        "catchup": self.showJediCatchup,
    })


def showJediCatchup(self):

    error_message = ""
    hascatchup = False

    self.oldref = self.session.nav.getCurrentlyPlayingServiceReference()
    self.oldrefstring = self.oldref.toString()

    listcurrent = self["list"].getCurrent()
    service_ref = listcurrent[1]

    current_service = service_ref.ref.toString()

    if self.oldrefstring != current_service:
        self.session.nav.playService(eServiceReference(current_service))
    service = self.session.nav.getCurrentService()

    glob.currentref = self.session.nav.getCurrentlyPlayingServiceReference()
    glob.currentrefstring = glob.currentref.toString()
    glob.name = ServiceReference(glob.currentref).getServiceName()

    self.playOriginalChannel()

    if service.streamed():
        from . import catchup
        try:
            error_message, hascatchup = catchup.downloadSimpleData()
        except Exception as e:
            print(e)

        if error_message != "":
            self.session.open(MessageBox, "%s" % error_message, MessageBox.TYPE_ERROR, timeout=5)
        elif hascatchup:
            self.session.openWithCallback(self.playOriginalChannel, catchup.JediMakerXtream_Catchup)
    else:
        self.session.open(MessageBox, _("Catchup only available on IPTV Streams."), MessageBox.TYPE_ERROR, timeout=5)


def playOriginalChannel(self):
    if self.oldrefstring != glob.currentrefstring:
        self.session.nav.playService(eServiceReference(self.oldrefstring))


def Plugins(**kwargs):
    addFont(os.path.join(font_folder, "SourceSansPro-Regular.ttf"), "jediregular", 100, 0)
    addFont(os.path.join(font_folder, "slyk-regular.ttf"), "slykregular", 100, 0)
    addFont(os.path.join(font_folder, "slyk-medium.ttf"), "slykbold", 100, 0)
    addFont(os.path.join(font_folder, "MavenPro-Regular.ttf"), "onyxregular", 100, 0)
    addFont(os.path.join(font_folder, "MavenPro-Medium.ttf"), "onyxbold", 100, 0)
    addFont(os.path.join(font_folder, "VSkin-Light.ttf"), "vskinregular", 100, 0)
    addFont(os.path.join(font_folder, "m-plus-rounded-1c-regular.ttf"), "mplusregular", 100, 0)
    addFont(os.path.join(font_folder, "m-plus-rounded-1c-medium.ttf"), "mplusbold", 100, 0)

    iconFile = "icons/JediMakerXtream.png"
    if screenwidth.width() > 1280:
        iconFile = "icons/JediMakerXtreamFHD.png"
    description = _("IPTV Bouquets Creator by KiddaC")
    pluginname = _("JediMakerXtream")

    main_menu = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_MENU, fnc=mainmenu, needsRestart=True)

    extensions_menu = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=extensionsmenu, needsRestart=True)

    result = [PluginDescriptor(name=pluginname, description=description, where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_PLUGINMENU, icon=iconFile, fnc=main)]

    result.append(extensions_menu)

    if cfg.main.getValue():
        result.append(main_menu)

    return result
