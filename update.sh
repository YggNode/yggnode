#!/bin/bash
sudo systemctl stop yggnode
sudo systemctl stop resync
cp annexes.yml annexes.yml.old
git reset --hard
git pull
mv annexes.yml.old annexes.yml
sudo bash update_installer.sh
sudo systemctl start yggnode
sudo systemctl start resync