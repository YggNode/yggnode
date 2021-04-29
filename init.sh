#!/bin/bash
echo "please enter IP or Domain Name where server is located"
echo "Server must be available for listening at port 443 !"
read serverAdress
sudo apt update && sudo apt full-upgrade -y
sudo apt install python3 python3-pip apache2 git python3-certbot-apache apt-transport-https ca-certificates curl software-properties-common -y
pip3 install flask torrentool
git clone https://github.com/YggNode/yggnode.git
sudo a2enmod proxy_http rewrite ssl
sudo systemctl restart apache2
cronjob="0 * * * * sudo bash /$HOME/yggnode/update.sh"
(sudo crontab -u $USER -l; echo "$cronjob" ) | crontab -u $USER -
cronjob="0 6 * * * sudo apt update && sudo apt full-upgrade -y && sudo reboot"
(sudo crontab -u $USER -l; echo "$cronjob" ) | crontab -u $USER -
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable" -y
sudo apt update
sudo apt install docker-ce -y
docker stop flaresolverr && docker rm flaresolverr
sudo docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
sudo rm /etc/apache2/sites-enabled/000-defaul*
sudo tee -a /etc/apache2/sites-enabled/000-default.conf <<EOF
<VirtualHost *:80>
         ServerName $serverAdress
         Redirect permanent / https://$serverAdress/
         ErrorLog ${APACHE_LOG_DIR}/error.log
        RewriteEngine on
        RewriteCond %{SERVER_NAME} =$serverAdress
        RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>
EOF
sudo systemctl restart apache2
sudo mkdir /etc/apache2/ssl
sudo openssl req -x509 -nodes -days 8 -newkey rsa:2048 -keyout /etc/apache2/ssl/$serverAdress.key -out /etc/apache2/ssl/$serverAdress.crt -batch
cronjob="0 0 * * 6 openssl req -x509 -nodes -days 7 -newkey rsa:2048 -keyout /etc/apache2/ssl/$serverAdress.key -out /etc/apache2/ssl/$serverAdress.crt -batch"
(sudo crontab -u $USER -l; echo "$cronjob" ) | crontab -u $USER -

sudo tee -a /etc/apache2/sites-enabled/000-default-ssl.conf <<EOF
<VirtualHost *:443>
        ServerName $serverAdress
        ProxyPass / http://127.0.0.1:5000/
        ProxyPassReverse / http://127.0.0.1:5000/
        ErrorLog ${APACHE_LOG_DIR}/error.log
        SSLCertificateFile /etc/apache2/ssl/$serverAdress.crt
        SSLCertificateKeyFile /etc/apache2/ssl/$serverAdress.key
</VirtualHost>
EOF

sudo service apache2 restart

sudo tee -a /lib/systemd/system/yggnode.service <<EOF
[Unit]
Description=YGG RSS feed Node Server
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $HOME/yggnode/yggnode.py
Restart=on-failure
WorkingDirectory=$HOME/yggnode
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo tee -a /lib/systemd/system/resync.service <<EOF
[Unit]
Description=YGG RSS feed Synchronisation Client
After=multi-user.target

[Service]
Type=simple
User=$USER
ExecStart=sudo /usr/bin/python3 $HOME/yggnode/resync.py
Restart=on-failure
WorkingDirectory=$HOME/yggnode

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable yggnode.service
sudo systemctl enable resync.service
sed -i "s/flareServerIp/127.0.0.1/g" yggnode/annexes.yml
sed -i "s/DomainNameOrIp/${serverAdress}/g" yggnode/annexes.yml
sudo systemctl start yggnode
sudo systemctl start resync
echo "==============================="
echo "     installation complete     "
echo "==============================="