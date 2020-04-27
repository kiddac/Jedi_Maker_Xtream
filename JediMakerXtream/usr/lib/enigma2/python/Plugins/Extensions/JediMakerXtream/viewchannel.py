#!/usr/bin/python
# -*- coding: utf-8 -*-

# for localized messages  	 
from . import _

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from plugin import skin_path
import jediglobals as jglob


class JediMakerXtream_ViewChannels(Screen):
	
	def __init__(self, session, current):
		Screen.__init__(self, session)
		self.session = session
		
		skin = skin_path + 'jmx_channels.xml'
		with open(skin, 'r') as f:
			self.skin = f.read()
			
		self.list = []
		self['viewlist'] = List(self.list)
 
		self.setup_title = _('Channel List')
		
		self.current = current
		
		self['actions'] = ActionMap(['ColorActions', 'OkCancelActions', 'MenuActions'], {
		 'ok': self.quit,
		 'cancel': self.quit,
		 'red': self.quit,
		 'menu': self.quit}, -2)
		 
		self['key_red'] = StaticText(_('Close'))
		
		self.getchannels()
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		self.setTitle(self.setup_title)


	def quit(self):
		self.close()


	def getchannels(self):
		self.list = []
		if self.current[1] == 'Live':
			for channel in jglob.livestreams:
				if str(channel['category_id']) == str(self.current[2]):
					name = str(channel['name'])
					self.list.append((name,'test'))
					
		elif self.current[1] == 'VOD':
			for channel in jglob.vodstreams:
				if str(channel['category_id']) == str(self.current[2]):
					name = str(channel['name'])
					self.list.append((name,'test'))
					
		elif self.current[1] == 'Series':
			for channel in jglob.seriesstreams:
				if str(channel['category_id']) == str(self.current[2]):
					name = str(channel['name'])
					self.list.append((name,'test'))
					
		self.list.sort()

		self['viewlist'].list = self.list
		self['viewlist'].setList(self.list)
