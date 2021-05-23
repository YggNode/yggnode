#! /usr/bin/python3
import os
import re
import time

import yaml
from flask import Flask, request, send_file, Response, render_template
from torrentool.api import Torrent

# server passkey which has not to bee a validated passkey
# but valid in means of length and format for getting RSS Feed and .torrent files
USER_PASSKEY = "ijnXPgYNat3VMnCsqofjUsU5zePmZr9C"

app = Flask(__name__)


@app.route('/')
def index():
    confFile = open(os.getcwd() + "/annexes.yml", 'r')
    serverConfiguration = yaml.safe_load(confFile)
    confFile.close()
    return "<head><title>index</title></head>" \
           "USE : <br> \
           /download?id={torrent_id}&passkey={your_passkey}<br> \
           /rss?id={category id}&passkey={your_passkey}<br><br> \
           Categories List available <a href=" + str(serverConfiguration["node"]["protocol"])\
           + "://" + str(serverConfiguration["node"]["ipAdress"]) + ":" + str(serverConfiguration["node"]["port"]) + "/links><strong>Here</strong></a>"+ \
           "<br><br><a href=" + str(serverConfiguration["node"]["protocol"]) + "://" + str(serverConfiguration["node"]["ipAdress"]) + ":"\
                             + str(serverConfiguration["node"]["port"]) + "/status>Server last time resynchronization</a>"


@app.route('/download', methods=['GET'])
def generatingTorrent():
    remoteTempTorrent()
    if not (os.path.isfile(os.getcwd() + "/torrents/" + str(int(request.args.get("id"))) + ".torrent")):
        return "torrent unavailable"
    # grab torrent file matching id provided
    my_torrent = Torrent.from_file(os.getcwd() + "/torrents/" + request.args.get("id") + ".torrent")
    # changing passkey for one transmitted as parameter by user
    newUrlTracker = re.sub("[a-zA-Z0-9]{32}", request.args.get("passkey"), ((my_torrent.announce_urls[0])[0]))
    my_torrent.announce_urls = newUrlTracker
    # write it in temp dir for more clarity
    my_torrent.to_file(os.getcwd() + "/torrents/tmp/" + request.args.get("id") + request.args.get("passkey") + ".torrent")
    # send torrent file
    return send_file(os.getcwd() + "/torrents/tmp/" + request.args.get("id") + request.args.get("passkey") + ".torrent",
                     as_attachment=True,
                     attachment_filename=(my_torrent.name + ".torrent"),
                     mimetype='application/x-bittorrent')


@app.route('/rss', methods=['GET'])
def generatingRSS():
    remoteTempTorrent()
    # check if category id is provided and valid
    if request.args.get("id") is None or int(request.args.get("id")) < 2139 \
            or int(request.args.get("id")) == 2146 \
            or int(request.args.get("id")) > 2187:
        return "<head><title>RSS generator</title></head>bad category requested"
    # check if passkey with valid format is provided
    if request.args.get("passkey") is None:
        return "<head><title>RSS generator</title></head>passkey not provided : please send one as parameter 'passkey'"

    if not (os.path.isfile(os.getcwd() + "/rss/" + request.args.get("id") + ".xml")):
        return "<head><title>RSS generator</title></head>rss file unavailable for this category at the moment"

    # opens last updated rss file corresponding to the category called
    rssFile = open(os.getcwd() + "/rss/" + str(int(request.args.get("id"))) + ".xml", "r")
    txt = rssFile.read()
    rssFile.close()
    # create a temp rss generated file with both category and passkey as name to avoid potential simultaneous access
    # replace original passkey by the one provided by the user
    txt = re.sub("passkey=[a-zA-Z0-9]{32}", "passkey=" + request.args.get("passkey"), txt)
    return Response(txt, mimetype='text/xml')


def remoteTempTorrent():
    now = time.time()
    # browses all files and delete every having more than 5 secs of existence
    for torrentFile in os.listdir(os.getcwd() + "/torrents/tmp/"):
        if os.stat(os.getcwd() + "/torrents/tmp/" + torrentFile).st_mtime < now:
            os.remove(os.getcwd() + "/torrents/tmp/" + torrentFile)

@app.route('/links', methods=['GET'])
def generateLinks():
    if request.args.get("passkey") == None or len(request.args.get("passkey")) != 32:
        return render_template('form.html')
    else:
        confFile = open(os.getcwd() + '/annexes.yml', 'r')
        serverConfiguration = yaml.safe_load(confFile)
        confFile.close()
        renderTxt = "<head><title>RSS links generator</title></head>Flux généralistes : <br>"
        for index in range(len(serverConfiguration["Categories"]["id"])):
            renderTxt += "<strong>" + serverConfiguration["Categories"]["idLabel"][index] + "</strong><br>  " + \
                         str(serverConfiguration["node"]["protocol"]) + "://" + str(serverConfiguration["node"]["ipAdress"]) +\
                         ":" + str(serverConfiguration["node"]["port"]) + "/rss?id=" + str(serverConfiguration["Categories"]["id"][index])\
                         + "&passkey=" + str(request.args.get("passkey")) + "<br>"
        renderTxt += "<br><br><br>Flux détaillés : <br>"
        for index in range(len(serverConfiguration["sub-Categories"]["id"])):
            renderTxt += "<strong>" + serverConfiguration["sub-Categories"]["idLabel"][index] + "</strong><br>  " + \
                         str(serverConfiguration["node"]["protocol"]) + "://" + str(serverConfiguration["node"]["ipAdress"]) +\
                         ":" + str(serverConfiguration["node"]["port"]) + "/rss?id=" + str(serverConfiguration["sub-Categories"]["id"][index])\
                         + "&passkey=" + str(request.args.get("passkey")) + "<br>"

    return renderTxt

@app.route('/status', methods=['GET'])
def getStatus():
    confFile = open(os.getcwd() + '/annexes.yml', 'r')
    serverConfiguration = yaml.safe_load(confFile)
    confFile.close()
    now = time.time()
    renderTxt = "<head><title>last resync</title></head>Time since last synchronisation:<br><br>"
    for index in range(len(serverConfiguration["Categories"]["id"])):
        if not os.path.exists (os.getcwd() + "/rss/" + str(serverConfiguration["Categories"]["id"][index]) + ".xml"):
            renderTxt += "<strong>" + serverConfiguration["Categories"]["idLabel"][index] + "</strong> : never synchronized<br>"
        else:
            renderTxt += "<strong>" + serverConfiguration["Categories"]["idLabel"][index] + "</strong> : " + str(timeUnderstandable(now - os.stat(os.getcwd() + "/rss/" + str(serverConfiguration["Categories"]["id"][index]) + ".xml").st_mtime)) + "<br>"
    renderTxt += "<br><br>"
    for index in range(len(serverConfiguration["sub-Categories"]["id"])):
        if not os.path.exists (os.getcwd() + "/rss/" + str(serverConfiguration["sub-Categories"]["id"][index]) + ".xml"):
            renderTxt += "<strong>" + serverConfiguration["sub-Categories"]["idLabel"][index] + "</strong> : never synchronized<br>"
        else :
            renderTxt += "<strong>" + serverConfiguration["sub-Categories"]["idLabel"][index] + "</strong> : " + str(timeUnderstandable(now - os.stat(os.getcwd() + "/rss/" + str(serverConfiguration["sub-Categories"]["id"][index]) + ".xml").st_mtime)) + "<br>"
    return renderTxt

def timeUnderstandable(sec):
    intSeconds = int(sec)
    hour = intSeconds // 3600
    min = (intSeconds - hour*3600)//60
    sec = intSeconds - hour*3600 - min * 60
    return "%02dH %02dm %02ds" % (hour, min, sec)

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
