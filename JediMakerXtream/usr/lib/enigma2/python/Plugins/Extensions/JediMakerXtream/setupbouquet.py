#!/usr/bin/python
# -*- coding: utf-8 -*-

# for localized messages
from . import _

from . import buildbouquet
from . import downloads
from . import globalfunctions as jfunc
from . import jediglobals as jglob
from . import owibranding

from .plugin import skin_path, cfg, playlist_file


from collections import OrderedDict
from Components.ActionMap import ActionMap
from Components.config import getConfigListEntry, ConfigText, ConfigSelection, ConfigBoolean, ConfigYesNo, ConfigEnableDisable, NoSave
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from datetime import datetime
from enigma import eTimer

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap


import json
import os



class JediMakerXtream_Bouquets(ConfigListScreen, Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin = skin_path + 'jmx_settings.xml'

        self.dreamos = False

        try:
            from boxbranding import getImageDistro, getImageVersion, getOEVersion
        except:
            self.dreamos = True
            if owibranding.getMachineBrand() == "Dream Multimedia" or owibranding.getOEVersion() == "OE 2.2":
                skin = skin_path + 'DreamOS/jmx_settings.xml'

        with open(skin, 'r') as f:
            self.skin = f.read()

        self.setup_title = _('Bouquets Settings')

        self.onChangedEntry = []

        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)

        self.loaded = False

        self['information'] = Label('')

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Continue'))

        self['VirtualKB'].setEnabled(False)
        self['HelpWindow'] = Pixmap()
        self['VKeyIcon'] = Pixmap()
        self['HelpWindow'].hide()
        self['VKeyIcon'].hide()
        self['lab1'] = Label(_('Loading data... Please wait...'))

        self['actions'] = ActionMap(['SetupActions'], {
            'save': self.save,
            'cancel': self.cancel
        }, -2)

        self.pause = 100

        address = jglob.current_playlist['playlist_info']['address']
        self.playlisttype = jglob.current_playlist['playlist_info']['playlisttype']

        # defaults
        if cfg.bouquet_id.value:
            jglob.bouquet_id = cfg.bouquet_id.value
        else:
            jglob.bouquet_id = 666

        # if xtream or external
        if self.playlisttype != 'local':
            protocol = jglob.current_playlist['playlist_info']['protocol']
            domain = jglob.current_playlist['playlist_info']['domain']
            port = str(jglob.current_playlist['playlist_info']['port'])
            host = str(protocol) + str(domain) + ':' + str(port) + '/'
            jglob.name = domain
        else:
            jglob.name = address

        if self.playlisttype == 'xtream':
            username = jglob.current_playlist['playlist_info']['username']
            password = jglob.current_playlist['playlist_info']['password']
            player_api = str(host) + 'player_api.php?username=' + str(username) + '&password=' + str(password)
            jglob.xmltv_address = str(host) + 'xmltv.php?username=' + str(username) + '&password=' + str(password)

            self.LiveCategoriesUrl = player_api + '&action=get_live_categories'
            self.VodCategoriesUrl = player_api + '&action=get_vod_categories'
            self.SeriesCategoriesUrl = player_api + '&action=get_series_categories'

            self.LiveStreamsUrl = player_api + '&action=get_live_streams'
            self.VodStreamsUrl = player_api + '&action=get_vod_streams'
            self.SeriesUrl = player_api + '&action=get_series'

            jglob.epg_provider = True

        elif self.playlisttype == 'panel':
            username = jglob.current_playlist['playlist_info']['username']
            password = jglob.current_playlist['playlist_info']['password']
            jglob.xmltv_address = str(host) + 'xmltv.php?username=' + str(username) + '&password=' + str(password)
            jglob.epg_provider = True

        else:
            jglob.epg_provider = False

        jglob.old_name = jglob.name
        jglob.categories = []

        if 'bouquet_info' in jglob.current_playlist and jglob.current_playlist['bouquet_info'] != {}:
            jfunc.readbouquetdata()
        else:
            # reset globals
            jglob.live_type = '4097'
            jglob.vod_type = '4097'
            jglob.vod_order = 'original'

            jglob.epg_rytec_uk = False
            jglob.epg_swap_names = False
            jglob.epg_force_rytec_uk = False

            jglob.live = True
            jglob.vod = False
            jglob.series = False
            jglob.prefix_name = True
            jglob.fixepg = False

        if self.playlisttype == 'xtream':
            self.timer = eTimer()
            self.timer.start(self.pause, 1)
            try:
                self.timer_conn = self.timer.timeout.connect(self.downloadEnigma2Data)
            except:
                self.timer.callback.append(self.downloadEnigma2Data)

        elif self.playlisttype == "panel":
            self.timer = eTimer()
            self.timer.start(self.pause, 1)
            try:
                self.timer_conn = self.timer.timeout.connect(self.getPanelData)
            except:
                self.timer.callback.append(self.getPanelData)
        else:
            self.createConfig()
            self.createSetup()

        self.onLayoutFinish.append(self.__layoutFinished)

        if self.setInfo not in self['config'].onSelectionChanged:
            self['config'].onSelectionChanged.append(self.setInfo)


    def __layoutFinished(self):
        self.setTitle(self.setup_title)


    def downloadEnigma2Data(self):
        downloads.downloadlivecategories(self.LiveCategoriesUrl)
        downloads.downloadvodcategories(self.VodCategoriesUrl)
        downloads.downloadseriescategories(self.SeriesCategoriesUrl)
        self.createConfig()
        self.createSetup()


    def getPanelData(self):
        jglob.livecategories = []
        jglob.vodcategories = []
        jglob.seriescategories = []

        valid = False

        # panel type 1
        downloads.getpanellive(jglob.current_playlist)
        downloads.getpanelvod(jglob.current_playlist)
        downloads.getpanelseries(jglob.current_playlist)

        # panel type 2
        if 'categories' in jglob.current_playlist:
            if 'live' in jglob.current_playlist['categories']:
                print("***** panel has categories / live *******")
                jglob.haslive = True
                try:
                    jglob.livecategories = jglob.current_playlist['categories']['live']
                    valid = True
                except:
                    print("\n ***** download live category error *****")
                    jglob.haslive = False

                if valid:

                    if jglob.livecategories == [] or 'user_info' in jglob.livecategories or 'category_id' not in jglob.livecategories[0]:
                        jglob.haslive = False
                        jglob.livecategories == []

                    if jglob.haslive is False or jglob.livecategories == []:
                        jglob.live = False

            valid = False

            if 'movie' in jglob.current_playlist['categories']:
                print("***** panel has categories / movies *******")
                jglob.hasvod = True
                try:
                    jglob.vodcategories = jglob.current_playlist['categories']['movie']
                    valid = True
                except:
                    print("\n ***** download vod category error *****")
                    jglob.hasvod = False

                if valid:
                    if jglob.vodcategories == [] or 'user_info' in jglob.vodcategories or 'category_id' not in jglob.vodcategories[0]:
                        jglob.hasvod = False
                        jglob.vodcategories == []

                    if jglob.hasvod is False or jglob.vodcategories == []:
                        jglob.vod = False

            valid = False

            if 'series' in jglob.current_playlist['categories']:
                print("***** panel has categories / series *******")
                jglob.hasseries = True
                try:
                    jglob.seriescategories = jglob.current_playlist['categories']['series']
                    valid = True
                except:
                    print("\n ***** download series category error *****")
                    jglob.hasseries = False

                if valid:
                    if jglob.seriescategories == [] or 'user_info' in jglob.seriescategories or 'category_id' not in jglob.seriescategories[0]:
                        jglob.hasseries = False
                        jglob.seriescategories == []

                    if jglob.hasseries is False or jglob.seriescategories == []:
                        jglob.series = False

        self.createConfig()
        self.createSetup()


    def createConfig(self):
        self['lab1'].setText('')
        self.NameCfg = NoSave(ConfigText(default=jglob.name, fixed_size=False))

        self.PrefixNameCfg = NoSave(ConfigYesNo(default=jglob.prefix_name))

        self.LiveCategoriesCfg = NoSave(ConfigYesNo(default=jglob.live))
        self.VodCategoriesCfg = NoSave(ConfigYesNo(default=jglob.vod))
        self.SeriesCategoriesCfg = NoSave(ConfigYesNo(default=jglob.series))

        self.XmltvCfg = NoSave(ConfigText(default=jglob.xmltv_address, fixed_size=False))

        self.VodOrderCfg = NoSave(ConfigSelection(default='alphabetical', choices=[('original', _('Original Order')), ('alphabetical', _('A-Z')), ('date', _('Newest First')), ('date2', _('Oldest First'))]))

        self.EpgProviderCfg = NoSave(ConfigEnableDisable(default=jglob.epg_provider))
        self.EpgRytecUKCfg = NoSave(ConfigEnableDisable(default=jglob.epg_rytec_uk))
        self.EpgSwapNamesCfg = NoSave(ConfigEnableDisable(default=jglob.epg_swap_names))
        self.ForceRytecUKCfg = NoSave(ConfigEnableDisable(default=jglob.epg_force_rytec_uk))

        if os.path.isdir('/usr/lib/enigma2/python/Plugins/SystemPlugins/ServiceApp'):
            self.LiveTypeCfg = NoSave(ConfigSelection(default=jglob.live_type, choices=[
                ('1', _('DVB(1)')),
                ('4097', _('IPTV(4097)')),
                ('5001', _('GStreamer(5001)')),
                ('5002', 'ExtPlayer(5002)')]))
            self.VodTypeCfg = NoSave(ConfigSelection(default=jglob.vod_type, choices=[
                ('1', _('DVB(1)')),
                ('4097', _('IPTV(4097)')),
                ('5001', _('GStreamer(5001)')),
                ('5002', 'ExtPlayer(5002)')]))
        else:
            self.LiveTypeCfg = NoSave(ConfigSelection(default=jglob.live_type, choices=[('1', _('DVB(1)')), ('4097', _('IPTV(4097)'))]))
            self.VodTypeCfg = NoSave(ConfigSelection(default=jglob.vod_type, choices=[('1', _('DVB(1)')), ('4097', _('IPTV(4097)'))]))

        self.bufferoption = '0'
        if jglob.livebuffer != '0':
            self.bufferoption = jglob.livebuffer
        if jglob.vodbuffer != '0':
            self.bufferoption = jglob.vodbuffer
        self.BufferCfg = NoSave(ConfigSelection(default=self.bufferoption, choices=[('0', _('No Buffering(0)')), ('1', _('Buffering Enabled(1)')), ('3', _('Progressive Buffering(3)'))]))
        self.FixEPGCfg = NoSave(ConfigEnableDisable(default=jglob.fixepg))


    def createSetup(self):
        self.list = []
        self.list.append(getConfigListEntry(_('Bouquet name'), self.NameCfg))

        self.list.append(getConfigListEntry(_('Use name as bouquet prefix'), self.PrefixNameCfg))

        if self.playlisttype == 'xtream' or self.playlisttype == 'panel':

            if jglob.haslive:
                self.list.append(getConfigListEntry(_('Live categories'), self.LiveCategoriesCfg))

            if self.LiveCategoriesCfg.value is True:
                self.list.append(getConfigListEntry(_('Stream type for Live'), self.LiveTypeCfg))

            if jglob.hasvod:
                self.list.append(getConfigListEntry(_('VOD categories'), self.VodCategoriesCfg))

            if jglob.hasseries:
                self.list.append(getConfigListEntry(_('Series categories'), self.SeriesCategoriesCfg))

            if self.VodCategoriesCfg.value is True or self.SeriesCategoriesCfg.value is True:
                self.list.append(getConfigListEntry(_('Stream type for VOD/SERIES'), self.VodTypeCfg))

            if self.VodCategoriesCfg.value is True:
                self.list.append(getConfigListEntry(_('VOD bouquet order'), self.VodOrderCfg))

            if (self.LiveCategoriesCfg.value is True and self.LiveTypeCfg.value != "1") or (self.VodCategoriesCfg.value is True and self.VodTypeCfg.value != "1"):
                self.list.append(getConfigListEntry(_('Buffer streams'), self.BufferCfg))

            if self.LiveCategoriesCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('Use your provider EPG'), self.EpgProviderCfg))


            if self.LiveCategoriesCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('Use Rytec UK EPG'), self.EpgRytecUKCfg))

            if self.EpgRytecUKCfg.value is True:
                self.list.append(getConfigListEntry(_('Replace UK channel names in bouquets with swap names'), self.EpgSwapNamesCfg))
                self.list.append(getConfigListEntry(_('UK only: Force UK name swap'), self.ForceRytecUKCfg))

            if self.EpgProviderCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('EPG url'), self.XmltvCfg))

            if self.EpgProviderCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('Rebuild XMLTV EPG data'), self.FixEPGCfg))

        else:
            self.list.append(getConfigListEntry(_('Live categories'), self.LiveCategoriesCfg))

            if self.LiveCategoriesCfg.value is True:
                self.list.append(getConfigListEntry(_('Stream type for Live'), self.LiveTypeCfg))

            self.list.append(getConfigListEntry(_('Vod categories'), self.VodCategoriesCfg))

            self.list.append(getConfigListEntry(_('Series categories'), self.SeriesCategoriesCfg))

            if self.VodCategoriesCfg.value is True or self.SeriesCategoriesCfg.value is True:
                self.list.append(getConfigListEntry(_('Stream type for VOD/Series'), self.VodTypeCfg))

            if (self.LiveCategoriesCfg.value is True and self.LiveTypeCfg.value != "1") or (self.VodCategoriesCfg.value is True and self.VodTypeCfg.value != "1"):
                self.list.append(getConfigListEntry(_('Buffer streams'), self.BufferCfg))


            if self.LiveCategoriesCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('Use your provider EPG'), self.EpgProviderCfg))

            if self.EpgProviderCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('EPG url'), self.XmltvCfg))

            if self.EpgProviderCfg.value is True and jglob.has_epg_importer:
                self.list.append(getConfigListEntry(_('Rebuild XMLTV EPG data'), self.FixEPGCfg))

        self['config'].list = self.list
        self['config'].l.setList(self.list)

        self.setInfo()
        self.handleInputHelpers()


    # dreamos workaround for showing setting descriptions
    def setInfo(self):
        entry = str(self.getCurrentEntry())

        if entry == _('Bouquet name'):
            self['information'].setText(_("\nEnter name to be shown as a prefix in your bouquets"))
            return

        if entry == _('Use name as bouquet prefix'):
            self['information'].setText(_("\nUse provider name prefix in your bouquets"))
            return

        if entry == _('Live categories'):
            self['information'].setText(_("\nInclude LIVE categories in your bouquets."))
            return

        if entry == _('Stream type for Live'):
            self['information'].setText(_("\nThis setting allows you to choose which player E2 will use for your live streams.\nIf your live streams do not play try changing this setting."))
            return

        if entry == _('VOD categories'):
            self['information'].setText(_("\nInclude VOD categories in your bouquets."))
            return

        if entry == _('Series categories'):
            self['information'].setText(_("\nInclude SERIES categories in your bouquets. \n** Note: Selecting Series can be slow to populate the lists.**"))
            return

        if entry == _('Stream type for VOD/SERIES'):
            self['information'].setText(_("\nThis setting allows you to choose which player E2 will use for your VOD/Series streams.\nIf your VOD streams do not play try changing this setting."))
            return

        if entry == _('VOD bouquet order'):
            self['information'].setText(_("\nSelect the sort order for your VOD Bouquets."))
            return

        if entry == _('Use your provider EPG'):
            self['information'].setText(_("\nMake provider xmltv for use in EPG Importer.\nProvider source needs to be selected in EPG Importer plugin."))
            return

        if entry == _('EPG url'):
            self['information'].setText(_("Enter the EPG url for your playlist. If unknown leave as default."))
            return

        if entry == _('Use Rytec UK EPG'):
            self['information'].setText(_("\nTry to match the UK Rytec names in the background to populate UK EPG.\nNote this will override your provider's UK EPG."))
            return

        if entry == _('Replace UK channel names in bouquets with swap names'):
            self['information'].setText(_("\nThis will amend the UK channels names in channel bouquets to that of the computed swap names."))
            return

        if entry == _('UK only: Force UK name swap'):
            self['information'].setText(_("Use for UK providers that do not specify UK in the category title or channel title.\nMay cause non UK channels to have the wrong epg.\nTrying creating bouquets without this option turned off first."))

        if entry == _('Buffer streams'):
            self['information'].setText(_("\nSet stream buffer (Experimental)."))

        if entry == _('Rebuild XMLTV EPG data'):
            self['information'].setText(_("\n(Optional) Download and attempt to rebuild XMLTV EPG data to UTF-8 encoding (Slower).\nOnly required if you think you have corrupt external EPG."))
            return


    def changedEntry(self):
        try:
            if isinstance(self['config'].getCurrent()[1], (ConfigBoolean, ConfigSelection)):
                self.createSetup()
        except:
            pass
	ConfigListScreen.changedEntry(self)


    def save(self):
        jglob.name = self.NameCfg.value
        if jglob.old_name != jglob.name:
            if jglob.name.strip() == '' or jglob.name.strip() is None:
                self.session.open(MessageBox, _('Bouquet name cannot be blank. Please enter a unique bouquet name. Minimum 2 characters.'), MessageBox.TYPE_ERROR, timeout=10)
                self.createSetup()
                return

        for x in self['config'].list:
            x[1].save()

        self['config'].instance.moveSelectionTo(1)

        jglob.finished = False
        jglob.name = self.NameCfg.value
        jglob.prefix_name = self.PrefixNameCfg.value
        jglob.live = self.LiveCategoriesCfg.value
        jglob.live_type = self.LiveTypeCfg.value
        jglob.vod = self.VodCategoriesCfg.value
        jglob.series = self.SeriesCategoriesCfg.value
        jglob.vod_type = self.VodTypeCfg.value
        jglob.vod_order = self.VodOrderCfg.value
        jglob.epg_provider = self.EpgProviderCfg.value
        jglob.epg_rytec_uk = self.EpgRytecUKCfg.value
        jglob.epg_swap_names = self.EpgSwapNamesCfg.value
        jglob.epg_force_rytec_uk = self.ForceRytecUKCfg.value

        if self.LiveTypeCfg.value != "1":
            jglob.livebuffer = self.BufferCfg.value

        if self.VodTypeCfg.value != "1":
            jglob.vodbuffer = self.BufferCfg.value

        jglob.xmltv_address = self.XmltvCfg.value

        jglob.fixepg = self.FixEPGCfg.value

        self.session.openWithCallback(self.finishedCheck, JediMakerXtream_ChooseBouquets)

    def cancel(self):
        self.close()


    def finishedCheck(self):
        self.createSetup()
        if jglob.finished:
            self.close()



class JediMakerXtream_ChooseBouquets(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin = skin_path + 'jmx_bouquets.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()

        self.setup_title = _('Choose Bouquets')

        self.startList = []
        self.drawList = []

        self.pause = 100

        self['list'] = List(self.drawList)

        self['key_red'] = StaticText('')
        self['key_green'] = StaticText('')
        self['key_yellow'] = StaticText('')
        self['key_blue'] = StaticText('')
        self['key_info'] = StaticText('')
        self['description'] = Label('')
        self['lab1'] = Label(_('Loading data... Please wait...'))

        self['setupActions'] = ActionMap(['ColorActions', 'SetupActions', 'ChannelSelectEPGActions'], {
            'red': self.keyCancel,
            'green': self.keyGreen,
            'yellow': self.toggleAllSelection,
            'blue': self.clearAllSelection,
            'save': self.keyGreen,
            'cancel': self.keyCancel,
            'ok': self.toggleSelection,
            'info': self.viewChannels,
            'showEPGList': self.viewChannels
        }, -2)

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Create'))
        self['key_yellow'] = StaticText(_('Invert'))
        self['key_blue'] = StaticText(_('Clear All'))
        self['key_info'] = StaticText(_('Show Channels'))
        self['description'] = Label(_('Select the playlist categories you wish to create bouquets for.\nPress OK to invert the selection.\nPress INFO to show the channels in this category.'))

        self['list'].onSelectionChanged.append(self.getCurrentEntry)

        self.cat_list = ''
        self.currentSelection = 0
        self.playlisttype = jglob.current_playlist['playlist_info']['playlisttype']

        if self.playlisttype == 'xtream':
            protocol = jglob.current_playlist['playlist_info']['protocol']
            domain = jglob.current_playlist['playlist_info']['domain']
            port = str(jglob.current_playlist['playlist_info']['port'])
            host = str(protocol) + str(domain) + ':' + str(port) + '/'
            username = jglob.current_playlist['playlist_info']['username']
            password = jglob.current_playlist['playlist_info']['password']
            player_api = str(host) + 'player_api.php?username=' + str(username) + '&password=' + str(password)

            self.LiveCategoriesUrl = player_api + '&action=get_live_categories'
            self.VodCategoriesUrl = player_api + '&action=get_vod_categories'
            self.SeriesCategoriesUrl = player_api + '&action=get_series_categories'

            self.LiveStreamsUrl = player_api + '&action=get_live_streams'
            self.VodStreamsUrl = player_api + '&action=get_vod_streams'
            self.SeriesUrl = player_api + '&action=get_series'

            if jglob.live or jglob.vod or jglob.series:
                if jglob.live:
                    self['lab1'].setText('Downloading Live data')

                    self.timer1 = eTimer()
                    self.timer1.start(self.pause, 1)
                    try:
                        self.timer1_conn = self.timer1.timeout.connect(self.downloadLive)
                    except:
                        self.timer1.callback.append(self.downloadLive)

                if jglob.vod:
                    self['lab1'].setText('Downloading VOD data')

                    self.timer2 = eTimer()
                    self.timer2.start(self.pause, 1)
                    try:
                        self.timer2_conn = self.timer2.timeout.connect(self.downloadVod)
                    except:
                        self.timer2.callback.append(self.downloadVod)

                if jglob.series:
                    self['lab1'].setText('Downloading Series data')

                    self.timer3 = eTimer()
                    self.timer3.start(self.pause, 1)
                    try:
                        self.timer3_conn = self.timer3.timeout.connect(self.downloadSeries)
                    except:
                        self.timer3.callback.append(self.downloadSeries)
            else:
                self.close()

        elif self.playlisttype == 'panel':
            protocol = jglob.current_playlist['playlist_info']['protocol']
            domain = jglob.current_playlist['playlist_info']['domain']
            port = str(jglob.current_playlist['playlist_info']['port'])
            host = str(protocol) + str(domain) + ':' + str(port) + '/'
            username = jglob.current_playlist['playlist_info']['username']
            password = jglob.current_playlist['playlist_info']['password']
            self['lab1'].setText('Getting categories')
            self.timer = eTimer()
            self.timer.start(self.pause, 1)

            try:
                self.timer_conn = self.timer.timeout.connect(self.getcategories)
            except:
                self.timer.callback.append(self.getcategories)

        else:
            jglob.live = True
            jglob.vod = True
            self.onFirstExecBegin.append(self.m3uStart)
        self.onLayoutFinish.append(self.__layoutFinished)


    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.getCurrentEntry()


    def nextjob(self, actiontext, function):
        self['lab1'].setText(actiontext)
        self.timer = eTimer()
        self.timer.start(self.pause, 1)
        try:
            self.timer_conn = self.timer.timeout.connect(function)
        except:
            self.timer.callback.append(function)


    def downloadLive(self):
        downloads.downloadlivestreams(self.LiveStreamsUrl)

        if jglob.vod:
            self.nextjob(_('Downloading VOD data'), self.downloadVod)
        elif jglob.series:
            self.nextjob(_('Downloading Series data'), self.downloadSeries)
        else:
            self.nextjob(_('Getting categories'), self.getcategories)


    def downloadVod(self):
        downloads.downloadvodstreams(self.VodStreamsUrl)

        if jglob.series:
            self.nextjob(_('Downloading Series data'), self.downloadSeries)
        else:
            self.nextjob(_('Getting categories'), self.getcategories)


    def downloadSeries(self):
        downloads.downloadseriesstreams(self.SeriesUrl)
        self.nextjob(_('Getting categories'), self.getcategories)


    def getcategories(self):
        jglob.categories = []

        if self.playlisttype == 'panel':
            jglob.livecategories = []
            jglob.vodcategories = []
            jglob.seriescategories = []
            if jglob.live:
                downloads.getpanellive(jglob.current_playlist)
            if jglob.vod:
                downloads.getpanelvod(jglob.current_playlist)
            if jglob.series:
                downloads.getpanelseries(jglob.current_playlist)
        jfunc.getcategories()
        self.nextjob(_('Getting selection list'), self.ignorelist)


    def ignorelist(self):
        # Only select previously selected categories or new categories
        if 'bouquet_info' in jglob.current_playlist and jglob.current_playlist['bouquet_info'] != {}:
            jfunc.IgnoredCategories()

        self.timer = eTimer()
        self.timer.start(self.pause, 1)
        try:
            self.timer_conn = self.timer.timeout.connect(self.getStartList)
        except:
            self.timer.callback.append(self.getStartList)


    def buildListEntry(self, name, streamtype, index, enabled):
        if enabled:
            pixmap = LoadPixmap(cached=True, path=skin_path + "images/lock_on.png")
        else:
            pixmap = LoadPixmap(cached=True, path=skin_path + "images/lock_off.png")

        return(pixmap, str(name), str(streamtype), index, enabled)


    def getStartList(self):
        self['lab1'].setText('')
        self.drawList = [self.buildListEntry(x[0], x[1], x[2], x[3]) for x in jglob.categories]
        self.refresh()


    def refresh(self):
        self.drawList = []
        self.drawList = [self.buildListEntry(x[0], x[1], x[2], x[3]) for x in jglob.categories]
        self['list'].updateList(self.drawList)


    def toggleSelection(self):
        if len(self['list'].list) > 0:
            idx = self['list'].getIndex()
            jglob.categories[idx][3] = not jglob.categories[idx][3]
            self.refresh()


    def toggleAllSelection(self):
        for idx, item in enumerate(self['list'].list):
            jglob.categories[idx][3] = not jglob.categories[idx][3]
        self.refresh()


    def getSelectionsList(self):
        return [(item[0], item[1], item[2], item[3]) for item in jglob.categories if item[3]]


    def getUnSelectedList(self):
        return [(item[0], item[1], item[2], item[3]) for item in jglob.categories if item[3] is False]


    def clearAllSelection(self):
        for idx, item in enumerate(self['list'].list):
            jglob.categories[idx][3] = False
        self.refresh()


    def getCurrentEntry(self):
        self.currentSelection = self['list'].getIndex()


    def viewChannels(self):
        from . import viewchannel
        try:
            self.session.open(viewchannel.JediMakerXtream_ViewChannels, jglob.categories[self.currentSelection])
        except:
            return


    def m3uStart(self):
        downloads.getM3uCategories(jglob.live, jglob.vod)
        self.makeBouquetData()
        self.session.open(buildbouquet.JediMakerXtream_BuildBouquets)
        self.close()


    def keyCancel(self):
        self.close()


    def keyGreen(self):
        selectedCategories = self.getSelectionsList()
        for selected in selectedCategories:
            if selected[1] == 'Live':
                jglob.live = True
                continue
            elif selected[1] == 'VOD':
                jglob.vod = True
                continue
            elif selected[1] == 'Series':
                jglob.series = True
                continue
            if jglob.live and jglob.vod and jglob.series:
                break

        self.makeBouquetData()
        self.session.openWithCallback(self.close, buildbouquet.JediMakerXtream_BuildBouquets)


    def makeBouquetData(self):
        jglob.current_playlist['bouquet_info'] = {}
        jglob.current_playlist['bouquet_info'] = OrderedDict([
            ('bouquet_id', jglob.bouquet_id),
            ('name', jglob.name),
            ('oldname', jglob.old_name),
            ('live_type', jglob.live_type),
            ('vod_type', jglob.vod_type),
            ('selected_live_categories', []),
            ('selected_vod_categories', []),
            ('selected_series_categories', []),
            ('ignored_live_categories', []),
            ('ignored_vod_categories', []),
            ('ignored_series_categories', []),
            ('live_update', '---'),
            ('vod_update', '---'),
            ('series_update', '---'),
            ('xmltv_address', jglob.xmltv_address),
            ('vod_order', jglob.vod_order),
            ('epg_provider', jglob.epg_provider),
            ('epg_rytec_uk', jglob.epg_rytec_uk),
            ('epg_swap_names', jglob.epg_swap_names),
            ('epg_force_rytec_uk', jglob.epg_force_rytec_uk),
            ('prefix_name', jglob.prefix_name),
            ('buffer_live', jglob.livebuffer),
            ('buffer_vod', jglob.vodbuffer),
            ('fixepg', jglob.fixepg)
        ])

        if jglob.live:
            jglob.current_playlist['bouquet_info']['live_update'] = datetime.now().strftime('%x  %X')

        if jglob.vod:
            jglob.current_playlist['bouquet_info']['vod_update'] = datetime.now().strftime('%x  %X')

        if jglob.series:
            jglob.current_playlist['bouquet_info']['series_update'] = datetime.now().strftime('%x  %X')


        if self.playlisttype == 'xtream' or self.playlisttype == 'panel':
            jglob.selectedcategories = self.getSelectionsList()

            for category in jglob.selectedcategories:
                if category[1] == 'Live':
                    jglob.current_playlist['bouquet_info']['selected_live_categories'].append(category[0])
                elif category[1] == 'Series':
                    jglob.current_playlist['bouquet_info']['selected_series_categories'].append(category[0])
                elif category[1] == 'VOD':
                    jglob.current_playlist['bouquet_info']['selected_vod_categories'].append(category[0])

            jglob.ignoredcategories = self.getUnSelectedList()

            for category in jglob.ignoredcategories:
                if category[1] == 'Live':
                    jglob.current_playlist['bouquet_info']['ignored_live_categories'].append(category[0])
                elif category[1] == 'Series':
                    jglob.current_playlist['bouquet_info']['ignored_series_categories'].append(category[0])
                elif category[1] == 'VOD':
                    jglob.current_playlist['bouquet_info']['ignored_vod_categories'].append(category[0])

        else:
            for category in jglob.getm3ustreams:
                if category[4] == 'live' and category[0] not in jglob.current_playlist['bouquet_info']['selected_live_categories']:
                    jglob.current_playlist['bouquet_info']['selected_live_categories'].append(category[0])
                elif category[4] == 'vod' and category[0] not in jglob.current_playlist['bouquet_info']['selected_vod_categories']:
                    jglob.current_playlist['bouquet_info']['selected_vod_categories'].append(category[0])

        self.playlists_all = jfunc.getPlaylistJson()

        for playlist in self.playlists_all:
            if playlist['playlist_info']['index'] == jglob.current_playlist['playlist_info']['index']:
                playlist['bouquet_info'] = jglob.current_playlist['bouquet_info']

                break

        with open(playlist_file, 'w') as f:
            json.dump(self.playlists_all, f)
