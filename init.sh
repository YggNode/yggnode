#!/bin/bash

sudo apt update && sudo apt full-upgrade -y
sudo apt install python3 python3-pip apache2 git python3-certbot-apache -y
pip3 install flask torrentool
git clone https://github.com/YggNode/yggnode.git
a2enmod proxy_http
systemctl restart apache2
cronjob="0 * * * * sudo bash /root/yggnode/update.sh"
(sudo crontab -u root -l; echo "$cronjob" ) | crontab -u root -
cronjob="0 6 * * * sudo apt update && sudo apt full-upgrade -y && sudo reboot"
(sudo crontab -u root -l; echo "$cronjob" ) | crontab -u root -
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable" -y
sudo apt update
sudo apt install docker-ce -y
docker stop flaresolverr && docker rm flaresolverr
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
echo "please enter IP or Domain Name where server is located"
read serverAdress
echo "Server must be available for listening at port 443 !"
rm /etc/apache2/sites-enabled/000-defaul*
echo "<VirtualHost *:80>
         ServerName $serverAdress
         Redirect permanent / https://$serverAdress/
         ErrorLog ${APACHE_LOG_DIR}/error.log
        RewriteEngine on
        RewriteCond %{SERVER_NAME} =$serverAdress
        RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>" > /etc/apache2/sites-enabled/000-default.conf
a2enmod rewrite
systemctl restart apache2
mkdir /etc/apache2/ssl
openssl req -x509 -nodes -days 8 -newkey rsa:2048 -keyout /etc/apache2/ssl/$serverAdress.key -out /etc/apache2/ssl/$serverAdress.crt -batch
cronjob="0 0 * * 6 openssl req -x509 -nodes -days 7 -newkey rsa:2048 -keyout /etc/apache2/ssl/$serverAdress.key -out /etc/apache2/ssl/$serverAdress.crt -batch"
(sudo crontab -u root -l; echo "$cronjob" ) | crontab -u root -
echo "<VirtualHost *:443>
        ServerName $serverAdress
        ProxyPass / http://127.0.0.1:5000/
        ProxyPassReverse / http://127.0.0.1:5000/
        ErrorLog ${APACHE_LOG_DIR}/error.log
        SSLCertificateFile /etc/apache2/ssl/$serverAdress.crt
        SSLCertificateKeyFile /etc/apache2/ssl/$serverAdress.key
</VirtualHost>" > /etc/apache2/sites-enabled/000-default-ssl.conf
service apache2 restart
echo "[Unit]
Description=YGG RSS feed Node Server
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/yggnode/yggnode.py
Restart=on-failure
WorkingDirectory=/root/yggnode
User=root

[Install]
WantedBy=multi-user.target" > /lib/systemd/system/yggnode.service
echo "[Unit]
Description=YGG RSS feed Synchronisation Client
After=multi-user.target

[Service]
Type=simple
User=root
ExecStart=sudo /usr/bin/python3 /root/yggnode/resync.py
#Restart=on-failure
WorkingDirectory=/root/yggnode

[Install]
WantedBy=multi-user.target" > /lib/systemd/system/resync.service

systemctl daemon-reload
systemctl enable yggnode.service
systemctl enable resync.service
systemctl start yggnode
systemctl start resync
echo "==============================="
echo "     installation complete     "
echo "==============================="