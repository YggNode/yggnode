#!/bin/bash
echo "please enter IP or Domain Name where server is located"
echo "Server must be available for listening at port 443 !"
read serverAdress
sudo apt update && sudo apt full-upgrade -y
sudo apt install python3 python3-pip nginx git apt-transport-https ca-certificates curl software-properties-common -y
pip3 install flask torrentool gevent gunicorn
git clone https://github.com/YggNode/yggnode.git
cronjob="0 * * * * sudo bash $HOME/yggnode/update.sh"
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
  --restart on-failure \
  ghcr.io/flaresolverr/flaresolverr:latest
sudo rm /etc/nginx/sites-enabled/default
sudo tee -a /etc/nginx/sites-enabled/default <<EOF
server {
        listen 80;
        rewrite ^ https://\$host\$request_uri permanent;
}
server {
        listen 443 ssl;
        ssl_certificate /etc/nginx/ssl/$serverAdress.crt;
        ssl_certificate_key /etc/nginx/ssl/$serverAdress.key;
        ssl_session_cache builtin:1000 shared:SSL:10m;
        ssl_protocols TLSv1.2;
        ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4;
        ssl_prefer_server_ciphers on;
        access_log /var/log/nginx/access.log;

        location / {
        proxy_set_header        Host \$host;
        proxy_set_header        X-Real-IP \$remote_addr;
        proxy_set_header        X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto \$scheme;
        proxy_pass      http://127.0.0.1:5000;
        }

}
EOF
sudo mkdir /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 8 -newkey rsa:2048 -keyout /etc/nginx/ssl/$serverAdress.key -out /etc/nginx/ssl/$serverAdress.crt -batch
cronjob="0 0 * * 6 openssl req -x509 -nodes -days 7 -newkey rsa:2048 -keyout /etc/nginx/ssl/$serverAdress.key -out /etc/nginx/ssl/$serverAdress.crt -batch"
(sudo crontab -u $USER -l; echo "$cronjob" ) | crontab -u $USER -

sudo service nginx restart

sudo tee -a /lib/systemd/system/yggnode.service <<EOF
[Unit]
Description=YGG RSS feed Node Server
After=multi-user.target

[Service]
Type=simple
ExecStart=gunicorn init:app -b localhost:5000 --worker-class=gevent --worker-connections=250 --workers=3
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
sudo systemctl start resync
sudo systemctl start yggnode
echo "==============================="
echo "     installation complete     "
echo "==============================="