import os, re, linecache, time, requests, json


def getFromCategory(idCat, CFcookies):
    url = "https://www4.yggtorrent.li/rss?action=generate&type=cat&id=" + idCat + "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH"
    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    return (requests.get(url, cookies=CFcookies, headers=headers)).text


def ManageTorrents(rssData, CFcookies, idCat):
    # extract from rss feed all id torrent
    rssTorrentsListId = re.findall("id=[0-9]{6}", rssData)

    if os.path.isfile("rss/" + idCat + ".xml"):
        oldRssFile = open("rss/" + idCat + ".xml", "r")
        oldRssString = oldRssFile.read(); oldRssFile.close()
        oldRssTorrentsListId = re.findall("id=[0-9]{6}", oldRssString)
        for oldIdTorrent in oldRssTorrentsListId:
            if oldIdTorrent not in rssTorrentsListId and os.path.isfile("torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent"):
                os.remove("torrents/" + (re.split("=", oldIdTorrent)[1]) + ".torrent")

    headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for torrentId in rssTorrentsListId:
        # if node haven't yet download torrent designated by this ID, then download it through flaresolverr
        if not (os.path.exists("torrents/" + str(re.split("=", torrentId)[1]) + ".torrent")):
            # download function to implement
            r = requests.get("https://www4.yggtorrent.li/rss/download?id=" + str(
                re.split("=", torrentId)[1]) + "&passkey=TNdVQssYfP3GTDnB3ijgE37c8MVvkASH", cookies=CFcookies,
                             headers=headers, stream=True)
            torrentFile = open("torrents/" + str(re.split("=", torrentId)[1]) + ".torrent", "wb")
            for chunk in r.iter_content(chunk_size=8192):
                torrentFile.write(chunk)
            torrentFile.close()


def initSession(id, serverPath):
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
    requests.request("POST", "http://" + serverPath + "/v1", headers=headers, data=payload)


def getCatRequested():
    # return categories for which node had been setup
    fileCat = open("idCat.txt", "r")
    analyseCategories = fileCat.readlines()
    catList = []
    for idCat in analyseCategories:
        if not (int(idCat) < 2139 or int(idCat) == 2146 or int(idCat) > 2187):
            catList.append(int(idCat))
    return catList


def getServerIpPort():
    return linecache.getline('annexes.txt', 1).strip() + ":" + linecache.getline('annexes.txt', 2).strip()


def getCookies(serverPath, idSession):
    url = "http://" + serverPath + "/v1"
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
    for i in json.loads((requests.request("POST", url, headers=headers, data=payload)).text).get('solution').get(
            'cookies'):
        cookies[i.get('name')] = i.get('value')
    return cookies


if __name__ == '__main__':
    # construct string containing ip and port server
    serverPath = getServerIpPort()
    # initialize session in flaresolverr server
    id_session = "123456789"
    initSession(id_session, serverPath)
    # read category to be syncing on this node.
    catlist = getCatRequested()

    # infinite loop to resync every X seconds
    while True:
        cookies = getCookies(serverPath, id_session)
        print(cookies)
        for idCat in catlist:
            # get rss feed from idCat
            rssString = getFromCategory(str(idCat), cookies)
            # download new torrents
            ManageTorrents(rssString, cookies, str(idCat))
            # write rss feed and erasing old xml file
            file = open("rss/" + str(idCat) + ".xml", "w")
            file.write(rssString)
            file.close()
        time.sleep(60)
