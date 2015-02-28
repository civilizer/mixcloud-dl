#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uncloud from mixcloud"""

__version__ = '0.1'
import sys

__doc__ =\
"""Unclouder.

Usage:
    uncloud.py [-l TRACK_URL]
    uncloud.py [-l TRACK_URL] [-L LOGLEVEL]
    uncloud.py [-t TAG] [-L LOGLEVEL]

Options:
    -l TRACK_URL
    -L LOGLEVEL
    -t tag

"""
from docopt import docopt
import urllib.request
import re
import random
import logging
import wget
import json

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
        track_ids.append(tag.attrs['m-url'])
    return track_ids

def download_track(track_id):
    track_info = get_track_info(track_id)
    stream = get_stream_url(track_id)

    filename = track_info["name"] + ".mp3"
    logging.info("Downloading {} -> {}".format(stream, filename))
    wget.download(stream, filename)


def main():
    logging.getLogger().setLevel(getattr(logging, 'INFO'))
    arguments = docopt(__doc__, version='Uncloud 0.1')
    print(arguments)
    loglevel = arguments['-L']
    if loglevel is not None and loglevel in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
        logging.getLogger().setLevel(getattr(logging, a))

    track_url = arguments['-l']
    if track_url is not None:
        download_track(get_track_id(track_url))
        return 0

    tag = arguments['-t']
    if tag is not None:
        tracks = get_tracks_tag(tag)
        logging.info("Found {} tracks".format(tracks))
        for track in tracks:
            download_track(track)

if __name__ == '__main__':
    sys.exit(main())

