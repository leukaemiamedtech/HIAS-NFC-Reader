
#!/usr/bin/env python3
######################################################################################################
#
# Organization:  Asociacion De Investigacion En Inteligencia Artificial Para La Leucemia Peter Moss
# Repository:    HIAS NFC
#
# Author:        Adam Milton-Barker (AdamMiltonBarker.com)
#
# Title:         NFC Class
# Description:   The HIAS NFC Authorization System.
# License:       MIT License
# Last Modified: 2020-09-24
#
######################################################################################################

import binascii
import json
import psutil
import requests
import signal
import threading
import time
import sys

from Classes.Helpers import Helpers
from Classes.iotJumpWay import Device as iot

from threading import Thread

from pn532pi import Pn532, pn532
from pn532pi import Pn532I2c
from pn532pi import Pn532Spi
from pn532pi import Pn532Hsu

PN532_I2C = Pn532I2c(1)
nfc = Pn532(PN532_I2C)

class NFC():
	""" NFC Class

	The HIAS NFC Authorization System.
	"""

	def __init__(self):
		""" Initializes the class. """

		self.Helpers = Helpers("NFC")

		# Initiates the iotJumpWay connection class
		self.iot = iot()
		self.iot.connect()

		# Subscribes to the commands topic
		self.iot.channelSub("Commands")

		# Sets the commands callback function
		self.iot.commandsCallback = self.commands

		# Initiates the NFC scanner
		self.scanner()

		self.Helpers.logger.info("NFC Class initialization complete.")

	def commands(self, topic, payload):
		"""
		iotJumpWay Commands Callback

		The callback function that is triggerend in the event of a
		command communication from the iotJumpWay.
		"""

		self.Helpers.logger.info("Recieved iotJumpWay Command Data : " + payload.decode())
		command = json.loads(payload.decode("utf-8"))

	def life(self):
		""" Sends vital statistics to HIAS """

		cpu = psutil.cpu_percent()
		mem = psutil.virtual_memory()[2]
		hdd = psutil.disk_usage('/').percent
		tmp = psutil.sensors_temperatures()['cpu-thermal'][0].current
		#r = requests.get('http://ipinfo.io/json?token=' +
		#                 self.Helpers.confs["iotJumpWay"]["ipinfo"])
		#data = r.json()
		#location = data["loc"].split(',')

		self.Helpers.logger.info(
			"GeniSysAI Life (TEMPERATURE): " + str(tmp) + "\u00b0")
		self.Helpers.logger.info("GeniSysAI Life (CPU): " + str(cpu) + "%")
		self.Helpers.logger.info("GeniSysAI Life (Memory): " + str(mem) + "%")
		self.Helpers.logger.info("GeniSysAI Life (HDD): " + str(hdd) + "%")
		#self.Helpers.logger.info("GeniSysAI Life (LAT): " + str(location[0]))
		#self.Helpers.logger.info("GeniSysAI Life (LNG): " + str(location[1]))

		# Send iotJumpWay notification
		self.iot.channelPub("Life", {
			"CPU": str(cpu),
			"Memory": str(mem),
			"Diskspace": str(hdd),
			"Temperature": str(tmp),
			"Latitude": float(41.5463),
			"Longitude": float(2.1086)
		})

		threading.Timer(300.0, self.life).start()

	def scanner(self):
		nfc.begin()

		versiondata = nfc.getFirmwareVersion()
		if (not versiondata):
			self.Helpers.logger.info("Didn't find PN53x board")
			raise RuntimeError("Didn't find PN53x board")

		self.Helpers.logger.info("Found board PN5 {:#x} Firmware ver. {:d}.{:d}".format((versiondata >> 24) & 0xFF,
											(versiondata >> 16) & 0xFF,
											(versiondata >> 8) & 0xFF))

		#  configure board to read RFID tags
		nfc.SAMConfig()

		self.Helpers.logger.info("Waiting for NFC chip...")

	def threading(self):
		""" Creates required module threads. """

		# Life thread
		Thread(target=self.life, args=(), daemon=True).start()

	def signal_handler(self, signal, frame):
		self.Helpers.logger.info("Disconnecting")
		self.iot.disconnect()
		sys.exit(1)


NFC = NFC()


def main():
	# Starts threading
	signal.signal(signal.SIGINT, NFC.signal_handler)
	signal.signal(signal.SIGTERM, NFC.signal_handler)
	NFC.threading()

	while True:
		found, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)

		if (found):
			chip = binascii.hexlify(uid).decode()
			NFC.Helpers.logger.info("Found an NFC chip!")
			NFC.Helpers.logger.info("Chip UID: {}".format(chip))

			# Send iotJumpWay Sensors notification
			NFC.iot.channelPub("Sensors", {
				"Type": "NFC",
				"Sensor": "PN532",
				"Value": chip,
				"Message": "Chip detected"
			})

			# Send iotJumpWay NFC notification
			NFC.iot.channelPub("NFC", {
				"Sensor": "PN532",
				"Value": chip,
				"Message": "Chip detected"
			})

			NFC.Helpers.logger.info("Waiting for NFC chip...")

		time.sleep(1)
	exit()


if __name__ == "__main__":
	main()
