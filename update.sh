#!/bin/bash
sudo systemctl stop yggnode
sudo systemctl stop resync
mv annexes.yml annexes.yml.old
git pull
sudo bash update_installer.sh
mv annexes.yml.old annexes.yml
sudo systemctl start yggnode
sudo systemctl start resync