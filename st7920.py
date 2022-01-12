#!/usr/bin/python3
import os
from time import sleep
import RPi.GPIO as GPIO
from baselcd import BaseLCD

LCD_CMD = 0
LCD_DATA = 1
LCD_BLANK_LINE = "                "

class ST792012864SPI(BaseLCD):
	"""Handle LCD with Hitachi ST7290 chip in SPI mode.  The default pins are 
	(in BCM numbering):
	  RS  = 8
		E   = 11
		RW  = 10
		RST = 25
		BLA = 24
	"""

	_textMode = True
	_font8x16 = True

	_textRows = ["", "", "", ""]
	_backLight = False

	def _quickSleep(self):
		sleep(0)

	def _strobe(self):
		GPIO.output(self.en, True)
		self._quickSleep()
		GPIO.output(self.en, False)

	def _strobe4(self):
		for i in range(4):
			GPIO.output(self.en, True)
			sleep(0)
			GPIO.output(self.en, False)
			sleep(0)

	def _strobe5(self):
		for i in range(5):
			GPIO.output(self.en, True)
			sleep(0)
			GPIO.output(self.en, False)
			sleep(0)
  
	def _setRw(self, state):
		GPIO.output(self.rw, state)

	def _sendByte(self, rs, byte):
		"""Send one byte. rs = 0 for command, 1 for data"""
		# Data alert.
		self._setRw(1)
		self._strobe5()
		self._setRw(0)
		self._strobe()                                                                                  
		# Select the register.
		self._setRw(rs)
		self._strobe()
		self._setRw(0)
		self._strobe()
		# Send the first half.
		for i in range(7, 3, -1):
			self._setRw(byte & (1 << i))
			self._strobe()
		self._setRw(0)
		self._strobe4()
		# Send the last half.
		for i in range(3, -1, -1):
			self._setRw(byte & (1 << i))
			self._strobe()
		self._setRw(0)
		self._strobe4()

	def _send2Bytes(self, rs, hi, lo):
		"""Send 2 bytes at once without interruption between them"""
		# Data alert.
		self._setRw(1)
		self._strobe5()
		# Select the register.
		self._setRw(0)
		self._strobe()
		self._setRw(rs)
		self._strobe()
		self._setRw(0)
		self._strobe()
		# Send the hi byte's hi half.
		for i in range(7, 3, -1):
			self._setRw(hi & (1 << i))
			self._strobe()
		self._setRw(0)
		self._strobe4()
		# Send the hi byte's last half.
		for i in range(3, -1, -1):    
			self._setRw(hi & (1 << i))
			self._strobe()
		self._setRw(0)
		self._strobe4()
		# Send the lo byte's hi half.
		for i in range(7, 3, -1):
			self._setRw(lo & (1 << i))
			self._strobe()
		self._setRw(0)
		self._strobe4()
		# Send the lo byte's last half.
		for i in range(3, -1, -1):
			self._setRw(lo & (1 << i))
			self._strobe()
		self._setRw(0)
		self._strobe4()

	def _setCaret(self, row, col): 
		"""Position text caret at the given row (1..4) and column (1..16)"""
		addr = 0x80
		if row == 2: 
			addr = 0x90
		elif row == 3:
			addr = 0x88
		elif row == 4: 
			addr = 0x98
		if self._font8x16:
			addr += (col - 1) // 2
		self._sendByte(LCD_CMD, addr)

	def init(self):  
		self._sendByte(LCD_CMD, 0b00110000)  # function set (8 bit)
		self._sendByte(LCD_CMD, 0b00110000)  # function set (basic instruction set)
		self._sendByte(LCD_CMD, 0b00001100)  # displ.=ON , cursor=OFF , blink=OFF
		self._sendByte(LCD_CMD, 0b10000000)  # Address Counter na left horni roh
		self._textMode = True
		self._font8x16 = True
		# Clear text buffer.
		for i in range(4):
			self._textRows[i] = LCD_BLANK_LINE

	def clear(self): 
		self._sendByte(LCD_CMD, 0b00000001)  # clear
		# Clear text buffer.
		for i in range(4):
			self._textRows[i] = LCD_BLANK_LINE

	def print(self, text, row = 1, col = 1, fillChar = ' '): 
		"""Print a text at the given row (1..4) and column (1..16)"""
		# Trim text longer than 16 characters.
		if fillChar is not None:
			if col > 1:
				text = text.rjust(col + len(text) - 1, fillChar)
			if len(text) < 16:
				text = text.ljust(16, fillChar)
			col = 1
		if (len(text) + col > 17):
			text = text[0:16 - col]
		# Merge into text buffer.
		s = list(self._textRows[row - 1])
		for i in range(len(text)):
			if s[i + col - 1] != text[i]:
				s[i + col - 1] = text[i]
		self._textRows[row - 1] = "".join(s)
		# Now send to LCD.
		self._setCaret(row, col)
		if self._font8x16:
			l = len(text)
			i = 0
			hi = 0
			lo = 0
			while i < l:
				# NOTE: 8x16 font require 2 character in a single address.
				if i == 0 and col % 2 == 0:
					hi = ord(self._textRows[row - 1][col - 2])
					lo = ord(text[0])
					i = 1
				else:
					hi = ord(text[i])
					if i + 1 < l:
						lo = ord(text[i + 1])
					else:
						lo = ord(self._textRows[row - 1][col + i])
					i += 2
				self._send2Bytes(LCD_DATA, hi, lo)

	def clearTextLine(self, row):
		self.print('', row = row)
		# Clear text buffer.
		self._textRows[row - 1] = LCD_BLANK_LINE

	@property
	def backLight(self):
		return self._backLight

	@backLight.setter
	def backLight(self, option):
		self._backLight = option
		if self.bl is not None:
			GPIO.output(self.bl, option)

	def __init__(self, rs = 8, en = 11, rw = 10, rst = 25, bl = 24,
			backLight = False):
		super().__init__(driver = "ST7290", 
				rs = rs, en = en, rw = rw, rst = rst, bl = bl,
				columns = 16, lines = 4, width = 128, height = 64)
		# Initialize text buffer.
		for i in range(4):
			self._textRows[i] = LCD_BLANK_LINE
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.rs, GPIO.OUT)
		GPIO.setup(self.rw, GPIO.OUT)
		GPIO.setup(self.en, GPIO.OUT)
		GPIO.setup(self.rst, GPIO.OUT)
		if bl is not None:
			GPIO.setup(self.bl, GPIO.OUT)
			self.backLight = backLight
		#  GPIO.output(self.rs, True)
		#  GPIO.output(self.rw, False)
		#  GPIO.output(self.en, False)
		#  GPIO.output(self.rst, False)
		#  sleep(0.001)   
		#  GPIO.output(self.rst, True)

	def demo(self):
		self.backLight = True
		self.init()
		self.clear()

		self.print("ST7920 demo:")
		self.print("Hi, how are you?", row = 2)
		sleep(1.0)
		self.print("Please wait...", row = 3)
		for i in range(16):
			self.print(">".rjust(i + 1, '='), row = 4)
			sleep(0.1)
		self.print("Numbers:", row = 1)
		self.print("0123456789-+=<>/", row = 2)
		self.print("~!@#$%^&*()_,.;?", row = 3)
		self.print("Next in  s", row = 4, col = 3)
		for i in range(3, 0, -1):
			self.print(str(i), row = 4, col = 11, fillChar = None)
			sleep(1.0)
		self.print("Lower cases:", row = 1)
		self.print("abcdefghijklmnop", row = 2);
		self.print("qrstuvwxyz", row = 3)
		for i in range(3, 0, -1):
			self.print(str(i), row = 4, col = 11, fillChar = None)
			sleep(1.0)
		self.print("Upper cases:", row = 1)
		self.print("ABCDEFGHIJKLMNOP", row = 2);
		self.print("QRSTUVWXYZ", row = 3)
		for i in range(3, 0, -1):
			self.print(str(i), row = 4, col = 11, fillChar = None)
			sleep(1.0)
		self.print("Turn off in  s", row = 4, col = 2)
		for i in range(3, 0, -1):
			self.print(str(i), row = 4, col = 14, fillChar = None)
			sleep(1.0)
		self.clear()
		self.backLight = False

