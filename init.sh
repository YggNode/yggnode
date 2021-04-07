#!/bin/sh
echo "please enter password for current user :"
read password
echo "Flaresolverr default uses (y/n)"
read flaresolverr
sudo apt install sshpass -y
sshpass -p $password sudo su -c "cd /root && git clone https://github.com/YggNode/yggnode.git && bash /root/yggnode/install/install.sh"