#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import jedi_globals as glob
from .plugin import cfg, hdr, rytec_url, rytec_file, sat28_file, alias_file

from io import StringIO

import gzip
import json
import os
import re
import socket
import sys

pythonVer = 2
if sys.version_info.major == 3:
    pythonVer = 3

if pythonVer == 3:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
else:
    from urllib2 import urlopen, Request, URLError


def checkGZIP(url):
    response = None

    request = Request(url, headers=hdr)

    try:
        response = urlopen(request, timeout=20)

        if response.info().get("Content-Encoding") == "gzip":
            buffer = StringIO(response.read())
            deflatedContent = gzip.GzipFile(fileobj=buffer)
            if pythonVer == 3:
                return deflatedContent.read().decode("utf-8")
            else:
                return deflatedContent.read()
        else:
            if pythonVer == 3:
                return response.read().decode("utf-8")
            else:
                return response.read()
    except Exception as e:
        print(e)
        return None


def downloadlivecategories(url):
    glob.livecategories = []
    valid = False
    response = checkGZIP(url)

    # try a second time if first attempt failed.
    if response is None:
        response = checkGZIP(url)

    if response is not None and "category_id" in response:
        glob.haslive = True
        try:
            glob.livecategories = json.loads(response)
            valid = True

        except:
            print("\n ***** download live category error *****")
            glob.haslive = False
            pass

        if valid:
            if glob.livecategories == [] or "user_info" in glob.livecategories or "category_id" not in glob.livecategories[0]:
                glob.haslive = False
                glob.livecategories == []

            if not glob.haslive or glob.livecategories == []:
                glob.live = False


def downloadvodcategories(url):
    glob.vodcategories = []
    valid = False
    response = checkGZIP(url)

    # try a second time if first attempt failed.
    if response is None:
        response = checkGZIP(url)

    if response is not None and "category_id" in response:
        glob.hasvod = True
        try:
            glob.vodcategories = json.loads(response)
            valid = True

        except:
            print("\n ***** download vod category error *****")
            glob.hasvod = False
            pass

        if valid:
            if glob.vodcategories == [] or "user_info" in glob.vodcategories or "category_id" not in glob.vodcategories[0]:
                glob.hasvod = False
                glob.vodcategories == []

            if not glob.hasvod or glob.vodcategories == []:
                glob.vod = False


def downloadseriescategories(url):
    glob.seriescategories = []
    valid = False
    response = checkGZIP(url)

    # try a second time if first attempt failed.
    if response is None:
        response = checkGZIP(url)

    if response is not None and "category_id" in response:

        glob.hasseries = True
        try:
            glob.seriescategories = json.loads(response)
            valid = True

        except:
            print("\n ***** download series category error *****")
            glob.hasseries = False
            pass

        if valid:
            if glob.seriescategories == [] or "user_info" in glob.seriescategories or "category_id" not in glob.seriescategories[0]:
                glob.hasseries = False
                glob.seriescategories == []

            if not glob.hasseries or glob.seriescategories == []:
                glob.series = False


def downloadlivestreams(url):
    glob.livestreams = []
    valid = False
    response = checkGZIP(url)

    # try a second time if first attempt failed.
    if response is None:
        response = checkGZIP(url)

    if response is not None and "category_id" in response:
        glob.haslive = True

        try:
            glob.livestreams = json.loads(response)
            valid = True

        except:
            print("\n ***** download live streams error *****")
            glob.haslive = False
            pass

    if valid:
        if glob.livestreams == [] or "user_info" in glob.livestreams or "category_id" not in glob.livestreams[0]:
            glob.haslive = False
            glob.livestreams = []

        if glob.haslive is False:
            glob.live = False


def downloadvodstreams(url):
    glob.vodstreams = []
    valid = False
    response = checkGZIP(url)

    # try a second time if first attempt failed.
    if response is None:
        response = checkGZIP(url)

    if response is not None and "category_id" in response:
        glob.hasvod = True

        try:
            glob.vodstreams = json.loads(response)
            valid = True

        except:
            print("\n ***** download vod streams error *****")
            glob.hasvod = False
            pass

    if valid:
        if glob.vodstreams == [] or "user_info" in glob.vodstreams or "category_id" not in glob.vodstreams[0]:
            glob.hasvod = False
            glob.vodstreams = []

        if glob.hasvod is False:
            glob.vod = False


def downloadseriesstreams(url):
    glob.seriesstreams = []
    valid = False
    response = checkGZIP(url)

    # try a second time if first attempt failed.
    if response is None:
        response = checkGZIP(url)

    if response is not None and "category_id" in response:
        glob.hasseries = True

        try:
            glob.seriesstreams = json.loads(response)
            valid = True
        except:
            print("\n ***** download series streams error *****")
            glob.hasseries = False
            pass

    if valid:
        if glob.seriesstreams == [] or "user_info" in glob.seriesstreams or "category_id" not in glob.seriesstreams[0]:
            glob.hasseries = False
            glob.seriersstreams = []

        if glob.hasseries is False:
            glob.series = False


def getM3uCategories(live, vod):
    # print("**** getM3uCategories ***")
    lines = []
    channelnum = 0
    glob.getm3ustreams = []
    group_title = "Uncategorised"
    epg_name = ""
    name = ""
    source = ""

    address = glob.current_playlist["playlist_info"]["address"]

    if glob.current_playlist["playlist_info"]["playlisttype"] == "external":

        req = Request(address, headers=hdr)
        try:
            response = urlopen(req, timeout=int(cfg.timeout.value))
            lines = response.read().splitlines(True)
        except URLError as e:
            print(e)
            pass

        except socket.timeout as e:
            print(e)
            pass

        except socket.error as e:
            print(e)
            pass

        except:
            print("\n ***** getM3uCategories unknown error")
            pass

    elif glob.current_playlist["playlist_info"]["playlisttype"] == "local":
        with open(cfg.m3ulocation.value + address) as f:
            lines = f.readlines()

    for line in lines:

        if pythonVer == 3 and glob.current_playlist["playlist_info"]["playlisttype"] == "external":
            line = line.decode("utf-8")

        if not line.startswith("#EXTINF") and not line.startswith("http"):
            continue

        if line.startswith("#EXTINF"):

            if re.search('group-title=\"(.*?)\"', line) is not None:
                group_title = re.search('group-title=\"(.*?)\"', line).group(1)
            else:
                group_title = ""

            if re.search("(?<=,).*$", line) is not None:
                name = re.search("(?<=,).*$", line).group().strip()

            elif re.search('tvg-name=\"(.*?)\"', line) is not None:
                name = re.search('tvg-name=\"(.*?)\"', line).group(1).strip()

            else:
                name = ""

            if name == "":
                channelnum += 1
                name = "Channel " + str(channelnum)

        elif line.startswith("http"):
            source = line.strip()

            stream = "unknown"

            if source.endswith(".ts") or source.endswith(".m3u8") or "/live" in source or "/m3u8" in source or "deviceUser" in source or "deviceMac" in source or (source[-1].isdigit()):
                stream = "live"

            if source.endswith(".mp4") or source.endswith(".mp3") or source.endswith(".mkv"):
                stream = "vod"

            if stream == "live":
                if live:
                    if group_title == "":
                        group_title = "Uncategorised Live"
                    glob.getm3ustreams.append([group_title, epg_name, name, source, "live"])

            elif stream == "vod":
                if vod:
                    if group_title == "":
                        group_title = "Uncategorised VOD"
                    glob.getm3ustreams.append([group_title, epg_name, name, source, "vod"])
            else:
                if group_title == "":
                    group_title = "Uncategorised"
                glob.getm3ustreams.append([group_title, epg_name, name, source, "live"])


def downloadrytec():
    haslzma = False
    try:
        import lzma
        print("\nlzma success")
        haslzma = True

    except ImportError:
        try:
            from backports import lzma
            print("\nbackports lzma success")
            haslzma = True

        except ImportError:
            print("\nlzma failed")
            pass

        except:
            print("\n ***** downloadrytec lzma unknown error")
            pass

    req = Request(rytec_url, headers=hdr)
    try:
        response = urlopen(req)
        with open(rytec_file, "wb") as output:
            output.write(response.read())

    except URLError as e:
        print(e)
        pass

    except socket.timeout as e:
        print(e)
        pass

    except socket.error as e:
        print(e)
        pass

    except:
        print("\n ***** downloadrytec download unknown error")
        pass

    if os.path.isfile(rytec_file) and os.stat(rytec_file).st_size > 0 and haslzma:
        with lzma.open(rytec_file, "rt", encoding="UTF-8") as fd:
            with open(sat28_file, "w") as outfile:
                for line in fd:
                    if "<!-- 28.2E -->" in line and "0000FFFF" not in line:
                        glob.rytecnames.append(line)
                    # get all 28.2e but ignore bad epg importer refs
                    if "28.2E" in line and "1:0:1:C7A7:817:2:11A0000:0:0:0:" not in line and "1:0:1:2EEF:7EF:2:11A0000:0:0:0:" not in line:
                        outfile.write(line)

        ###################################################################################################
        # read rytec 28.2e file

        with open(sat28_file, "r") as outfile:
            rytec_sat28 = outfile.readlines()
        rytec_ref = {}

        for line in rytec_sat28:

            serviceref = ""
            epg_channel_id = ""
            channelname = ""

            if re.search(r"(?<=<\/channel><!-- ).*(?= --)", line) is not None:
                channelname = re.search(r"(?<=<\/channel><!-- ).*(?= --)", line).group()

            if re.search(r'(?<=\">1).*(?=<\/)', line) is not None:
                serviceref = re.search(r'(?<=\">1).*(?=<\/)', line).group()

            if re.search(r'(?<=id=\")[a-zA-Z0-9\.]+', line) is not None:
                epg_channel_id = re.search(r'(?<=id=\")[a-zA-Z0-9\.]+', line).group()

            rytec_ref[channelname.lower()] = [serviceref, epg_channel_id, channelname]

        ###################################################################################################
        # read iptv name file

        epg_alias_names = []

        if os.path.isfile(alias_file) and os.stat(alias_file).st_size > 0:
            with open(alias_file) as f:
                try:
                    epg_alias_names = json.load(f)
                except ValueError as e:
                    print(("%s\n******** broken alias.txt file ***********" % e))
                    print("\n******** check alias.txt file with https://jsonlint.com ********")

        ###################################################################################################

        return rytec_ref, epg_alias_names
    else:
        return {}, [], {}


def downloadgetfile(url):
    response = checkGZIP(url)

    channelnum = 0
    m3uValues = {}
    series_group_title = "Uncategorised"
    series_name = ""

    if response is not None:
        for line in response.splitlines():

            if not line.startswith("#EXTINF") and not line.startswith("http"):
                continue

            if line.startswith("#EXTINF"):

                if re.search('group-title=\"(.*?)\"', line) is not None:
                    series_group_title = re.search('group-title=\"(.*?)\"', line).group(1)
                else:
                    series_group_title = "Uncategorised"

                if re.search('tvg-name=\"(.*?)\"', line) is not None:
                    series_name = re.search('tvg-name=\"(.*?)\"', line).group(1).strip()

                elif re.search('(?<=",).*$', line) is not None:
                    series_name = re.search('(?<=",).*$', line).group().strip()

                else:
                    series_name = ""

                if series_name == "":
                    channelnum += 1
                    series_name = "Channel " + str(channelnum)

            elif line.startswith("http"):
                series_url = line.strip()

                if "/series/" in series_url:
                    if series_group_title not in m3uValues:
                        m3uValues[series_group_title] = [{"name": series_name, "url": series_url}]
                    else:
                        m3uValues[series_group_title].append({"name": series_name, "url": series_url})

                else:
                    continue
    return m3uValues
