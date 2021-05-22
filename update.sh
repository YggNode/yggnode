#!/bin/bash
sudo systemctl stop yggnode
sudo systemctl stop resync
mv annexes.yml annexes.yml.save
git pull
mv annexes.yml.save annexes.yml
sudo systemctl start yggnode
sudo systemctl start resync