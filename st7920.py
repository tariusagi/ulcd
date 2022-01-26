#!/usr/bin/python3
import os
from time import sleep
import RPi.GPIO as GPIO
import spidev
from baselcd import BaseLCD
from font3x5 import font3x5

# Serial transmission speed in Hz. Set to 1.93Mhz to be safe, but 15.6Mhz
# (15600000Hz) tested working well on a Raspberry Pi Zero W.
# on Raspberry Pi Zero W.
SPI_SPEED = 1953000
# Transmission modes: command and data.
CMD = 0
DATA = 1
# Default text mode font settings.
HCGFONT_MAX_LINES = 4
HCGFONT_MAX_COLS = 16
# FONT 3x5 settings.
FONT3x5_MAX_LINES = 10
FONT3x5_MAX_COLS = 32
FONT3x5_WIDTH=3
FONT3x5_HEIGHT=5
FONT3x5_VSPACE=1
FONT3x5_HSPACE=1

class ST792012864SPI(BaseLCD):
	"""Handle LCD with Sitronix ST7290 chip in SPI mode.  The default pins are 
	(in BCM numbering):
		E   = 11
		RW  = 10
		RST = 25
		BLA = 24
	"""
	# GDRAM buffer in memory. It has an address counter which point to the first
	# of a 2-bytes pair. So if AC = 0 means byte 0, AC = 1 means byte 2. Each line
	# has 128 dots, equal 16 bytes, so the AC range from 0 to 7. The AC will only
	# automatically increase after each data write the the GDRAM, but only within
	# that range. After that it will stop moving, and we must set a start address
	# again.
	#
	# The start address of (x, y) position follow this rule:
	# - If y = 0..31: y address set start at 0x80 + y, x (AC) start at 0x80.
	# - If y = 32..63: y address start at 0x80 + (y - 32), AC start at 0x88.
	#
	# The buffer is set up as a matrix of 64 lines of 16 bytes.
	_mem = []

	def _pulse(self):
		GPIO.output(self._e, GPIO.HIGH)
		GPIO.output(self._e, GPIO.LOW)

	def _pulse4(self):
		for i in range(4):
			GPIO.output(self._e, GPIO.HIGH)
			GPIO.output(self._e, GPIO.LOW)

	def _pulse5(self):
		for i in range(5):
			GPIO.output(self._e, GPIO.HIGH)
			GPIO.output(self._e, GPIO.LOW)
  
	def _setRw(self, state):
		GPIO.output(self._rw, state)

	def _sendByte(self, byte, delay = 72):
		"""Send one byte. If hw is True, then hardware mode will be used."""
		# A byte is sent as a pair of bytes:
		# - First byte contains the 4 MSB and 4 "0".
		# - Second byte contains the 4 LSB and 4 "0".
		if self._softClock:
			# Use software generated clock by pulsing the E pin.
			for i in range(7, 3, -1):
				GPIO.output(self._rw, byte & (1 << i))
				self._pulse()
			GPIO.output(self._rw, GPIO.LOW)
			self._pulse4()
			for i in range(3, -1, -1):
				GPIO.output(self._rw, byte & (1 << i))
				self._pulse()
			GPIO.output(self._rw, GPIO.LOW)
			self._pulse4()
		else:
			# Use hardware clock.
			self._spi.xfer2([0xF0 & byte, 0xF0 & (byte << 4)], SPI_SPEED, delay, 8)

	def _send2Bytes(self, first, second, delay = 72):
		"""Send 2 bytes at once without interruption between them."""
		self._sendByte(first, delay)
		self._sendByte(second, delay)

	def _setMode(self, mode):
		"""Start/switch transmission with mode = 0 for command, 1 for data"""
		# A transmission begin with a start byte, which set the mode (register) of
		# command or data, which consists of:
		# - 5 "1" bits.
		# - Direction bit: "0" for writing (this function), "1" for reading.
		# - Register select bit: "0" for command, "1" for data.
		# - 1 "0" bit.
		if self._txMode != mode:
			#  print(f"Start transmission mode {mode}")
			self._txMode = mode
			if self._softClock:
				GPIO.output(self._rw, GPIO.HIGH)
				self._pulse5()
				GPIO.output(self._rw, GPIO.LOW)
				self._pulse()
				GPIO.output(self._rw, mode)
				self._pulse()
				GPIO.output(self._rw, GPIO.LOW)
				self._pulse()
			else:
				self._spi.xfer2([0xF8 | (mode << 1)])

	def _setTextModeCaret(self, line, col): 
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
		self._setMode(CMD)
		self._sendByte(addr)
	
	def backlight(self, state):
		super().backlight(state)
		if self._bla is not None:
			GPIO.output(self._bla, state)

	def cleanup(self):
		GPIO.cleanup()

	def init(self): 
		"""Initialize LCD hardware basic registers and operation mode"""
		if self._softClock:
			GPIO.output(self._rw, GPIO.LOW)
			GPIO.output(self._e, GPIO.LOW)
			GPIO.output(self._rst, GPIO.LOW)
			GPIO.output(self._rst, GPIO.HIGH)
		self._setMode(CMD)
		self._sendByte(0x38)   # Basic function set (8 bit).
		self._sendByte(0x0C)   # Display on, cursor off, blinkking off.
		self._sendByte(0x06)   # No cursor or shift operation.
		self._sendByte(0x01, 1600) # Clear screen and reset AC (need 1.6ms).

	def setTextMode(self):	
		if not self._textMode:
			self._textMode = True
			self._maxLines = HCGFONT_MAX_LINES
			self._maxCols = HCGFONT_MAX_COLS
			self._setMode(CMD)
			self._sendByte(0x30)  # Function set (8 bit)
			self._sendByte(0x34)  # Extend instruction set
			self._sendByte(0x36)  # Graphic OFF
			self._sendByte(0x30)  # Basic instruction set
			self._sendByte(0x02)  # Enable CGRAM
			self._sendByte(0x0C)  # Display ON, cursor OFF, no blinking
			self._sendByte(0x80)  # Reset AC.

	def setGraphicMode(self):	
		if self._textMode:
			self._textMode = False
			self._setMode(CMD)
			self._sendByte(0x36)  # Turn on graphic display.
			self._sendByte(0x02)  # Enable CGRAM.

	def clearScreen(self, pattern = 0): 
		if self._textMode: 
			self._setMode(CMD)
			self._sendByte(0x01, 1600)
			self._textBuf = self._newTextBuf(16, 4)
		else:
			# Reset graphic mode text buffers.
			self._3x5buf = self._newTextBuf(32, 10)
			# Erase GDRAM, which effectively clear the display.
			for y in range(64):
				# Move AC.
				self._setMode(CMD)
				if y < 32:
					# Set AC to firt column of the top half of the screen.
					self._send2Bytes(0x80 | y, 0x80)
				else:
					# Set AC to firt column of the bottom half of the screen.
					self._send2Bytes(0x80 | (y - 32), 0x88)
				# Write data.
				self._setMode(DATA)
				for x in range(8):
					# Write 16 bytes of each line. The AC auto-advance 2 bytes in a line.
					self._send2Bytes(pattern, pattern)
			# Erase memory buffer.
			for y in range(64):
				for x in range(16):
					self._mem[y][x] = pattern

	def plot(self, x, y, inverted = True):
		"""Plot a dot at x, y"""
		if (x > 127) or (y > 63):
			return
		byteIndex = x // 8
		if inverted:
			self._mem[y][byteIndex] ^= 0x80 >> (x % 8)
		else:
			self._mem[y][byteIndex] |= 0x80 >> (x % 8)
		if byteIndex % 2:
			first = self._mem[y][byteIndex - 1]
			second = self._mem[y][byteIndex]
		else:
			first = self._mem[y][byteIndex]
			second = self._mem[y][byteIndex + 1]
		# Move AC.
		self._setMode(CMD)
		if y < 32:
			self._send2Bytes(0x80 | y, 0x80 | (byteIndex // 2))
		else:
			self._send2Bytes(0x80 | (y - 32), 0x88 | (byteIndex // 2))
		# Write data.
		self._setMode(DATA)
		self._send2Bytes(first, second)

	def erase(self, x, y):
		"""Erase a dot at x, y. Its bit is alway cleared to zero"""
		if (x > 127) or (y > 63):
			return
		byteIndex = x // 8
		self._mem[y][byteIndex] &= ~(0x80 >> (x % 8))
		if byteIndex % 2:
			first = self._mem[y][byteIndex - 1]
			second = self._mem[y][byteIndex]
		else:
			first = self._mem[y][byteIndex]
			second = self._mem[y][byteIndex + 1]
		# Move AC.
		self._setMode(CMD)
		if y < 32:
			self._send2Bytes(0x80 | y, 0x80 | (byteIndex // 2))
		else:
			self._send2Bytes(0x80 | (y - 32), 0x88 | (byteIndex // 2))
		# Write data.
		self._setMode(DATA)
		self._send2Bytes(first, second)

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
		# Merge into text buffer.
		s = list(self._textBuf[line - 1])
		for i in range(len(text)):
			if s[i + col - 1] != text[i]:
				s[i + col - 1] = text[i]
		self._textBuf[line - 1] = "".join(s)
		# Now send to LCD.
		self._setTextModeCaret(line, col)
		if self._hcgrom:
			l = len(text)
			i = 0
			hi = 0
			lo = 0
			self._setMode(DATA)
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
				self._setMode(DATA)
				self._send2Bytes(hi, lo)

	def printText3x5(self, text, line = 1, col = 1, fillChar = ' '):
		if not self._textMode:
			self._maxLines = FONT3x5_MAX_LINES
			self._maxCols = FONT3x5_MAX_COLS
			plotX = (col - 1) * (FONT3x5_WIDTH + FONT3x5_HSPACE)
			plotY = (line - 1) * (FONT3x5_HEIGHT + FONT3x5_VSPACE)
			for char in text:
				char = ord(char)
				if (32 > char or char > 126):
					char = 127
				# Our font set starts at ASCII 32.
				char -= 32
				# Now draw the character.
				for column in range(len(font3x5[char])):
					for row in range(len(font3x5[char][column])):
						if font3x5[char][column][row]:
							self.plot(plotX, plotY + row, inverted = False)
						else:
							self.erase(plotX, plotY + row)
					if column == len(font3x5[char]) - 1:
						# Leave a blank vertical line between characters.
						self.erase(plotX + 1, plotY + row)
						plotX += 2 * FONT3x5_HSPACE
					else:
						plotX += 1

	def clearLine(self, line):
		if self._textMode:
			self.printText('', line = line)
			# Clear text buffer.
			self._textBuf[line - 1] = BLANK_LINE

	def _demoCountdown(self, duration = 3, init = False):
		if init:
			self.printText("Next in  s", line = 4, col = 3)
		for i in range(duration, 0, -1):
			self.printText(str(i), line = 4, col = 11, fillChar = None)
			sleep(1.0)

	def _demoGraphic(self):
		# Clear text mode screen.
		self.clearScreen()
		# Switch to graphic mode.
		self.setGraphicMode()
		# Clear graphic mode screen.
		self.clearScreen(0x00)
		# 3x5 font demo.
		line = 1
		col = 1
		texts = [
				"3x5 font demo with 1px spaces ",
				"between letters and lines",
				"0123456789ABCDEFGHIJKLMNOPQRSTUV",
				"WXYZ,./<>?;':\"[]{}\|-=_+~!@#$%^&",
				"*() and a space at the end."
				]
		for s in texts:
			self.printText3x5(s, line, col);
			line += 1
		sleep(1)
		#  texts = [
				#  "1 line of 3x5 font can contains",
				#  "up to 32 letters and 10 lines"
				#  ]
		#  line = 1
		#  for s in texts:
			#  self.printText3x5(s, line, col);
			#  line += 1
		#  sleep(1)
		# Draw screen borders with 1 pixel width.
		for x in range(128):
			self.plot(x, 0)
		for y in range(1, 64):
			self.plot(127, y)
		for x in range(126, -1, -1):
			self.plot(x, 63)
		for y in range(62, 0, -1):
			self.plot(0, y)
		# Draw diagonal lines.
		for x in range(128):
				self.plot(x, x // 2)
				self.plot(127 - x, x // 2)

	def demo(self, option = "all"):
		self.init()
		self.backlight(True)

		if option == "all":
			# 16 char ruler"----------------"
			self.printText("ST7920 demo:")
			self.printText("The default 8x16", line = 2)
			self.printText("font text mode", line = 3)
			sleep(3.0)
			self.printText("Please wait...", line = 3)
			sleep(0.5)
			for i in range(16):
				self.printText(">".rjust(i + 1, '='), line = 4)
				sleep(0.1)
			self.printText("Numbers:", line = 1)
			self.printText("0123456789-+=<>/", line = 2)
			self.printText("~!@#$%^&*()_,.;?", line = 3)
			self._demoCountdown(init = True)
			self.printText("Lower cases:", line = 1)
			self.printText("abcdefghijklmnop", line = 2);
			self.printText("qrstuvwxyz", line = 3)
			self._demoCountdown()
			self.printText("Upper cases:", line = 1)
			self.printText("ABCDEFGHIJKLMNOP", line = 2);
			self.printText("QRSTUVWXYZ", line = 3)
			self._demoCountdown()
			self.clearScreen()
			self.printText("To graphic mode", line = 1)
			self._demoCountdown(init = True, duration = 5)
			self._demoGraphic()
			self.setTextMode()
			self.printText("Turn off in  s", line = 4, col = 2)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 14, fillChar = None)
				sleep(1.0)
			self.clearScreen()
			self.backlight(False)
		elif option == "gfx":
			self._demoGraphic()

	def _newTextBuf(self, width, lines):
		"""Return a space filled text buffer with given number of lines and width."""
		buf = []
		for i in range(lines):
			buf.append(' ' * width)
		return buf

	def __init__(self, e = 11, rw = 10, rst = 25, bla = 24, softClock = False):
		super().__init__(driver = "ST7290", e = e, rw = rw, rst = rst, bla = bla,
				columns = 16, lines = 4, width = 128, height = 64)
		self._softClock = softClock
		self._txMode = None
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		if self._softClock:
			print("Use soft clock.")
			GPIO.setup(self._rw, GPIO.OUT)
			GPIO.setup(self._e, GPIO.OUT)
		GPIO.setup(self._rst, GPIO.OUT)
		if self._bla is not None:
			GPIO.setup(self._bla, GPIO.OUT)
		# Instantiate the SPI object.
		if not self._softClock:
			self._spi = spidev.SpiDev()
			self._spi.open(0, 0)
			self._spi.max_speed_hz = SPI_SPEED
			self._spi.cshigh = True
		# Default to text mode with 8x16 HCGROM font, 4 lines, 16 letters width.
		self._textMode = True
		self._hcgrom = True
		self._maxLines = HCGFONT_MAX_LINES
		self._maxCols = HCGFONT_MAX_COLS
		self._textBuf = self._newTextBuf(16, 4)
		# Initialize 3x5 font buffer with 10 lines, 32 letters width.
		self._3x5buf = self._newTextBuf(32, 10)
		# Initialize the graphic bitmap (128x64) in memory buffer.
		for y in range(64):
			self._mem.append([])
			for x in range(16):
				self._mem[y].append(0)
