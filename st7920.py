#!/usr/bin/python3
import os
from time import sleep
import RPi.GPIO as GPIO
from baselcd import BaseLCD

LCD_CMD = 0
LCD_DATA = 1
BLANK_LINE = "                "

class ST792012864SPI(BaseLCD):
	"""Handle LCD with Sitronix ST7290 chip in SPI mode.  The default pins are 
	(in BCM numbering):
		E   = 11
		RW  = 10
		RST = 25
		BLA = 24
	"""

	def _quickSleep(self):
		sleep(0)

	def _strobe(self):
		GPIO.output(self._e, True)
		self._quickSleep()
		GPIO.output(self._e, False)

	def _strobe4(self):
		for i in range(4):
			GPIO.output(self._e, True)
			sleep(0)
			GPIO.output(self._e, False)
			sleep(0)

	def _strobe5(self):
		for i in range(5):
			GPIO.output(self._e, True)
			sleep(0)
			GPIO.output(self._e, False)
			sleep(0)
  
	def _setRw(self, state):
		GPIO.output(self._rw, state)

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

	def _setCaret(self, line, col): 
		"""Position text caret at the given line (1..4) and column (1..16)"""
		addr = 0x80
		if line == 2: 
			addr = 0x90
		elif line == 3:
			addr = 0x88
		elif line == 4: 
			addr = 0x98
		if self._hcgrom:
			addr += (col - 1) // 2
		self._sendByte(LCD_CMD, addr)
	
	def backlight(self, state):
		super().backlight(state)
		if self._bla is not None:
			GPIO.output(self._bla, state)

	def cleanup(self):
		GPIO.cleanup()

	def init(self): 
		GPIO.output(self._rw, False)
		GPIO.output(self._e, False)
		GPIO.output(self._rst, False)
		sleep(0.1)
		GPIO.output(self._rst, True)
		#
		self._sendByte(LCD_CMD, 0b00110000)  # Function set (8 bit)
		self._sendByte(LCD_CMD, 0b00110000)  # Function set (basic instruction set)
		self._sendByte(LCD_CMD, 0b00001100)  # Display ON, cursor OFF, no blinking
		self._sendByte(LCD_CMD, 0b10000000)  # Reset Address Counter
		#
		self._textMode = True
		self._hcgrom = True
		self._textBuf = [ BLANK_LINE, BLANK_LINE, BLANK_LINE, BLANK_LINE ]

	def clearScreen(self): 
		self._sendByte(LCD_CMD, 0b00000001)
		self._textBuf = [ BLANK_LINE, BLANK_LINE, BLANK_LINE, BLANK_LINE ]

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
		if (len(text) + col > self._maxCols + 1):
			text = text[0:self._maxCols - col]
		# Merge into text buffer.
		s = list(self._textBuf[line - 1])
		for i in range(len(text)):
			if s[i + col - 1] != text[i]:
				s[i + col - 1] = text[i]
		self._textBuf[line - 1] = "".join(s)
		# Now send to LCD.
		self._setCaret(line, col)
		if self._hcgrom:
			l = len(text)
			i = 0
			hi = 0
			lo = 0
			while i < l:
				# NOTE: 8x16 font require 2 character in a single address.
				if i == 0 and col % 2 == 0:
					hi = ord(self._textBuf[line - 1][col - 2])
					lo = ord(text[0])
					i = 1
				else:
					hi = ord(text[i])
					if i + 1 < l:
						lo = ord(text[i + 1])
					else:
						lo = ord(self._textBuf[line - 1][col + i])
					i += 2
				self._send2Bytes(LCD_DATA, hi, lo)

	def clearTextLine(self, line):
		self.printText('', line = line)
		# Clear text buffer.
		self._textBuf[line - 1] = BLANK_LINE

	def demo(self):
		try:
			self.init()
			self.backLight = True

			self.printText("ST7920 demo:")
			self.printText("Hi, how are you?", line = 2)
			sleep(1.0)
			self.printText("Please wait...", line = 3)
			for i in range(16):
				self.printText(">".rjust(i + 1, '='), line = 4)
				sleep(0.1)
			self.printText("Numbers:", line = 1)
			self.printText("0123456789-+=<>/", line = 2)
			self.printText("~!@#$%^&*()_,.;?", line = 3)
			self.printText("Next in  s", line = 4, col = 3)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 11, fillChar = None)
				sleep(1.0)
			self.printText("Lower cases:", line = 1)
			self.printText("abcdefghijklmnop", line = 2);
			self.printText("qrstuvwxyz", line = 3)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 11, fillChar = None)
				sleep(1.0)
			self.printText("Upper cases:", line = 1)
			self.printText("ABCDEFGHIJKLMNOP", line = 2);
			self.printText("QRSTUVWXYZ", line = 3)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 11, fillChar = None)
				sleep(1.0)
			self.printText("Turn off in  s", line = 4, col = 2)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 14, fillChar = None)
				sleep(1.0)
			self.clearScreen()
			self.backLight = False
		finally:
			self.cleanup()

	def __init__(self, e = 11, rw = 10, rst = 25, bla = 24):
		super().__init__(driver = "ST7290", e = e, rw = rw, rst = rst, bla = bla,
				columns = 16, lines = 4, width = 128, height = 64)
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self._rw, GPIO.OUT)
		GPIO.setup(self._e, GPIO.OUT)
		GPIO.setup(self._rst, GPIO.OUT)
		if self._bla is not None:
			GPIO.setup(self._bla, GPIO.OUT)
		self._textMode = True
		self._hcgrom = True
		self._textBuf = [ BLANK_LINE, BLANK_LINE, BLANK_LINE, BLANK_LINE ]

