#!/bin/sh

echo "!! This program will setup everything you need to use the HIAS NFC Authorization System !!"
echo " "

echo "-- Installing requirements"
echo " "

sudo apt update

pip3 install --user paho-mqtt
pip3 install --user psutil
pip3 install --user pn532pi
pip3 install --user requests