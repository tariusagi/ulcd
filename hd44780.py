#!/usr/bin/env python3
import os
import sys
import getopt
import RPi.GPIO as GPIO
from time import sleep
from baselcd import BaseLCD

DATA_MODE = True
CMD_MODE = False
 
LINE_ADDR = [ 0x80, 0xC0 ]

#  E_PULSE = 0.0005
#  E_DELAY = 0.0005

class HD44780(BaseLCD):
	"""Handle LCD with Hitachi HD44780 chip in 4 bit parallel mode.  The default
	pins are (in BCM numbering):
  LCD   GPIO (BCM)
  ---   ----------
  VDD - +5V
  VSS - Ground
  V0  - Pin 3 (possitive) of a 10kΩ potentionmeter 
  RS  - 25
  RW  - Ground (to write data)
  E   - 24
  D4  - 23
  D5  - 17
  D6  - 18
  D7  - 22
	"""

	def __init__(self, rs = 25, en = 24, d4 = 23, d5 = 17, d6 = 18, d7 = 22):
		super().__init__(driver = "HD44780", 
				en = en, rs = rs, d4 = d4, d5 = d5, d6 = d6, d7 = d7,
				columns = 16, lines = 2)
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.en, GPIO.OUT)
		GPIO.setup(self.rs, GPIO.OUT)
		GPIO.setup(self.d4, GPIO.OUT)
		GPIO.setup(self.d5, GPIO.OUT)
		GPIO.setup(self.d6, GPIO.OUT)
		GPIO.setup(self.d7, GPIO.OUT)

	def _toggleEn(self):
		#  sleep(E_DELAY)
		GPIO.output(self.en, True)
		#  sleep(E_PULSE)
		GPIO.output(self.en, False)
		#  sleep(E_DELAY)
	 
	def _sendByte(self, byte, mode):
		"""Send one byte to the LCD. mode True for character, False for command."""
		GPIO.output(self.rs, mode)
		# High bits.
		GPIO.output(self.d4, False)
		GPIO.output(self.d5, False)
		GPIO.output(self.d6, False)
		GPIO.output(self.d7, False)
		if byte&0x10==0x10:
			GPIO.output(self.d4, True)
		if byte&0x20==0x20:
			GPIO.output(self.d5, True)
		if byte&0x40==0x40:
			GPIO.output(self.d6, True)
		if byte&0x80==0x80:
			GPIO.output(self.d7, True)
		self._toggleEn()
		# Low bits.
		GPIO.output(self.d4, False)
		GPIO.output(self.d5, False)
		GPIO.output(self.d6, False)
		GPIO.output(self.d7, False)
		if byte&0x01==0x01:
			GPIO.output(self.d4, True)
		if byte&0x02==0x02:
			GPIO.output(self.d5, True)
		if byte&0x04==0x04:
			GPIO.output(self.d6, True)
		if byte&0x08==0x08:
			GPIO.output(self.d7, True)
		self._toggleEn()
	 
	def init(self):
		self._sendByte(0x28,CMD_MODE) # Set 4 bits, 2 lines, default font.
		self._sendByte(0x0C,CMD_MODE) # Display, cursor and blinking all off.
		#  sleep(E_DELAY)
	 
	def clearScreen(self):
		self._sendByte(0x01,CMD_MODE) # Clear display

	def printText(self, text, line = 1, col = 1):
		# Avoid unused warning.
		col = None
		text = text.ljust(self.columns," ")
		self._sendByte(LINE_ADDR[line - 1], CMD_MODE)
		for i in range(self.columns):
			self._sendByte(ord(text[i]),DATA_MODE)

	def demo(self):
		print("Running a demo...")
		self.clearScreen()
		sleep(1)
		self.printText("    HD44780", line = 1)
		self.printText(" 16x2 LCD demo", line = 2)
		sleep(3)
		self.printText("1234567890*@$#%&", line = 1)
		self.printText("abcdefghijklmnop", line = 2)
		sleep(3)
		self.printText("ABCDEFGHIJKLMNOP", line = 2)
		sleep(3)
		self.printText("Have a nice day!", line = 1)
		self.printText("    The end", line = 2)
		sleep(3)
		print("End of demo.")

