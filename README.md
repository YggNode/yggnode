# YggNode
Kind of CDN for rss feed and .torrent files concerned

Flask server available for requests from RSS clients such as for example [qBittorrent](https://github.com/qbittorrent/qBittorrent) or [Jackett](https://github.com/Jackett/Jackett)

Grab original RSS feed from Yggtorrent.li using user's dedicated passkey and new .torrent files associated with RSS feed.

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
