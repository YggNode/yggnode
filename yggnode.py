import os
import re
import time

from flask import Flask, request, send_file, Response
from torrentool.api import Torrent

# server passkey which has not to bee a validated passkey
# but valid in means of length and format for getting RSS Feed and .torrent files
USER_PASSKEY = "ijnXPgYNat3VMnCsqofjUsU5zePmZr9C"

app = Flask(__name__)


@app.route('/')
def index():
    return 'USE : <br>' \
           '/download?id={torrent_id}&passkey={your_passkey}<br>' \
           '/rss?id={category id}&passkey={your_passkey}'


@app.route('/download', methods=['GET'])
def generatingTorrent():
    remoteTempTorrent()
    if not (os.path.isfile("torrents/" + request.args.get("id") + ".torrent")):
        return "torrent unavailable"
    # grab torrent file matching id provided
    my_torrent = Torrent.from_file("torrents/" + request.args.get("id") + ".torrent")
    # changing passkey for one transmitted as parameter by user
    newUrlTracker = re.sub("[a-zA-Z0-9]{32}", request.args.get("passkey"), ((my_torrent.announce_urls[0])[0]))
    my_torrent.announce_urls = newUrlTracker
    # write it in temp dir for more clarity
    my_torrent.to_file("torrents/tmp/" + request.args.get("id") + request.args.get("passkey") + ".torrent")
    # send torrent file
    return send_file("torrents/tmp/" + request.args.get("id") + request.args.get("passkey") + ".torrent",
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
        return "bad category requested"
    # check if passkey with valid format is provided
    if request.args.get("passkey") is None:
        return "passkey not provided : please send one as parameter 'passkey'"

    if not (os.path.isfile("rss/" + request.args.get("id") + ".xml")):
        return "rss file unavailable for this category at the moment"

    # opens last updated rss file corresponding to the category called
    rssFile = open("rss/" + request.args.get("id") + ".xml", "r")
    txt = rssFile.read()
    rssFile.close()
    # create a temp rss generated file with both category and passkey as name to avoid potential simultaneous access
    # replace original passkey by the one provided by the user
    txt = re.sub("passkey=[a-zA-Z0-9]{32}", "passkey=" + request.args.get("passkey"), txt)
    return Response(txt, mimetype='text/xml')


def remoteTempTorrent():
    now = time.time()
    # browses all files and delete every having more than 5 secs of existence
    for torrentFile in os.listdir("torrents/tmp/"):
        if os.stat("torrents/tmp/" + torrentFile).st_mtime < now - 1:
            if os.path.isfile("torrents/tmp/" + torrentFile):
                os.remove("torrents/tmp/" + torrentFile)


if __name__ == '__main__':
    # initialize working environment for python server
    if not (os.path.exists("rss/")):
        os.mkdir('rss')
    if not (os.path.exists("torrents/")):
        os.mkdir('torrents')
    if not (os.path.exists("torrents/tmp")):
        os.mkdir('torrents/tmp')

    app.run(host='0.0.0.0', port=5000)
