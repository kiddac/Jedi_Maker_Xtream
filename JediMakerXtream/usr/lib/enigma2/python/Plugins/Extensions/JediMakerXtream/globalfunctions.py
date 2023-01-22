#!/usr/bin/python
# -*- coding: utf-8 -*-


from . import jedi_globals as glob

from .plugin import cfg, playlists_json

from collections import OrderedDict
from Components.config import configfile
from enigma import eDVBDB

import json
import os
import re


def getPlaylistJson():
    playlists_all = []
    if os.path.isfile(playlists_json) and os.stat(playlists_json).st_size > 0:
        with open(playlists_json) as f:
            try:
                playlists_all = json.load(f, object_pairs_hook=OrderedDict)

            except:
                os.remove(playlists_json)
    return playlists_all


def refreshBouquets():
    eDVBDB.getInstance().reloadServicelist()
    eDVBDB.getInstance().reloadBouquets()


def purge(dir, pattern):
    for f in os.listdir(dir):
        file_path = os.path.join(dir, f)
        if os.path.isfile(file_path):
            if re.search(pattern, f):
                os.remove(file_path)


def resetUnique():
    cfg.unique.value = 0
    cfg.bouquet_id.value = 666
    cfg.unique.save()
    cfg.bouquet_id.save()
    configfile.save()


def getcategories():
    if glob.live:
        for c in range(len(glob.livecategories)):
            categoryValues = [str(glob.livecategories[c]["category_name"]), "Live", int(glob.livecategories[c]["category_id"]), True]
            glob.categories.append(categoryValues)
    if glob.vod:
        for c in range(len(glob.vodcategories)):
            categoryValues = [str(glob.vodcategories[c]["category_name"]), "VOD", int(glob.vodcategories[c]["category_id"]), True]
            glob.categories.append(categoryValues)
    if glob.series:
        for c in range(len(glob.seriescategories)):
            categoryValues = [str(glob.seriescategories[c]["category_name"]), "Series", int(glob.seriescategories[c]["category_id"]), True]
            glob.categories.append(categoryValues)


def SelectedCategories():
    for x in glob.categories:
        # ignore = False
        if glob.live:
            for name in glob.current_playlist["bouquet_info"]["selected_live_categories"]:
                if x[0] == name and x[1] == "Live":
                    x[3] = True
                    break

        if glob.vod:
            for name in glob.current_playlist["bouquet_info"]["selected_vod_categories"]:
                if x[0] == name and x[1] == "VOD":
                    x[3] = True
                    break

        if glob.series:
            for name in glob.current_playlist["bouquet_info"]["selected_series_categories"]:
                if x[0] == name and x[1] == "Series":
                    x[3] = True


def IgnoredCategories():
    for x in glob.categories:
        ignore = False
        if glob.live:
            for name in glob.current_playlist["bouquet_info"]["ignored_live_categories"]:
                if x[0] == name and x[1] == "Live":
                    x[3] = False
                    ignore = True
                    break

        if glob.vod:
            for name in glob.current_playlist["bouquet_info"]["ignored_vod_categories"]:
                if x[0] == name and x[1] == "VOD":
                    x[3] = False
                    ignore = True
                    break

        if glob.series:
            for name in glob.current_playlist["bouquet_info"]["ignored_series_categories"]:
                if x[0] == name and x[1] == "Series":
                    x[3] = False
                    ignore = True
                    break
        if ignore is False:
            x[3] = True


def readbouquetdata():
    glob.live = False
    glob.vod = False
    glob.series = False

    glob.bouquet_id = glob.current_playlist["bouquet_info"]["bouquet_id"]
    glob.name = glob.current_playlist["bouquet_info"]["name"]
    glob.old_name = glob.current_playlist["bouquet_info"]["oldname"]
    glob.live_type = glob.current_playlist["bouquet_info"]["live_type"]
    glob.vod_type = glob.current_playlist["bouquet_info"]["vod_type"]
    glob.selected_live_categories = glob.current_playlist["bouquet_info"]["selected_live_categories"]
    glob.selected_vod_categories = glob.current_playlist["bouquet_info"]["selected_vod_categories"]
    glob.selected_series_categories = glob.current_playlist["bouquet_info"]["selected_series_categories"]

    glob.ignored_live_categories = glob.current_playlist["bouquet_info"]["ignored_live_categories"]
    glob.ignored_vod_categories = glob.current_playlist["bouquet_info"]["ignored_vod_categories"]
    glob.ignored_series_categories = glob.current_playlist["bouquet_info"]["ignored_series_categories"]

    glob.live_update = glob.current_playlist["bouquet_info"]["live_update"]
    glob.vod_update = glob.current_playlist["bouquet_info"]["vod_update"]
    glob.series_update = glob.current_playlist["bouquet_info"]["series_update"]
    glob.xmltv_address = glob.current_playlist["bouquet_info"]["xmltv_address"]
    glob.vod_order = glob.current_playlist["bouquet_info"]["vod_order"]
    glob.epg_provider = glob.current_playlist["bouquet_info"]["epg_provider"]
    glob.epg_rytec_uk = glob.current_playlist["bouquet_info"]["epg_rytec_uk"]
    glob.epg_swap_names = glob.current_playlist["bouquet_info"]["epg_swap_names"]
    glob.epg_force_rytec_uk = glob.current_playlist["bouquet_info"]["epg_force_rytec_uk"]
    glob.prefix_name = glob.current_playlist["bouquet_info"]["prefix_name"]
    glob.livebuffer = glob.current_playlist["bouquet_info"]["buffer_live"]
    glob.vodbuffer = glob.current_playlist["bouquet_info"]["buffer_vod"]
    glob.fixepg = glob.current_playlist["bouquet_info"]["fixepg"]
    try:
        glob.catchupshift = glob.current_playlist["bouquet_info"]["catchupshift"]
    except:
        glob.catchupshift = 0

    if glob.selected_live_categories != []:
        glob.live = True

    if glob.selected_vod_categories != []:
        glob.vod = True

    if glob.selected_series_categories != []:
        glob.series = True


def deleteBouquets():
    cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", str(glob.name))
    cleanName = re.sub(r" ", "_", cleanName)
    cleanName = re.sub(r"_+", "_", cleanName)

    cleanNameOld = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", str(glob.old_name))
    cleanNameOld = re.sub(r" ", "_", cleanNameOld)
    cleanNameOld = re.sub(r"_+", "_", cleanNameOld)

    # delete old bouquet files

    with open("/etc/enigma2/bouquets.tv", "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if (glob.live and "jmx_live_" + str(cleanNameOld) + "_" in line) or (glob.live and "jmx_live_" + str(cleanName) + "_" in line):
                continue
            if (glob.vod and "jmx_vod_" + str(cleanNameOld) + "_" in line) or (glob.vod and "jmx_vod_" + str(cleanName) + "_" in line):
                continue
            if (glob.series and "jmx_series_" + str(cleanNameOld) + "_" in line) or (glob.series and "jmx_series_" + str(cleanName) + "_" in line):
                continue
            if ("jmx_" + str(cleanNameOld) in line) or ("jmx_" + str(cleanName) in line):
                continue
            f.write(line)
        f.truncate()

    if glob.live:
        purge("/etc/enigma2", "jmx_live_" + str(cleanName))
        purge("/etc/enigma2", "jmx_live_" + str(cleanNameOld))

        if glob.has_epg_importer:
            purge("/etc/epgimport", "jmx." + str(cleanName))
            purge("/etc/epgimport", "jmx." + str(cleanNameOld))

    if glob.vod:
        purge("/etc/enigma2", "jmx_vod_" + str(cleanName))
        purge("/etc/enigma2", "jmx_vod_" + str(cleanNameOld))

    if glob.series:
        purge("/etc/enigma2", "jmx_series_" + str(cleanName))
        purge("/etc/enigma2", "jmx_series_" + str(cleanNameOld))

    purge("/etc/enigma2", str(cleanName) + str(".tv"))
    purge("/etc/enigma2", str(cleanNameOld) + str(".tv"))

    refreshBouquets()


def process_category(category_name, category_type, category_id, domain, port, username, password, protocol, output, bouquet, epg_alias_names, epg_name_list, rytec_ref, m3uValues):
    from . import buildxml as bx
    streamvaluesgroup = []
    streamvalues = []

    for u in (
        (":", "%3A"),
        ("'", "%27"),
        (";", "%3B"),
        ("@", "%40"),
        ("&", "%26"),
        ("=", "%3D"),
        ("+", "%2B"),
        ("$", "%24"),
        (",", "%2C"),
        ("/", "%2F"),
        ("?", "%3F"),
        ("#", "%23"),
        ("[", "%5B"),
        ("]", "%5D")
    ):
        username = username.replace(*u)

    username = username.replace("%", "%25")

    for p in (
        (":", "%3A"),
        ("'", "%27"),
        (";", "%3B"),
        ("@", "%40"),
        ("&", "%26"),
        ("=", "%3D"),
        ("+", "%2B"),
        ("$", "%24"),
        (",", "%2C"),
        ("/", "%2F"),
        ("?", "%3F"),
        ("#", "%23"),
        ("[", "%5B"),
        ("]", "%5D")
    ):
        password = password.replace(*p)

    password = password.replace("%", "%25")
    bouquetTitle = str(glob.name) + " - " + str(category_name)

    bouquetString = "#NAME " + str(bouquetTitle) + "\n"
    if bouquet["bouquet_info"]["prefix_name"] is False:
        bouquetString = "#NAME " + str(category_name) + "\n"

    service_type = 1
    # build individual bouquets

    if category_type == "Live":

        # get all the values for this live category
        streamvalues = [stream for stream in glob.livestreams if str(category_id) == str(stream["category_id"])]
        streamvaluesgroup += streamvalues

        stream_type = "live"

        for i in range(len(streamvaluesgroup)):

            epgid = False

            if bouquet["bouquet_info"]["epg_force_rytec_uk"] is True \
                or any(s in category_name.lower() for s in ("uk", "u.k", "united kingdon", "gb", "bt sport", "sky sports", "manchester", "mufc", "mutv")) \
                    or any(s in streamvaluesgroup[i]["name"].strip().lower() for s in ("uk", "u.k", "gb", "bt sport", "sky sports", "manchester", "mufc", "mutv")):

                if bouquet["bouquet_info"]["epg_rytec_uk"] is True:
                    swapname = str(streamvaluesgroup[i]["name"]).strip().lower()  # make lowercase
                    swapname = re.sub(r"\|.+?\||\[.+?\]", "", swapname)  # replace words in pipes and square brackets

                    if all(s not in swapname for s in ("(english)", "(w)", "(e)", "(ireland)", "(aberdeen)", "(dundee/tay)")):
                        swapname = re.sub(r"\(.+?\)", "", swapname)

                    swapname = swapname.strip()

                    if all(s not in swapname for s in ("atn bangla uk", "faith uk", "racing uk", "tbn uk")):
                        swapname = re.sub(" uk$", "", swapname)

                    swapname = re.sub("vip uk$", "", swapname)
                    swapname = re.sub("vip sports$", "", swapname)

                    for r in (
                        ("  ", " "),
                        ("sport:", ""),
                        ("en:", ""),
                        ("vip:", ""),
                        ("uk fhd :", ""),
                        ("uk hd :", ""),
                        ("uk sd :", ""),
                        ("uk fhd:", ""),
                        ("uk hd:", ""),
                        ("uk sd:", ""),

                        ("sky sp ", "skysp "),

                        ("e !", "e!"),
                        ("granda", "granada"),
                        (" sly", " sky"),
                        ("sly ", "sky "),
                        ("s3y", "sky"),
                        ("skyfi", "scifi"),
                        ("uk | ss", "uk | sky sports"),
                        ("sky movies", "sky cinema"),
                        ("sky movie", "sky cinema"),
                        ("greagts", "greats"),
                        ("bt sports", "bt sport"),
                        ("bee-t", "bt"),
                        ("beetee", "bt"),
                        ("cartonito", "cartoonito"),
                        ("cartoonio", "cartoonito"),
                        ("plus one", "+1"),
                        ("plus 1", "+1"),
                        ("nickoldeon", "nickelodeon"),
                        ("nicklodean", "nickelodeon"),
                        ("nickeloden", "nickelodeon"),
                        ("nicklodeon", "nickelodeon"),
                        ("nickelodeno", "nickelodeon"),
                        ("premiere sports", "premier sports"),
                        ("premiere sport", "premier sports"),
                        ("rté", "rte"),
                        ("sci-fi", "scifi"),
                        ("skycinema", "sky cinema"),
                        ("cienma", "cinema"),
                        ("nothern", "northern"),
                        ("ssp -", "sky sports"),
                        ("$port$", "sports"),
                        ("$por$", "sports"),
                        ("uk ||", ""),
                        ("uk* |", ""),
                        ("uk** |", ""),
                        ("uk fhd |", ""),
                        ("uk hd |", ""),
                        ("uk sd |", ""),
                        ("uk |", ""),
                        ("uk|", ""),

                        ("uk :", ""),
                        ("uk:", ""),
                        ("uk -", ""),

                        ("uk 50 fps", ""),
                        ("uks:", ""),
                        ("ukl:", ""),
                        ("uk i", ""),

                        ("ukd -", ""),
                        ("ukd ", ""),

                        ("uks -", ""),
                        ("uks ", ""),

                        ("ukshd -", ""),
                        ("ukshd ", ""),

                        ("ukhd -", ""),
                        ("ukhd ", ""),

                        ("ukk -", ""),
                        ("ukk ", ""),

                        ("ukn -", ""),
                        ("ukn ", ""),

                        ("ukm -", ""),
                        ("ukm ", ""),

                        ("ukl -", ""),
                        ("ukl ", ""),


                        ("fhd", "hd"),
                        ("full hd", "hd"),
                        ("1080p", "hd"),
                        ("1080", "hd"),
                        ("4k", "hd"),
                        ("uhd", "hd"),
                        ("ʜᴅ", "hd"),
                        ("sd ", ""),
                        (" sd", ""),
                        ("720p", ""),
                        ("720", ""),
                        ("local", ""),
                        ("backup", ""),
                        ("ppv", ""),
                        ("vip", ""),
                        ("pdc", ""),
                        ("hq", ""),
                        ("region", ""),
                        ("u* |", ""),
                        ("sp** |", ""),
                        ("d* |", ""),
                        ("s* |", ""),
                        ("sp* |", ""),
                        ("sp ||", ""),
                        ("||", ""),
                        ("ir: ", "")
                    ):
                        swapname = swapname.replace(*r)

                    swapname = re.sub(r"\'$", "", swapname)
                    swapname = re.sub(r"^uk[^A-Za-z0-9]+", "", swapname)
                    swapname = re.sub(r"^uki[^A-Za-z0-9]+", "", swapname)
                    swapname = re.sub(r"^ir[^A-Za-z0-9]+", "", swapname)
                    swapname = re.sub(r"^ire[^A-Za-z0-9]+", "", swapname)
                    swapname = re.sub(r"^ie[^A-Za-z0-9]+", "", swapname)
                    swapname = re.sub(r"^epl[^A-Za-z0-9]+", "", swapname)
                    swapname = re.sub(r'[^a-zA-Z0-9\u00C0-\u00FF \+\(\)\&\'\*\:\.\!\/]', '', swapname)  # replace characters not in the list with blank
                    swapname = re.sub(r'\b(hd)( \1\b)+', r'\1', swapname)  # remove duplicate hd

                    swapname = swapname.replace("hd/hd", "hd")
                    swapname = swapname.replace("()", "")
                    swapname = swapname.replace("[]", "")
                    swapname = swapname.replace("||", "")
                    swapname = re.sub(" +", " ", swapname)
                    swapname = swapname.strip(".").strip("*").strip(":").strip("'").strip()

                    found = False
                    reference = ""

                    for line in epg_alias_names:

                        for item in line:

                            if swapname == item:

                                reference = str(line[0]).lower()
                                found = True
                                break
                        if found:
                            break

                    if reference != "" and reference in rytec_ref:
                        serviceref = str(rytec_ref[reference][0])
                        epg_channel_id = str(rytec_ref[reference][1])

                        if epg_channel_id != "":
                            epgid = True
                        else:
                            epgid = False

                    if bouquet["bouquet_info"]["epg_swap_names"] is True:
                        streamvaluesgroup[i]["name"] = str(swapname).upper()

            streamvaluesgroup[i]['name'] = streamvaluesgroup[i]['name'].replace(":", "")
            streamvaluesgroup[i]['name'] = streamvaluesgroup[i]['name'].replace('"', "")

            stream_id = streamvaluesgroup[i]["stream_id"]
            if "tv_archive" in streamvaluesgroup[i]:
                catchup = int(streamvaluesgroup[i]["tv_archive"])
            else:
                catchup = 0
            calc_remainder = int(stream_id) // 65535
            bouquet_id_sid = int(glob.bouquet_id + calc_remainder)
            stream_id_sid = int(stream_id) - int(calc_remainder * 65535)

            custom_sid = ":0:" + str(service_type) + ":" + str(format(bouquet_id_sid, "04x")) + ":" + str(format(stream_id_sid, "04x")) + ":0:0:0:0:" + str(glob.livebuffer) + str(":")

            if "custom_sid" in streamvaluesgroup[i]:
                if re.match(r":\d+:\d+:[a-zA-Z0-9]+:[a-zA-Z0-9]+:[a-zA-Z0-9]+:[a-zA-Z0-9]+:0:0:0:", str(streamvaluesgroup[i]["custom_sid"])):
                    custom_sid = streamvaluesgroup[i]["custom_sid"][:-2] + str(glob.livebuffer) + str(":")
                elif re.match(r":\d+:\d+:[a-zA-Z0-9]+:[a-zA-Z0-9]+:[a-zA-Z0-9]+:[a-zA-Z0-9]+:0:0:", str(streamvaluesgroup[i]["custom_sid"])):
                    custom_sid = str(streamvaluesgroup[i]["custom_sid"]) + str(glob.livebuffer) + str(":")

            if epgid:
                custom_sid = serviceref[:-2] + str(glob.livebuffer) + str(":")

            source_epg = "1" + str(custom_sid) + "http%3a//example.m3u8"

            if epgid:
                epg_name_list.append([str(epg_channel_id), source_epg])
            elif streamvaluesgroup[i]["epg_channel_id"]:
                epg_name_list.append([str(streamvaluesgroup[i]["epg_channel_id"]), source_epg])

            name = streamvaluesgroup[i]["name"]

            if cfg.catchupprefix.value is True and catchup == 1:
                name = str(cfg.catchupprefixsymbol.value) + str(name)

            bouquetString += "#SERVICE " + str(glob.live_type) + str(custom_sid) + str(protocol) + str(domain) + "%3a" + str(port) + "/" \
                + str(stream_type) + "/" + str(username) + "/" + str(password) + "/" + str(stream_id) + "." + str(output) + ":" + str(name) + "\n"

            bouquetString += "#DESCRIPTION " + str(name) + "\n"

        bx.categoryBouquetXml("live", bouquetTitle, bouquetString)
        bx.bouquetsTvXml("live", bouquetTitle)

    elif category_type == "VOD":

        # get all the values for this VOD category
        streamvalues = [stream for stream in glob.vodstreams if str(category_id) == str(stream["category_id"])]

        # sorting
        if bouquet["bouquet_info"]["vod_order"] == "alphabetical":
            streamvalues = sorted(streamvalues, key=lambda s: s["name"])
        elif bouquet["bouquet_info"]["vod_order"] == "date":
            streamvalues = sorted(streamvalues, key=lambda s: s["added"], reverse=True)
        elif bouquet["bouquet_info"]["vod_order"] == "date2":
            streamvalues = sorted(streamvalues, key=lambda s: s["added"])

        streamvaluesgroup += streamvalues
        stream_type = "movie"
        custom_sid = ":0:1:0:0:0:0:0:0:" + str(glob.vodbuffer) + str(":")

        for i in range(len(streamvaluesgroup)):

            stream_id = streamvaluesgroup[i]["stream_id"]
            output = str(streamvaluesgroup[i]["container_extension"])

            source_epg = "1" + str(custom_sid) + str(protocol) + str(domain) + "%3a" + str(port) + "/" + str(stream_type) + "/" + str(username) + "/" + str(password) + "/" + str(stream_id) + "." + str(output)

            name = streamvaluesgroup[i]["name"]

            bouquetString += "#SERVICE " + str(glob.vod_type) + str(custom_sid) + str(protocol) + str(domain) + "%3a" + str(port) + \
                "/" + str(stream_type) + "/" + str(username) + "/" + str(password) + "/" + str(stream_id) + "." + str(output) + ":" + str(name) + "\n"

            bouquetString += "#DESCRIPTION " + str(name) + "\n"

        bx.categoryBouquetXml("vod", bouquetTitle, bouquetString)
        bx.bouquetsTvXml("vod", bouquetTitle)

    elif category_type == "Series":
        # get all the values for this series category

        streamvalues = [stream for stream in glob.seriesstreams if str(category_id) == str(stream["category_id"])]
        streamvalues = sorted(streamvalues, key=lambda s: s["name"])
        streamvaluesgroup += streamvalues
        stream_type = "series"
        custom_sid = ":0:1:0:0:0:0:0:0:" + str(glob.vodbuffer) + str(":")

        for i in range(len(streamvaluesgroup)):
            name = streamvaluesgroup[i]["name"]
            if category_name in m3uValues:
                for channel in m3uValues[category_name]:
                    source = glob.vod_type + custom_sid + channel["url"].replace(":", "%3a")
                    bouquetString += "#SERVICE " + str(source) + ":" + str(channel["name"]) + "\n"
                    bouquetString += "#DESCRIPTION " + str(channel["name"]) + "\n"
                break

        bx.categoryBouquetXml("series", bouquetTitle, bouquetString)
        bx.bouquetsTvXml("series", bouquetTitle)

    return epg_name_list


def m3u_process_category(category_name, category_type, unique_ref, epg_name_list, bouquet):
    from . import buildxml as bx
    streamvaluesgroup = []
    streamvalues = []
    bouquetTitle = str(glob.name) + " - " + str(category_name)

    bouquetString = "#NAME " + str(bouquetTitle) + "\n"

    if bouquet["bouquet_info"]["prefix_name"] is False:
        bouquetString = "#NAME " + str(category_name) + "\n"

    service_type = 1

    if category_type == "live":

        streamvalues = [stream for stream in glob.getm3ustreams if str(category_name) == str(stream[0]) and str(category_type) == str(stream[4])]
        streamvaluesgroup += streamvalues

        for m3u in streamvaluesgroup:

            # group_title = m3u[0]
            epg_name = m3u[1]

            name = m3u[2]
            name = name.replace(":", "")
            name = name.replace("'", "")

            source = m3u[3]
            source = source.replace(":", "%3a")

            custom_sid = ":0:" + str(service_type) + ":" + str(format(333, "04x")) + ":" + str(format(unique_ref, "04x")) + ":0:0:0:0:" + str(glob.livebuffer) + str(":")

            unique_ref += 1
            if unique_ref > 65535:
                unique_ref = 0
            cfg.unique.value = unique_ref
            cfg.unique.save()

            source_epg = "1" + str(custom_sid) + source

            if epg_name:
                epg_name_list.append([epg_name, source_epg])

            bouquetString += "#SERVICE " + str(glob.live_type) + str(custom_sid) + str(source) + ":" + str(name) + "\n"
            bouquetString += "#DESCRIPTION " + str(name) + "\n"

        bx.categoryBouquetXml("live", bouquetTitle, bouquetString)
        bx.bouquetsTvXml("live", bouquetTitle)

    elif category_type == "vod":

        # get all the values for this VOD category
        streamvalues = [stream for stream in glob.getm3ustreams if str(category_name) == str(stream[0]) and str(category_type) == str(stream[4])]
        streamvaluesgroup += streamvalues
        custom_sid = ":0:1:0:0:0:0:0:0:" + str(glob.vodbuffer) + str(":")

        for m3u in streamvaluesgroup:

            # group_title = m3u[0]
            epg_name = m3u[1]
            name = m3u[2]
            source = m3u[3]
            source = source.replace(":", "%3a")

            bouquetString += "#SERVICE " + str(glob.vod_type) + str(custom_sid) + str(source) + ":" + str(name) + "\n"
            bouquetString += "#DESCRIPTION " + str(name) + "\n"

        bx.categoryBouquetXml("vod", bouquetTitle, bouquetString)
        bx.bouquetsTvXml("vod", bouquetTitle)

    return epg_name_list
