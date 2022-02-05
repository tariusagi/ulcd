#!/usr/bin/python3
import os
import sys
from time import sleep
import RPi.GPIO as GPIO
import spidev
import pprint
import copy
import png
from baselcd import BaseLCD
from font6x8 import font6x8
from font4x6 import font4x6
from font5x6 import font5x6

# Serial transmission speed in Hz. Set to 1.95Mhz to be safe, but 39.9Mhz
# (39900000Hz) tested working well on a Raspberry Pi Zero W.
# on Raspberry Pi Zero W.
SPI_SPEED = 1953000
# Default delay between writes to LCD's internal RAM (in microsecond).
DEFAULT_DELAY = 72
# Transmission modes: command and data.
CMD = 0
DATA = 1
# Default text mode font settings.
HCGROM_COLS = 16
HCGROM_LINES = 4
# Graphic mode settings.
WIDTH = 128
HEIGHT = 64

class ST7920HSPI(BaseLCD):
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
	# The buffer is set up as a matrix of 64 lines of 17 bytes. The last byte
	# is the indicator byte, each bit represent a pair of bytes that contain 
	# changes in the line, from MSB (first pair) to LSB (last pair).
	_gfxBuf = []

	def __init__(self, e = 11, rw = 10, rst = 25, bla = 24, freq = SPI_SPEED,
			writeDelay = DEFAULT_DELAY):
		super().__init__(driver = "ST7290", width = WIDTH, height = HEIGHT,
				columns = HCGROM_COLS, lines = HCGROM_LINES)
		self._debug = 0
		self._e = e
		self._rw = rw
		self._rst = rst
		self._bla = bla
		self._txMode = None
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		if self._bla is not None:
			GPIO.setup(self._bla, GPIO.OUT)
		# Instantiate the SPI object.
		self._spi = spidev.SpiDev()
		self._spi.open(0, 0)
		self._spi.max_speed_hz = freq
		self._spi.no_cs = True
		self._writeDelay = writeDelay
		# Default to text mode with 8x16 HCGROM font, 4 lines, 16 letters width.
		self._textMode = True
		self._hcgrom = True
		self._gfxBuf = [[0] * 17 for i in range(64)]
		self._textBuf = self._newTextBuf(self._lines, self._columns)
		# List of supported fonts.
		self._gfxFonts = {'default' : font6x8, '6x8' : font6x8,
				'4x6' : font4x6, '5x6': font5x6}
		# Default font for printing text in gfx mode.
		self._gfxFont = self._gfxFonts['default']

	def setDebug(self, level):
		"""Set setDebug level. Level 0 turn it off."""
		self._debug = level
		if level > 0:
			print("Set setDebug to level", level)
		else:
			print("Turn setDebug off")

	def _sendByte(self, byte, delay = None):
		"""Send one byte to the LCD. If delay is None, the internal value will be 
		used."""
		# A byte is sent as a pair of bytes:
		# - First byte contains the 4 MSB and 4 "0".
		# - Second byte contains the 4 LSB and 4 "0".
		self._spi.xfer2([0xF0 & byte, 0xF0 & (byte << 4)], self._spi.max_speed_hz,
				self._writeDelay if delay is None else delay, 8)

	def _send2Bytes(self, first, second, delay = None):
		"""Send 2 bytes. This is for convenience."""
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

	def _sendBlock(self, line, y, start, count):
		# Move AC.
		self._setMode(CMD)
		self._send2Bytes(0x80 + (y % 32), 0x80 + (8 if y >= 32 else 0) + start)
		self._setMode(DATA)
		for i in range(count):
			self._send2Bytes(line[2 * (start + i)], line[2 * (start + i) + 1])

	def _sendLine(self, y):
		"""Send the whole line at y to the LCD."""
		# Check the whole dirty flag first.
		if self._gfxBuf[y][16] == 0:
			# This line is clean? Nothing to do.
			return
		# Create a short alias (reference).
		buf = self._gfxBuf
		flag = buf[y][16]
		# Calculate range of data to send.
		if self._debug > 1:
			debugMsg = ""
		start = None
		for i in range(8):
			if flag & (0x80 >> i):
				# Mark the start of a new (dirty) block.
				if start is None:
					start = i
					count = 1
				else:
					# Extend current block.
					count += 1
				if i == 7:
					# Last bit? Send this last block.
					if self._debug > 1:
						debugMsg += "(last)%d:%d " % (start, count)
					self._sendBlock(buf[y], y, start, count) 
			elif start is not None:
				# End of a block? Send it!
				if self._debug > 1:
					debugMsg += "%d:%d " % (start, count)
				self._sendBlock(buf[y], y, start, count) 
				# Reset block marker.
				start = None
		if self._debug > 1:
			print("%02d: %s flag %s blocks %s" % 
					(y, ' '.join(map(lambda n: format(n, "08b"), buf[y][0:16])),
						format(flag, "08b"),
						debugMsg), file = sys.stderr)
		# Clear dirty bits.
		buf[y][16] = 0
	
	def _fillTextLine(self, text, col, maxCols, fillChar):
		# Trim text longer than display.
		if col > 1:
			text = text.rjust(col + len(text) - 1, fillChar)
		if len(text) < maxCols:
			text = text.ljust(maxCols, fillChar)
		return text

	def setBacklight(self, state):
		if self._bla is not None:
			GPIO.output(self._bla, state)

	def cleanup(self):
		GPIO.cleanup()

	def setWriteDelay(self, usec):
		"""Set delay between byte writes in microseconds. Revert to default if usec 
		is None"""
		if usec is None:
			self._writeDelay = DEFAULT_DELAY
		else:
			self._writeDelay = usec
		if self._debug > 0:
			print("Set write delay to", self._writeDelay, file = sys.stderr)

	def setFreq(self, freq):
		"""Set SPI frequency. If freq is None, revert back to default."""
		if freq is None:
			self._spi.max_speed_hz = SPI_SPEED
		else:
			self._spi.max_speed_hz = freq

	def init(self): 
		"""Initialize LCD hardware basic registers and operation mode"""
		self._setMode(CMD)
		self._sendByte(0x30) # Basic function set (8 bit).
		self._sendByte(0x0C) # Display on, cursor off, blinking off.
		self._sendByte(0x06) # No cursor or shift operation.
		self._sendByte(0x02) # Enable CGRAM for user-defined font.
		self._sendByte(0x01, 1600) # Clear screen and reset AC (need 1.6ms).

	def setTextMode(self):	
		if not self._textMode:
			self._textMode = True
			self._columns = HCGROM_COLS
			self._lines = HCGROM_LINES
			self._setMode(CMD)
			self._sendByte(0x34) # Extend instruction set
			self._sendByte(0x34) # Graphic OFF
			self._sendByte(0x30) # Basic instruction set
			self._sendByte(0x02) # Enable CGRAM for user-defined font.
			self._sendByte(0x0C) # Display ON, cursor OFF, no blinking
			self._sendByte(0x80) # Reset AC.

	def setGfxMode(self):	
		if self._textMode:
			self._textMode = False
			self._columns = self._width // self._gfxFont['width']
			self._lines = self._height // self._gfxFont['height']
			self._setMode(CMD)
			self._sendByte(0x34) # Extend instruction set
			self._sendByte(0x36) # Turn on graphic display.

	def clearScreen(self, pattern = 0, redraw = True): 
		"""Clear the entire screen, both text and graphic mode."""
		if self._textMode: 
			self._setMode(CMD)
			self._sendByte(0x01, 1600)
			self._textBuf = self._newTextBuf(self._lines, self._columns)
		else:
			# Reset internal graphic buffer.
			self._gfxBuf = [[pattern] * 17 for i in range(64)]
			# Mark all lines dirty.
			for y in range(64):
				self._gfxBuf[y][16] = 0xFF
		if redraw:
			self.redraw()

	def plot(self, x, y, inverted = False, redraw = True):
		"""Plot a dot at x, y. If inverted = True, then the dot will be inverted."""
		if (x > 127) or (y > 63):
			return
		byteIndex = x // 8
		# Mark dirty bit.
		self._gfxBuf[y][16] |= 0x80 >> (byteIndex // 2)
		# Process pixel bit.
		if inverted:
			self._gfxBuf[y][byteIndex] ^= 0x80 >> (x % 8)
		else:
			self._gfxBuf[y][byteIndex] |= 0x80 >> (x % 8)
		if redraw:
			self.redraw()

	def erase(self, x, y, redraw = True):
		"""Erase a dot at x, y (its bit will always be set to zero)."""
		if (x > 127) or (y > 63):
			return
		byteIndex = x // 8
		# Mark dirty bit.
		self._gfxBuf[y][16] |= 0x80 >> (byteIndex // 2)
		# Process pixel bit.
		self._gfxBuf[y][byteIndex] &= ~(0x80 >> (x % 8))
		if redraw:
			self.redraw()

	def redraw(self):
		"""Redraw the screen by sending changed lines to the LCD."""
		if self._textMode:
			return
		for y in range(64):
			self._sendLine(y)

	def _printText(self, text, line = 1, col = 1, fillChar = ' ', wrap = True): 
		"""Print a text at the given line and column. Missing character will be 
		filled with fillChar, default is space. If fillChar is None, then the text
		will be printed as-is"""
		if not self._textMode:
			return
		if line < 1 or line > self._lines or col < 1 or col > self._columns:
			# Ignore invalid position.
			return
		if fillChar is not None:
			text = self._fillTextLine(text, col, self._columns, fillChar)
			col = 1
		# Trim text longer than display.
		if (len(text) + col - 1 > self._columns):
			text = text[0:self._columns - col + 1]
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

	def _printGfxText(self, text, line = 1, col = 1, fillChar = ' ', wrap = True,
			redraw = True):
		"""Print text in graphic mode. Only support font width up to 8."""
		if self._textMode:
			return
		font = self._gfxFont
		if line < 1 or line > self._lines or col < 1 or col > self._columns:
			# Ignore invalid position.
			return
		if fillChar is not None:
			text = self._fillTextLine(text, col, self._columns, fillChar)
			col = 1
		# Trim text longer than display.
		if (len(text) + col - 1 > self._columns):
			text = text[0:self._columns - col + 1]
		# Draw characters on gfx buffer.
		x = (col - 1) * font['width']
		y = (line - 1) * font['height']
		for c in text:
			try:
				rows = font['bitmap'][ord(c)]
				dy = 0
				for r in rows:
					dx = 0
					for byte in r:
						for i in range(8):
							if dx >= font['width']:
								break
							if byte & (0x80 >> i):
								self.plot(x + dx, y + dy, redraw = False)
							else:
								self.erase(x + dx, y + dy, redraw = False)
							dx += 1
					dy += 1
			except KeyError:
				pass
			x += font['width']
		if redraw:
			self.redraw()

	def _demoCountdown(self, sec = 3):
		self.printText("Next in  s", line = self._lines, col = self._columns - 9)
		for i in range(sec, 0, -1):
			self.printText(str(i), line = self._lines, col = self._columns - 1,
					fillChar = None)
			sleep(1.0)

	def _demoGfxText(self, font):
		self.clearScreen()
		self.setGfxMode()
		self.clearScreen(0)
		sleep(0.5)
		oldGfxFont = self._gfxFont
		self.setGfxFont(font)
		self.printText(f"The {font['width']}x{font['height']} font demo")
		self.printText(f"{self._lines} lines of {self._columns} chars", line = 2)
		sleep(1.0)
		self.printText("Please wait...", line = 3)
		sleep(0.5)
		for col in range(self._columns):
			self.printText("=>", line = 4, col = col, fillChar = None)
			sleep(0.01)
		sleep(0.5)
		# Print the whole font sheet.
		self.printText(f"{font['size']} chars from {font['first']}", line = 2)
		line = 3
		col = 1
		for c in range(font['first'], font['first'] + font['size']):
			self._printGfxText(chr(c), line = line, col = col, fillChar = None, 
					redraw = False)
			if col == self._columns:
				# Move to next line.
				line += 1
				col = 1
			else:
				col += 1
		self.redraw()

	def _demoGfx(self):
		self.clearScreen()
		self.setGfxMode()
		self.clearScreen(0)
		self.redraw()
		sleep(0.5)
		# Draw screen borders with 1 pixel width.
		for x in range(128):
			self.plot(x, 0, False)
		for y in range(1, 64):
			self.plot(127, y, False)
		for x in range(126, -1, -1):
			self.plot(x, 63, False)
		for y in range(62, 0, -1):
			self.plot(0, y, False)
		self.redraw()
		# Draw diagonal lines.
		for x in range(128):
				self.plot(x, x // 2, False)
				self.plot(127 - x, x // 2, False)
		self.redraw()
		sleep(1)

	def _newTextBuf(self, lines, width):
		"""Return a space filled text buffer with given number of lines and width."""
		buf = [[' '] * width for i in range(lines)]
		return buf

	def printText(self, text, line = 1, col = 1, fillChar = ' ', wrap = True): 
		"""Print a text at the given line and column. Missing character will be 
		filled with fillChar, default is space. If fillChar is None, then the text
		will be printed as-is"""
		if self._textMode:
			self._printText(text, line, col, fillChar, wrap)
		else:
			self._printGfxText(text, line, col, fillChar, wrap)

	def getGfxFontNames(self):
		return list(self._gfxFonts.keys())

	def setGfxFont(self, font):
		ok = False
		if type(font) is dict:
			self._gfxFont = font
			ok = True
		elif type(font) is str:
			for s in self._gfxFonts:
				if s == font:
					self._gfxFont = self._gfxFonts[s]
					ok = True
		if ok:
			self._columns = self._width // self._gfxFont['width']
			self._lines = self._height // self._gfxFont['height']
			return True
		else:
			return False
	
	def clearTextLine(self, line):
		"""Clear given line of text by filling it with spaces"""
		self.printText('', line)

	def demo(self, option = "all"):
		self.init()
		self.setBacklight(True)

		if option == "all":
			# 16 char ruler"----------------"
			self.printText("ST7920 demo:")
			self.printText("The default 8x16", line = 2)
			self.printText("font text mode", line = 3)
			sleep(1.0)
			self.printText("Please wait...", line = 3)
			sleep(0.5)
			for i in range(16):
				self.printText(">".rjust(i + 1, '='), line = 4)
				sleep(0.05)
			self.printText("Numbers:", line = 1)
			self.printText("0123456789-+=<>/", line = 2)
			self.printText("~!@#$%^&*()_,.;?", line = 3)
			self._demoCountdown()
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
			self._demoCountdown()
			# Graphic drawing demo.
			self._demoGfx()
			# Graphic text mode demo.
			for k in self._gfxFonts.keys():
				if k == "default":
					# Skip default font.
					continue
				self._demoGfxText(self._gfxFonts[k])
				self._demoCountdown(sec = 5)
			self.setTextMode()
			self.printText("Turn off in  s", line = 4, col = 2)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 14, fillChar = None)
				sleep(1.0)
			self.clearScreen()
			self.setBacklight(False)
		elif option == "gfx":
			self._demoGfx()
		else:
			# Must be request to run graphic text demo.
			self._demoGfxText(self._gfxFonts[option])

