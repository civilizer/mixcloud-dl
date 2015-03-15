#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uncloud from mixcloud"""

__version__ = '0.1'
import sys

__doc__ =\
"""Unclouder.

Usage:
    uncloud.py -l TRACK_URL
    uncloud.py -l TRACK_URL [-L LOGLEVEL]
    uncloud.py -t TAG [-L LOGLEVEL]
    uncloud.py [-h]

Options:
    -l TRACK_URL download a file with a given mixcloud url
    -L LOGLEVEL 
    -t tag download all files with given tag

"""
from docopt import docopt
import urllib.request
import re
import random
import logging
import wget
import json
import os

WebUrlPrefix = "http://www.mixcloud.com/"
ApiUrlPrefix = "http://api.mixcloud.com/"

WebUrlPrefixes = [
        "https://www.mixcloud.com/",
        "http://www.mixcloud.com/",
        "https://mixcloud.com/",
        "http://mixcloud.com/",
        "https://x.mixcloud.com/",
        "http://x.mixcloud.com/",
    ]

StreamServerStart = 13
StreamServerEnd = 22

def get_track_id(track_url):
    for prefix in WebUrlPrefixes:
        res = re.sub(prefix, "", track_url)
        if res != track_url:
            return res
    return track_url


def get_stream_url(track_id, servnum_start = StreamServerStart, servnum_end = StreamServerEnd):
    track_url = WebUrlPrefix + track_id
    content = urllib.request.urlopen(track_url).read()
    m = re.search(r'm-preview="([^\"]*)"', content.decode('utf-8'))
    preview = None
    if m:
        preview = m.group(1)
    else:
        raise RuntimeError("Can't find stream url")

    stream = re.sub("previews", "c/originals", preview)
    servers = list(range(servnum_start, servnum_end))
    server = random.choice(servers)
    stream = re.sub("/stream[0-9][0-9]/", "stream{}".format(server), stream)
    stream_http_resp = urllib.request.urlopen(stream)
    if stream_http_resp.status == 200:
        return stream
    return None

def get_track_info(track_id):
    track_url = ApiUrlPrefix + track_id
    track_info = json.loads(urllib.request.urlopen(track_url).read().decode())
    return track_info

def get_tracks_tag(tag):
    from bs4 import BeautifulSoup
    content = urllib.request.urlopen(WebUrlPrefix + "/tag/" + tag).read().decode()
    soup = BeautifulSoup(content)
    playable_tags = soup.find_all('span', {'class': 'play-button'})
    track_ids = []
    for tag in playable_tags:
        if tag.has_attr('m-url'):
            track_ids.append(tag.attrs['m-url'])
    return track_ids

def download_track(track_id, filename):
    stream = get_stream_url(track_id)
    logging.info("Downloading {} -> {}".format(stream, filename))
    wget.download(stream, filename)

def main():
    logging.getLogger().setLevel(getattr(logging, 'INFO'))
    arguments = docopt(__doc__, version='Uncloud 0.1')
    #print(arguments)
    loglevel = arguments['-L']
    track_url = arguments['-l']
    tag = arguments['-t']
    if loglevel is not None and loglevel in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
        logging.getLogger().setLevel(getattr(logging, a))

    if track_url is not None :
        track_id = get_track_id(track_url)
        track_info = get_track_info(track_id)
        filename = track_info["name"] + ".mp3"
        if os.path.exists(filename):
            logging.warning("Skipping '{}', file '{}' already exists.".format(track_id, filename))
            return 0
        download_track(track_id, filename)
        return 0

    elif tag is not None:
        tracks = get_tracks_tag(tag)
        logging.info("Found {} tracks".format(tracks))
        for track_url in tracks:
            track_id = get_track_id(track_url)
            track_info = get_track_info(track_id)
            filename = track_info["name"] + ".mp3"
            if os.path.exists(filename):
                logging.warning("Skipping '{}', file '{}' already exists.".format(track_id, filename))
            else:
                download_track(track_id, filename)

    else:
        print(__doc__)


if __name__ == '__main__':
    sys.exit(main())

