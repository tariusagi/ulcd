#!/usr/bin/env python3
import os
import sys
import getopt
import OPi.GPIO as GPIO
from time import sleep
from baselcd import BaseLCD

DATA_MODE = GPIO.HIGH
CMD_MODE = GPIO.LOW
E_DELAY=0.001
LINE_ADDR = [ 0x80, 0xC0 ]

class HD44780OPiH616(BaseLCD):
	"""Handle LCD with Hitachi HD44780 chip in 4 bit parallel mode which attachs
	to an OrangePi H616 board (such as Zero2). The default wiring scheme is (in 
	physical numbering):
  LCD   GPIO (Physical)
  ---   ---------------
  VDD - +5V
  VSS - Ground
  V0  - Pin 3 (possitive) of a 10kΩ potentionmeter 
  RS  - 26
  RW  - Ground (to write data)
  E   - 24
  D4  - 22
  D5  - 18
  D6  - 16
  D7  - 12
	A   - 10 (backlight anode) 
	K   - Ground (backlight kathode)
	"""

	def __init__(self, rs = 26, e = 24, bla = 10, 
			d4 = 22, d5 = 18, d6 = 16, d7 = 12):
		super().__init__(driver = "HD44780", 
				e = e, rs = rs, bla = bla, d4 = d4, d5 = d5, d6 = d6, d7 = d7,
				columns = 16, lines = 2)
		GPIO.setboard(GPIO.H616)
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self._e, GPIO.OUT)
		GPIO.setup(self._rs, GPIO.OUT)
		GPIO.setup(self._d4, GPIO.OUT)
		GPIO.setup(self._d5, GPIO.OUT)
		GPIO.setup(self._d6, GPIO.OUT)
		GPIO.setup(self._d7, GPIO.OUT)
		if self._bla is not None:
			GPIO.setup(self._bla, GPIO.OUT)

	def _pulse(self):
		GPIO.output(self._e, GPIO.HIGH)
		# Need a delay in between.
		sleep(E_DELAY)
		GPIO.output(self._e, GPIO.LOW)
	 
	def _sendNibble(self, nibble):
		GPIO.output(self._d4, nibble & 0b0001 != 0)
		GPIO.output(self._d5, nibble & 0b0010 != 0)
		GPIO.output(self._d6, nibble & 0b0100 != 0)
		GPIO.output(self._d7, nibble & 0b1000 != 0)

	def _sendByte(self, byte, mode):
		"""Send one byte to the LCD. mode True for character, False for command."""
		GPIO.output(self._rs, mode)
		# High 4 bits.
		self._sendNibble(byte >> 4)
		self._pulse()
		# Low 4 bits.
		self._sendNibble(byte & 0xF)
		self._pulse()
	 
	def init(self):
		GPIO.output(self._rs, GPIO.LOW)
		self._sendNibble(0x03)
		self._pulse()
		self._pulse()
		self._pulse()
		self._sendNibble(0x02)
		self._pulse()
		self._sendByte(0x28, CMD_MODE) # Set 4 bits interface with 2 lines.
		self._sendByte(0x0C, CMD_MODE) # Display On,Cursor Off, Blink Off
	 
	def clearScreen(self):
		self._sendByte(0x01,CMD_MODE) # Clear display
		sleep(0.01)

	def printText(self, text, line = 1, col = 1, fillChar = ' '): 
		"""Print a text at the given line and column. Missing character will be 
		filled with fillChar, default is space. If fillChar is None, then the text
		will be printed as-is"""
		if line < 1 or line > self._maxLines or col < 1 or col > self._maxCols:
			# Ignore invalid position.
			return
		# Trim text longer than 16 characters.
		if fillChar is not None:
			if col > 1:
				text = text.rjust(col + len(text) - 1, fillChar)
			if len(text) < self._maxCols:
				text = text.ljust(self._maxCols, fillChar)
			col = 1
		if (len(text) + col - 1 > self._maxCols):
			text = text[0:self._maxCols - col + 1]
		# Now send to LCD.
		self._sendByte(LINE_ADDR[line - 1] + col - 1, CMD_MODE)
		for i in range(len(text)):
			self._sendByte(ord(text[i]),DATA_MODE)

	def backlight(self, state):
		super().backlight(state)
		if self._bla is not None:
			GPIO.output(self._bla, state)

	def demo(self):
		print("Running a demo...")
		self.init()
		self.clearScreen()
		self.backlight(True)
		sleep(1)
		self.printText("HD44780", line = 1, col = 6)
		self.printText("16x2 LCD demo", line = 2, col = 3)
		sleep(3)
		self.printText("1234567890*@$#%&", line = 1)
		self.printText("abcdefghijklmnop", line = 2)
		sleep(3)
		self.printText("ABCDEFGHIJKLMNOP", line = 2)
		sleep(3)
		self.printText("End of demo", line = 1, col = 4)
		self.printText("Off in  s", line = 2, col = 5)
		for i in range(4, 0, -1):
			self.printText(str(i), line = 2, col = 12, fillChar = None)
			sleep(1)
		self.clearScreen()
		self.printText("SCREEN", line = 1, col = 6)
		self.printText("OFF", line = 2, col = 8)
		self.backlight(False)

