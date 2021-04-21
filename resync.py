import json
import os
import re
import requests
import time
import yaml


def getFromCategory(idCat, CFcookies):
    url = "https://www4.yggtorrent.li/rss?action=generate&type=subcat&id=" + idCat + \
          "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
    print(url)
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    return (requests.get(url, cookies=CFcookies, headers=headers)).text


def ManageTorrents(rssData, CFcookies, idCat, categories):
    # extract from rss feed all id torrent
    rssTorrentsListId = re.findall("id=[0-9]{6}", rssData)

    # check if rss file for category requested is available
    if os.path.isfile("rss/" + idCat + ".xml") and (int(idCat) not in categories):
        oldRssFile = open("rss/" + idCat + ".xml", "r")
        oldRssString = oldRssFile.read()
        oldRssFile.close()
        oldRssTorrentsListId = re.findall("id=[0-9]{6}", oldRssString)
        for oldIdTorrent in oldRssTorrentsListId:
            if (oldIdTorrent not in rssTorrentsListId) and (os.path.isfile("torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")):
                print("removing --> " + (re.split("=", oldIdTorrent)[1]))
                os.remove("torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")

    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for torrentId in rssTorrentsListId:
        # if node haven't yet download torrent designated by this ID, then download it through flaresolverr
        if not (os.path.exists("torrents/" + str(re.split("=", torrentId)[1]) + ".torrent")):
            # download function to implement
            time.sleep(0.5)
            r = requests.get("https://www4.yggtorrent.li/rss/download?id=" + str(
                re.split("=", torrentId)[1]) + "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH", cookies=CFcookies,
                             headers=headers, stream=True)
            torrentFile = open("torrents/" + str(re.split("=", torrentId)[1]) + ".torrent", "wb")
            for chunk in r.iter_content(chunk_size=8192):
                torrentFile.write(chunk)
            torrentFile.close()
            print("download torrent --> " + str(re.split("=", torrentId)[1]))


def initSession(id, serverPath):
    print(serverPath)
    # initialize session identified by id on serverPath flaresolverr
    payload = json.dumps({
        "cmd": "sessions.create",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "maxTimeout": 60000,
        "session": id
    })
    headers = {
        'Content-Type': 'application/json'
    }
    # TODO : look at response from request to flaresolverr (200/XXX)
    requests.request("POST", serverPath + "/v1", headers=headers, data=payload)


def getCookies(url, idSession):
    payload = json.dumps({
        "cmd": "request.get",
        "url": "https://www4.yggtorrent.li",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "maxTimeout": 60000,
        "session": "" + idSession
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


def changeDownloadUrl(rssFeed, serverURL):
    return re.sub("https://www4.yggtorrent.li/rss/", serverURL + "/", rssFeed)


if __name__ == '__main__':
    confFile = open('annexes.txt', 'r')
    serverConfiguration = yaml.safe_load(confFile)
    confFile.close()

    # construct string containing ip and port server
    FlaresolverrPath = "http://" + str(serverConfiguration["flaresolverr"]["ipAdress"]) + ":" + \
                       str(serverConfiguration["flaresolverr"]["port"])

    nodeURL = serverConfiguration["node"]["protocol"] + "://" + str(
        serverConfiguration["node"]["ipAdress"]) + ":" + str(serverConfiguration["node"]["port"])

    # initialize session in flaresolverr server
    id_session = "123456789"
    initSession(id_session, FlaresolverrPath)

    # read category to be syncing on this node.
    catList = serverConfiguration["Categories"]["id"]
    subCatList = serverConfiguration["sub-Categories"]["id"]

    # infinite loop to resync every X seconds
    while True:
        cookies = getCookies(FlaresolverrPath, id_session)
        for idCat in subCatList + catList:
            print(str(idCat))
            # get rss feed from idCat
            rssString = getFromCategory(str(idCat), cookies)
            # download new torrents
            ManageTorrents(rssString, cookies, str(idCat), catList)
            # write rss feed and erasing old xml file
            rssString = (changeDownloadUrl(rssString, nodeURL))
            file = open("rss/" + str(idCat) + ".xml", "w")
            file.write(rssString)
            file.close()
        print("en pause")
        time.sleep(300)
