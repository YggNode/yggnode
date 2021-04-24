#! /usr/bin/python3
import json
import os
import re
import requests
import time
import yaml
import logging


def getFromCategory(idCat, CFcookies, catList, domainName, logger):
    if int(idCat) in catList:
        prefixType = "cat"
    else :
        prefixType = "subcat"
    url = "https://" + domainName + "/rss?action=generate&type=" + prefixType + "&id=" + idCat + "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
    print(url)
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    return (requests.get(url, cookies=CFcookies, headers=headers)).text


def ManageTorrents(rssData, CFcookies, idCat, categories, domainName, logger):
    # extract from rss feed all id torrent
    rssTorrentsListId = re.findall("id=[0-9]{6}", rssData)

    # check if rss file for category requested is available
    if os.path.isfile(os.getcwd() + "/rss/" + idCat + ".xml") and (int(idCat) not in categories):
        oldRssFile = open(os.getcwd() + "/rss/" + idCat + ".xml", "r")
        oldRssString = oldRssFile.read()
        oldRssFile.close()
        oldRssTorrentsListId = re.findall("id=[0-9]{6}", oldRssString)
        for oldIdTorrent in oldRssTorrentsListId:
            if (oldIdTorrent not in rssTorrentsListId) and (os.path.isfile("torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")):
                print("removing --> " + (re.split("=", oldIdTorrent)[1]))
                os.remove(os.getcwd() + "/torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")

    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for torrentId in rssTorrentsListId:
        # if node haven't yet download torrent designated by this ID, then download it through flaresolverr
        if not (os.path.exists(os.getcwd() + "/torrents/" + str(re.split("=", torrentId)[1]) + ".torrent")):
            # download function to implement
            time.sleep(0.5)
            r = requests.get("https://" + domainName + "/rss/download?id=" + str(
                re.split("=", torrentId)[1]) + "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH", cookies=CFcookies,
                             headers=headers, stream=True)
            torrentFile = open(os.getcwd() + "/torrents/" + str(re.split("=", torrentId)[1]) + ".torrent", "wb")
            for chunk in r.iter_content(chunk_size=8192):
                torrentFile.write(chunk)
            torrentFile.close()
            print("download torrent --> " + str(re.split("=", torrentId)[1]))

def getCookies(url, domainName, logger):
    payload = json.dumps({
        "cmd": "request.get",
        "url": "https://" + domainName,
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "maxTimeout": 60000,
    })
    headers = {
        'Content-Type': 'application/json'
    }
    cookies = dict()
    print(url, payload)
    for i in json.loads((requests.request("POST", url + "/v1", headers=headers, data=payload)).text).get(
            'solution').get('cookies'):
        cookies[i.get('name')] = i.get('value')
    return cookies

def changeDownloadUrl(rssFeed, serverURL, domainName, logger):
    return re.sub("https://" + domainName + "/rss/", serverURL + "/", rssFeed)

if __name__ == '__main__':
    confFile = open(os.getcwd() + "/annexes.yml", 'r')
    serverConfiguration = yaml.safe_load(confFile)
    confFile.close()

    if not (os.path.exists(os.getcwd() + "/logs/")):
        os.mkdir(os.getcwd() + '/logs')

    logging.basicConfig(level=logging.INFO, filename=os.getcwd() + "/esync.log")


    # construct string containing ip and port server
    FlaresolverrPath = "http://" + str(serverConfiguration["flaresolverr"]["ipAdress"]) + ":" + \
                       str(serverConfiguration["flaresolverr"]["port"])

    nodeURL = serverConfiguration["node"]["protocol"] + "://" + str(
        serverConfiguration["node"]["ipAdress"]) + ":" + str(serverConfiguration["node"]["port"])
    logging.info("Server URL : "+nodeURL)
    # read category to be syncing on this node.
    catList = serverConfiguration["Categories"]["id"]
    subCatList = serverConfiguration["sub-Categories"]["id"]
    logging.info("Successfully load categories to sync")
    # infinite loop to resync every X seconds
    while True:
        cookies = getCookies(FlaresolverrPath, serverConfiguration["yggDomainName"], logging)
        logging.info(cookies)
        for idCat in subCatList + catList:
            logging.info(str(idCat))
            # get rss feed from idCat
            rssString = getFromCategory(str(idCat), cookies, catList, serverConfiguration["yggDomainName"], logging)
            if rssString.find("<!DOCTYPE HTML>") == -1:
                logging.info("Correct response")
                # download new torrents
                if idCat not in catList:
                    logging.info("torrent management")
                    ManageTorrents(rssString, cookies, str(idCat), catList, serverConfiguration["yggDomainName"], logging)
                # write rss feed and erasing old xml file
                rssString = (changeDownloadUrl(rssString, nodeURL, serverConfiguration["yggDomainName"], logging))
                file = open(os.getcwd() + "/rss/" + str(idCat) + ".xml", "w")
                file.write(rssString)
                file.close()
                logging.info("RSS feed correctly received and analyzed")
            else:
                logging.info("Incorrect response : possible cloudfare captcha or new DNS")
        logging.info("Resync terminated : next in 5 mins")
        time.sleep(300)
