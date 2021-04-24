# YggNode
Kind of CDN for rss feed and .torrent files concerned

# Installation :
You have just to download [this file](https://raw.githubusercontent.com/YggNode/yggnode/main/init.sh) to install automatically all server dependencies and requirements.

***Be carefull to execute it as root in root home directory***

It's dangerous but in future, such requirement will not be required


# Details

Flask server available for requests from RSS clients such as for example [qBittorrent](https://github.com/qbittorrent/qBittorrent) or [Jackett](https://github.com/Jackett/Jackett)

Grab original RSS feed from Yggtorrent.li using user's dedicated passkey and new .torrent files associated with RSS feed.
Due to sensitive data going through this server such as passkey, servers available for being YggNode have to check following requirements :
1. Server must contain only 2 interfaces : localhost and for example enp0s6 connected **DIRECTLY** to internet (ip address class will be checked and tracert will certify that)
2. Server must NOT be container or VM (will be checked)
3. Server's users must be only root and ygguser. ygguser will be created during installation but no rights will be given to him. (will be checked)
4. SSH must be enable and launched by default. (otherwise, it will be impossible for admins to connect for enabling this node).
5. Init script (still WIP) will install all dependencies, block all access to the server (ssh disabled + user's password reconfigured) and will create cron job to update server automatically, start YggNode server instance at startup and update python server.
6. init script will also get and install let's encrypt certificates for HTTPS access






## RSS server side
User calling for rss feed need to provide two parameters :
1. **caterogy's id** : id required to get RSS feed for a certain category. Category id must be contain in [2139;2145] for global category or [2147;2187] for sub-category
2. **personnal passkey** : passkey required to create .torrent URL for downloading later

Those two parameters are required to get RSS feed

Example : ``http://[DomainName or IP Adress]/rss?id=2139&passkey=Ttw5xQcCbmjHUwC9jCs8fdbrGEnF8yEt``

This example will return RSS feed for category 2139 (audio) and for user identified by passkey ``Ttw5xQcCbmjHUwC9jCs8fdbrGEnF8yEt`` in the form of xml file

***The passkey in the example above is not valid and has been auto-generated!!!***

## Torrent server side
User requesting .torrent file has to provide two parameters :
1. **Torrent id** : identifier linked to .torrent file requested
2. **personnal passkey** : passkey required to generate .torrent file

Those two parameters are required to get .torrent file

Example : ``http://[DomainName or IP Adress]/download?id=742868&passkey=Ttw5xQcCbmjHUwC9jCs8fdbrGEnF8yEt``

This example will return .torrent file identified by id 742868([AFFINITY SUITE : PHOTO, DESIGNER, PUBLISHER V1.9.2 [MACOS MULTI PRÉ ACTIVÉ BY TNT]](https://www4.yggtorrent.li/torrent/application/macos/742868-affinity+suite+photo+designer+publisher+v1+9+2+macos+multi+pr%C3%A9+activ%C3%A9+by+tnt)) and for user identified by passkey ``Ttw5xQcCbmjHUwC9jCs8fdbrGEnF8yEt`` in the form of ``Affinity SUITE v1.9.2 macOS_by_TNT.dmg.torrent``

***The passkey in the example above is not valid and has been auto-generated!!!***


## RSS/Torrent client side

WIP
