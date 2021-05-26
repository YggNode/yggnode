#! /usr/bin/python3
import os
import re
import time
import humanize
import yaml
from flask import Flask, request, send_file, Response, render_template
from torrentool.api import Torrent

# server passkey which has not to bee a validated passkey
# but valid in means of length and format for getting RSS Feed and .torrent files
USER_PASSKEY = "ijnXPgYNat3VMnCsqofjUsU5zePmZr9C"

app = Flask(__name__)


@app.route('/')
def index():
    with open("config/annexes.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    server = f'{str(cfg["node"]["protocol"])}://{str(cfg["node"]["ipAdress"])}:{str(cfg["node"]["port"])}'
    name = f'{str(cfg["node"]["ipAdress"])}'
    return render_template('index.html', server=server, name=name)

# write torrents and send file on request.


@app.route('/download', methods=['GET'])
def generatingTorrent():
    remoteTempTorrent()
    if not os.path.exists(f'torrents/{request.args.get("id")}.torrent'):
        return "torrent unavailable"
    my_torrent = Torrent.from_file(f'torrents/{request.args.get("id")}.torrent')
    # changing passkey for one transmitted as parameter by user
    newUrlTracker = re.sub(
        "[a-zA-Z0-9]{32}", request.args.get("passkey"), ((my_torrent.announce_urls[0])[0]))
    my_torrent.announce_urls = newUrlTracker
    # write it in temp dir for more clarity
    my_torrent.to_file(f'torrents/tmp/{request.args.get("id")}.{request.args.get("passkey")}.torrent')
    # send torrent file
    return send_file(f'torrents/tmp/{request.args.get("id")}.{request.args.get("passkey")}.torrent',
                     as_attachment=True,
                     attachment_filename=(my_torrent.name + ".torrent"),
                     mimetype='application/x-bittorrent')

# Rss Feed route


@app.route('/rss', methods=['GET'])
def generatingRSS():
    if request.args.get("id") is None or int(request.args.get("id")) < 2139 \
            or int(request.args.get("id")) == 2146 \
            or int(request.args.get("id")) > 2187:
        return "bad category requested"
    if request.args.get("passkey") is None or len(request.args.get("passkey")) != 32:
        return "passkey not provided : please send one as parameter 'passkey'"
    if not os.path.exists(f'rss/{request.args.get("id")}.xml'):
        return "rss file unavailable for this category at the moment"
    with open(f'rss/{request.args.get("id")}.xml', "r") as rssFile:
        txt = re.sub(
            "passkey=[a-zA-Z0-9]{32}", f'passkey={request.args.get("passkey")}', rssFile.read())
    return Response(txt, mimetype='text/xml')

# Clear temp files.


def remoteTempTorrent():
    now = time.time()
    # browses all files and delete every having more than 5 secs of existence
    for torrentFile in os.listdir("torrents/tmp/"):
        if os.stat(f"torrents/tmp/{torrentFile}").st_mtime < now:
            os.remove(f"torrents/tmp/{torrentFile}")

# Links generators route.


@app.route('/links', methods=['GET'])
def generateLinks():
    # Config file
    with open("config/annexes.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    # Set variables
    server = f'{str(cfg["node"]["protocol"])}://{str(cfg["node"]["ipAdress"])}:{str(cfg["node"]["port"])}'
    name = f'{str(cfg["node"]["ipAdress"])}'
    # Check passkey an return form
    if request.args.get("passkey") == None or len(request.args.get("passkey")) != 32:
        return render_template('link.html', server=server, name=name)
    else:
        passkey = str(request.args.get("passkey"))
        catID = cfg["Categories"]["id"]
        catNAME = cfg["Categories"]["idLabel"]
        subID = cfg["sub-Categories"]["id"]
        subNAME = cfg["sub-Categories"]["idLabel"]
        catdata = dict()
        subdata = dict()
        for index in range(len(catID)):
            key = str(catNAME[index])
            url = f"{server}/rss?id={str(catID[index])}&passkey={passkey}"
            catdata[key] = url
        for index in range(len(subID)):
            key = str(subNAME[index])
            url = f"{server}/rss?id={str(subID[index])}&passkey={passkey}"
            subdata[key] = url
        return render_template('genlinks.html', catdata=catdata, subdata=subdata, server=server, name=name)

# Status route


@app.route('/status', methods=['GET'])
def getStatus():
    with open("config/annexes.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    humanize.i18n.activate("fr_FR")
    server = f'{str(cfg["node"]["protocol"])}://{str(cfg["node"]["ipAdress"])}:{str(cfg["node"]["port"])}'
    name = f'{str(cfg["node"]["ipAdress"])}'
    dataCat = dict()
    dataSub = dict()   
    for index in range(len(cfg["Categories"]["id"])):
        now = time.time()
        osModTime = os.stat(f'rss/{str(cfg["Categories"]["id"][index])}.xml').st_mtime
        lastModTime = now - osModTime
        val1 = time.strftime(" %d/%m/%Y --- %H:%M:%S ", time.localtime(osModTime))
        val2 = humanize.naturaltime(lastModTime, minimum_unit="milliseconds")
        val = (val1, val2)
        key = cfg["Categories"]["idLabel"][index]
        dataCat[key] = val
    for index in range(len(cfg["sub-Categories"]["id"])):
        now = time.time()
        osModTime = os.stat(f'rss/{str(cfg["sub-Categories"]["id"][index])}.xml').st_mtime
        lastModTime = now - osModTime
        val1 = time.strftime(" %d/%m/%Y --- %H:%M:%S ", time.localtime(osModTime))
        val2 = humanize.naturaltime(lastModTime, minimum_unit="milliseconds")
        val = (val1, val2)
        key = cfg["sub-Categories"]["idLabel"][index]
        dataSub[key] = val
    data = {**dataCat, **dataSub}
    return render_template('stats.html', server=server, name=name, data=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
