#! /usr/bin/python3

import json
import os
import re
import requests
import time
import yaml
import logging
import dns.resolver
from retry import retry

# Make Rss Feed URL with config file.
def get_Url_Feed(idCat, catList, domainName):
    if int(idCat) in catList:
        prefixType = "cat"
    else:
        prefixType = "subcat"
    url = f"https://{domainName}/rss?action=generate&type={prefixType}&id={idCat}&passkey=TNdVQssYfP3GTDoB3ijgE37c8MVvkASH"
    logging.debug(f"Url {url}")
    return url

# Manages torrents file.
def manage_Torrents(rssData, cookies, idCat, categories, domainName, manual_Mode):
    # extract from rss feed all id torrent
    rssTorrentsListId = re.findall("id=[0-9]{6}", rssData)

    # check if rss file for category requested is available and remove old torrents
    if os.path.exists(f"rss/{idCat}.xml") and (int(idCat) not in categories):
        with open(f"rss/{idCat}.xml", "r") as oldRss:
            oldRssTorrentsListId = re.findall("id=[0-9]{6}", oldRss.read())
        for oldIdTorrent in oldRssTorrentsListId:
            if oldIdTorrent not in rssTorrentsListId:
                oldId = re.split("=", oldIdTorrent)[1]
                if os.path.exists(f"torrents/{oldId}.torrent"):
                    os.remove(f"torrents/{oldId}.torrent")
                    logging.info(f"removing --> {oldId}.torrent")

    for fullTorrentId in rssTorrentsListId:
        # if node haven't yet download torrent designated by this ID, then download it through Flaresolverr
        torrentId = re.split("=", fullTorrentId)[1]
        if not os.path.exists(f"torrents/{torrentId}.torrent"):
            url = f"https://{domainName}/rss/download?id={torrentId}&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
            try:
                get_Torrents(url, cookies, torrentId, manual_Mode)
            except:
                logging.warning("skep bad torrent file dll")
                pass
            time.sleep(0.5)

# Get cloudflare cookies.
@retry(tries=25, delay=120, jitter=200, logger=logging)
def get_Cookies(url, domainName):
    payload = json.dumps({
        "cmd": "request.get",
        "url": "https://" + domainName,
        "userAgent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5",
        "maxTimeout": 60000,
    })
    headers = {
        'Content-Type': 'application/json'
    }
    cookies = dict()
    logging.debug(url + payload)
    for i in json.loads((requests.request("POST", url + "/v1", headers=headers, data=payload)).text).get(
            'solution').get('cookies'):
        cookies[i.get('name')] = i.get('value')
    if len(cookies) < 2 :
        logging.warning(f'Cookies check - not pass : {str(cookies)}')
        raise ValueError(
            " Bad cookie Possible cloudfare captcha, retry loop... and wait...")
    return cookies

# Request in retry block return string rss feed.
@retry(tries=10, delay=60, jitter=10, logger=logging)
def get_Rss_Feed(url, cookies, manual_Mode):
    yggDomain = str(dns.resolver.query("ygg.dathomir.fr", "TXT")[0]).strip('"')
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5'}
    try:
        if manual_Mode:
            rss = requests.get(url, headers=get_Manual_header(), timeout=25)
            rss.raise_for_status()
            return rss.text
        else:
            rss = requests.get(url, cookies=cookies, headers=headers, timeout=25)
            rss.raise_for_status()
            return rss.text
    except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        logging.warning(
            f"Connection fails try fix : {e}")
        cookies = get_Cookies(
            flaresolverrPath, yggDomain)
        logging.debug(
            f"New cookies : {str(cookies)} ")
        raise

# request get .torrent in retry block, and write torrent files.
@retry(tries=3, delay=20, jitter=10, logger=logging)
def get_Torrents(url, cookies, torrentId, manual_Mode):
    yggDomain = str(dns.resolver.query("ygg.dathomir.fr", "TXT")[0]).strip('"')
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5'}
    try:
        if manual_Mode:
            rtorrent = requests.get(url, headers=get_Manual_header(), stream=True, timeout=25)
        else:
            rtorrent = requests.get(url, cookies=cookies,
                                    headers=headers, stream=True, timeout=25)
        rtorrent.raise_for_status()
        with open(f"torrents/{torrentId}.torrent", "wb") as torrentFile:
            for chunk in rtorrent.iter_content(chunk_size=8192):
                if chunk:
                    torrentFile.write(chunk)
        logging.info("download torrent --> " + str(torrentId))
    except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        logging.warning(
            f"Connection fails try fix with 5 mins delay: {e}")
        cookies = get_Cookies(
            flaresolverrPath, yggDomain)
        logging.debug(
            f"New cookies : {str(cookies)} ")
        raise

# Change Serveur download url.
def change_Download_Url(rssFeed, serverURL, domainName):
    return re.sub(f"https://{domainName}/rss/", f"{serverURL}/", rssFeed)

# Change Rss Titles.
def change_Title(idCat, rssString):
    catNum = serverConfiguration["sub-Categories"]["id"] + \
        serverConfiguration["Categories"]["id"]
    catNames = serverConfiguration["sub-Categories"]["idLabel"] + \
        serverConfiguration["Categories"]["idLabel"]
    index = catNum.index(idCat)
    catTitle = catNames[index]
    return re.sub("YggTorrent Tracker BitTorrent Francophone - Flux RSS", f"Yggnode RSS : {catTitle}", rssString)

#
def get_Manual_header():
    headers = {
        'Content-Type': 'application/json',
        'cookie': 'cf_clearance=h2cJ1eXR4UJNS6AZt0XgSgVJZpzgerkgCFOJ_vwuOEk-1646497569-0-150; ygg_=beioeac55c65us4g0k3pdlo1r3o9s0ak',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
        'sec-fetch-dest': 'document',
        'sec-fetch-user': '?1',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'upgrade-insecure-requests': '1',
        'cache-control': 'max-age=0',
        'authority': 'www3.yggtorrent.re'
    }
    return headers

if __name__ == '__main__':
    manual_Mode = True
    # Config file.
    with open('annexes.yml', 'r') as yamlfile:
        serverConfiguration = yaml.load(yamlfile, Loader=yaml.FullLoader)
    # Create folders if doesn't exist.
    os.makedirs("logs", exist_ok=True)
    os.makedirs("torrents/tmp", exist_ok=True)
    os.makedirs("rss", exist_ok=True)
    # Logging config
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        format='%(levelname)s - %(asctime)s ::   %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        level=LOGLEVEL,
        filename="logs/yggnode-resync.log")
    # construct string containing ip and port server for flaresolverr
    flaresolverrPath = f'http://{str(serverConfiguration["flaresolverr"]["ipAdress"])}:{str(serverConfiguration["flaresolverr"]["port"])}'
    # construct string containing ip and port server for serveur Url
    nodeURL = f'{serverConfiguration["node"]["protocol"]}://{str(serverConfiguration["node"]["ipAdress"])}:{str(serverConfiguration["node"]["port"])}'
    logging.debug(
        f"Server URL : {nodeURL}")
    # read category to be syncing on this node.
    catList = serverConfiguration["Categories"]["id"]
    subCatList = serverConfiguration["sub-Categories"]["id"]
    domainName = str(dns.resolver.query("ygg.dathomir.fr", "TXT")[0]).strip('"')
    logging.debug("Successfully load categories to sync")
    # infinite loop to resync every X seconds
    while True:
        response = requests.get(f"https://{str(domainName)}", timeout=60)
        logging.debug(
            f"Ygg Response : {str(response)} ")
        if not response.ok:
            logging.info("Cloudflare UAM enabled")
            cookies = dict()
            if not manual_Mode:
                cookies = get_Cookies(flaresolverrPath, domainName)
                logging.debug(f" Flaresolverr cookies : {str(cookies)} ")
        else:
            cookies = dict()
            if manual_Mode:
                logging.debug(f" Manual mode enabled ")
            else:
                logging.debug(f" No cookies = not hungry /. event that's not gonna happend ")

        for idCat in subCatList + catList:
            logging.info(
                f"Process category : {str(idCat)}")
            # get rss feed from idCat and renew cookie if needed
            url = get_Url_Feed(idCat, catList, domainName)
            rssString = get_Rss_Feed(url, cookies, manual_Mode)
            if rssString.find("<!DOCTYPE HTML>") == -1:
                logging.debug("rssString Correct response")
                # download new torrents
                if idCat not in catList:
                    logging.debug("Process torrent management")
                    manage_Torrents(rssString, cookies, str(
                        idCat), catList, domainName, manual_Mode)
                # Formating
                rssString = change_Download_Url(rssString, nodeURL, domainName)
                rssString = change_Title(idCat, rssString)
                with open(f"rss/{str(idCat)}.xml", "w") as file:
                    file.write(rssString)
                logging.debug(
                    "RSS feed correctly received and analyzed - sleep 3 seconds -")
                time.sleep(3)
            else:
                logging.debug(
                    "Incorrect response : possible cloudfare captcha or new DNS")
        logging.info("Resync terminated : next in " + str(int(serverConfiguration["refreshTiming"])/60) + " mins")
        time.sleep(int (serverConfiguration["refreshTiming"]))
