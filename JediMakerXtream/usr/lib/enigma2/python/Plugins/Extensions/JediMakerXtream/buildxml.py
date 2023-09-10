#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import downloads
from . import globalfunctions as jfunc
from . import jedi_globals as glob

from .plugin import cfg
try:
    from xml.dom import minidom
except:
    pass

import os
import re
import sys
import xml.etree.cElementTree as ET

sys.setrecursionlimit(2000)


def categoryBouquetXml(streamtype, bouquetTitle, bouquetString):
    cleanTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", bouquetTitle)
    cleanTitle = re.sub(r" ", "_", cleanTitle)
    cleanTitle = re.sub(r"_+", "_", cleanTitle)
    filepath = "/etc/enigma2/"

    if cfg.groups.value is True:
        cleanGroup = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", glob.name)
        cleanGroup = re.sub(r" ", "_", cleanGroup)
        cleanGroup = re.sub(r"_+", "_", cleanGroup)
        filename = "subbouquet.jedimakerxtream_" + str(streamtype) + "_" + str(cleanTitle) + ".tv"
    else:
        filename = "userbouquet.jedimakerxtream_" + str(streamtype) + "_" + str(cleanTitle) + ".tv"
    fullpath = os.path.join(filepath, filename)

    with open(fullpath, "w+") as f:
        f.write(bouquetString)


def bouquetsTvXml(streamtype, bouquetTitle):
    cleanTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", bouquetTitle)
    cleanTitle = re.sub(r" ", "_", cleanTitle)
    cleanTitle = re.sub(r"_+", "_", cleanTitle)

    if cfg.groups.value is True:
        cleanGroup = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", glob.name)
        cleanGroup = re.sub(r" ", "_", cleanGroup)
        cleanGroup = re.sub(r"_+", "_", cleanGroup)

        groupname = "userbouquet.jedimakerxtream_" + str(cleanGroup) + ".tv"

        with open("/etc/enigma2/bouquets.tv", "r") as f:
            content = f.read()

        with open("/etc/enigma2/bouquets.tv", "a+") as f:
            bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + str(groupname) + '" ORDER BY bouquet\n'
            if str(bouquetTvString) not in content:
                f.write(str(bouquetTvString))

        filename = "/etc/enigma2/" + str(groupname)

        with open(filename, "a+") as f:
            nameString = "#NAME " + str(glob.name) + "\n"
            f.write(str(nameString))

            filename = "subbouquet.jedimakerxtream_" + str(streamtype) + "_" + str(cleanTitle) + ".tv"
            bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + str(filename) + '" ORDER BY bouquet\n'
            f.write(str(bouquetTvString))

    else:
        filename = "userbouquet.jedimakerxtream_" + str(streamtype) + "_" + str(cleanTitle) + ".tv"

        with open("/etc/enigma2/bouquets.tv", "a+") as f:
            bouquetTvString = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "' + str(filename) + '" ORDER BY bouquet\n'
            f.write(str(bouquetTvString))


def buildXMLTVSourceFile():
    safeName = re.sub(r'[\<\>\:\"\/\\\|\?\* ]', "_", str(glob.name))
    safeName = re.sub(r" ", "_", safeName)
    safeName = re.sub(r"_+", "_", safeName)

    filepath = "/etc/epgimport/"
    epgfilename = "jedimakerxtream." + str(safeName) + ".channels.xml"
    channelpath = os.path.join(filepath, epgfilename)

    # buildXMLTVSourceFile

    sourcefile = "/etc/epgimport/jedimakerxtream.sources.xml"
    if not os.path.isfile(sourcefile) or os.stat(sourcefile).st_size == 0:
        with open(sourcefile, "w") as f:
            xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
            xml_str += '<sources>\n'
            xml_str += '<sourcecat sourcecatname="JediMakerXtream EPG">\n'
            xml_str += '</sourcecat>\n'
            xml_str += '</sources>\n'
            f.write(xml_str)

    import xml.etree.ElementTree as ET

    tree = ET.parse(sourcefile)
    root = tree.getroot()
    sourcecat = root.find("sourcecat")

    exists = False

    for sourceitem in sourcecat:
        if channelpath in sourceitem.attrib["channels"]:
            exists = True
            break

    if exists is False:
        import datetime
        if sys.version_info.major == 3:
			if 'user_info' in glob.current_playlist and 'timezone' in glob.current_playlist['user_info']:
				import zoneinfo
				offset = int(datetime.datetime.now(zoneinfo.ZoneInfo(glob.current_playlist['user_info']['timezone'])).strftime('%z')) * -1
			else:
				offset = 0
        else:
			if 'server_info' in glob.current_playlist and 'time_now' in glob.current_playlist['server_info']:
				import time
				server_datestamp = datetime.datetime.strptime(str(glob.current_playlist['server_info']['time_now']), "%Y-%m-%d %H:%M:%S")
				utc_datestamp = datetime.datetime.utcfromtimestamp(time.time())
				offset = utc_datestamp - server_datestamp
				if offset.days == -1:
					offset = (86400 - offset.seconds) / -3600
				else:
					offset = offset.seconds / 3600
			else:
				offset = 0
        offset = '%+05d' % (offset * 100)
        source = ET.SubElement(sourcecat, "source", type="gen_xmltv", nocheck="1", offset=offset, channels=channelpath)
        description = ET.SubElement(source, "description")
        description.text = str(safeName)

        url = ET.SubElement(source, "url")
        url.text = str(glob.xmltv_address)

        tree.write(sourcefile)

    try:
        with open(sourcefile, "r+") as f:
            xml_str = f.read()
            f.seek(0)
            doc = minidom.parseString(xml_str)
            xml_output = doc.toprettyxml(encoding="utf-8", indent="\t")
            try:
                xml_output = os.linesep.join([s for s in xml_output.splitlines() if s.strip()])
            except:
                xml_output = os.linesep.join([s for s in xml_output.decode().splitlines() if s.strip()])
            f.write(xml_output)
    except Exception as e:
        print(e)


def buildXMLTVChannelFile(epg_name_list):
    safeName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", str(glob.name))
    safeName = re.sub(r" ", "_", safeName)
    safeName = re.sub(r"_+", "_", safeName)

    safeNameOld = re.sub(r'[\<\>\:\"\/\\\|\?\* ]', "_", str(glob.old_name))
    safeNameOld = re.sub(r" ", "_", safeNameOld)
    safeNameOld = re.sub(r"_+", "_", safeNameOld)

    # remove old files
    jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeName) + ".channels.xml")
    jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeNameOld) + ".channels.xml")

    filepath = "/etc/epgimport/"
    epgfilename = "jedimakerxtream." + str(safeName) + ".channels.xml"
    channelpath = os.path.join(filepath, epgfilename)

    # if xmltv file doesn't already exist, create file and build.
    if not os.path.isfile(channelpath):
        with open(channelpath, "a") as f:
            f.close()

    # buildXMLTVChannelFile

    with open(channelpath, "w") as f:
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += '<channels>\n'

        for i in range(len(epg_name_list)):
            channelid = epg_name_list[i][0]
            if channelid and "&" in channelid:
                channelid = channelid.replace("&", "&amp;")

            serviceref = epg_name_list[i][1]
            name = epg_name_list[i][2]

            if channelid and channelid != "None":
                xml_str += '\t<channel id="' + str(channelid) + '">' + str(serviceref) + '</channel><!-- ' + str(name) + ' -->\n'

        xml_str += '</channels>\n'

        f.write(xml_str)


def downloadXMLTV():

    safeName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", str(glob.name))
    safeName = re.sub(r" ", "_", safeName)
    safeName = re.sub(r"_+", "_", safeName)

    safeNameOld = re.sub(r'[\<\>\:\"\/\\\|\?\* ]', "_", str(glob.old_name))
    safeNameOld = re.sub(r" ", "_", safeNameOld)
    safeNameOld = re.sub(r"_+", "_", safeNameOld)

    jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeName) + ".xmltv.xml")
    jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeNameOld) + ".xmltv.xml")
    jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeName) + ".xmltv2.xml")
    jfunc.purge("/etc/epgimport", "jedimakerxtream." + str(safeNameOld) + ".xmltv2.xml")

    filepath = "/etc/epgimport/"
    epgfilename = "jedimakerxtream." + str(safeName) + ".xmltv.xml"
    epgpath = os.path.join(filepath, epgfilename)
    response = downloads.checkGZIP(glob.xmltv_address)

    if response is not None:

        with open(epgpath, "w") as f:
            f.write(response)

        with open(epgpath, "r") as f:
            # tree = ET.parse(f)
            tree = ET.parse(f, parser=ET.XMLParser(encoding="utf-8"))

        tree.write("/etc/epgimport/" + "jedimakerxtream." + str(safeName) + ".xmltv2.xml", encoding="utf-8", xml_declaration=True)
