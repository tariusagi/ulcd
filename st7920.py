#!/usr/bin/python3
import os
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

# Toggle debug mode.
DEBUG = False
# Serial transmission speed in Hz. Set to 1.93Mhz to be safe, but 15.6Mhz
# (15600000Hz) tested working well on a Raspberry Pi Zero W.
# on Raspberry Pi Zero W.
SPI_SPEED = 1953000
# Default delay between writes to LCD's internal RAM (in microsecond).
WRITE_DELAY = 72
# Transmission modes: command and data.
CMD = 0
DATA = 1
# Default text mode font settings.
HCGROM_LINES = 4
HCGROM_COLS = 16
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

	def __init__(self, e = 11, rw = 10, rst = 25, bla = 24):
		super().__init__(driver = "ST7290")
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
		self._spi.max_speed_hz = SPI_SPEED
		self._spi.no_cs = True
		# Default to text mode with 8x16 HCGROM font, 4 lines, 16 letters width.
		self._textMode = True
		self._hcgrom = True
		self._gfxBuf = [[0] * 17 for i in range(64)]
		self._textBuf = self._newTextBuf(HCGROM_LINES, HCGROM_COLS)
		# List of supported fonts.
		self._gfxFonts = {'default' : font6x8, '6x8' : font6x8,
				'4x6' : font4x6, '5x6': font5x6}
		# Default font for printing text in gfx mode.
		self._gfxFont = self._gfxFonts['default']

	def _sendByte(self, byte, delay = WRITE_DELAY):
		"""Send one byte. Note that ST7920 requires 72us delay after each write."""
		# A byte is sent as a pair of bytes:
		# - First byte contains the 4 MSB and 4 "0".
		# - Second byte contains the 4 LSB and 4 "0".
		self._spi.xfer2([0xF0 & byte, 0xF0 & (byte << 4)], SPI_SPEED, delay, 8)

	def _send2Bytes(self, first, second, delay = WRITE_DELAY):
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
		self._send2Bytes(0x80 + (y % 32), 0x80 + (8 if y >= 32 else 0) + start,
				delay = 0)
		self._setMode(DATA)
		for i in range(count):
			self._send2Bytes(line[2 * (start + i)], line[2 * (start + i) + 1],
					delay = 0)

	def _sendLine(self, y):
		"""Send the whole line at y to the LCD."""
		global DEBUG
		# Check the whole dirty flag first.
		if self._gfxBuf[y][16] == 0:
			# This line is clean? Nothing to do.
			return
		# Create a short alias (reference).
		buf = self._gfxBuf
		flag = buf[y][16]
		# Calculate range of data to send.
		if DEBUG:
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
					if DEBUG:
						debugMsg += "(last)%d:%d " % (start, count)
					self._sendBlock(buf[y], y, start, count) 
			elif start is not None:
				# End of a block? Send it!
				if DEBUG:
					debugMsg += "%d:%d " % (start, count)
				self._sendBlock(buf[y], y, start, count) 
				# Reset block marker.
				start = None
		if DEBUG:
			print("%02d: %s flag %s blocks %s" % 
					(y, ' '.join(map(lambda n: format(n, "08b"), buf[y][0:16])),
						format(flag, "08b"),
						debugMsg))
		# Clear dirty bits.
		buf[y][16] = 0
	
	def _fillTextLine(self, text, col, maxCols, fillChar):
		# Trim text longer than display.
		if col > 1:
			text = text.rjust(col + len(text) - 1, fillChar)
		if len(text) < maxCols:
			text = text.ljust(maxCols, fillChar)
		return text

	def backlight(self, state):
		if self._bla is not None:
			GPIO.output(self._bla, state)

	def cleanup(self):
		GPIO.cleanup()

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
			self._setMode(CMD)
			self._sendByte(0x34) # Extend instruction set
			self._sendByte(0x36) # Turn on graphic display.

	def clearScreen(self, pattern = 0, redraw = True): 
		"""Clear the entire screen, both text and graphic mode."""
		if self._textMode: 
			self._setMode(CMD)
			self._sendByte(0x01, 1600)
			self._textBuf = self._newTextBuf(HCGROM_LINES, HCGROM_COLS)
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

	def _printText(self, text, line = 1, col = 1, fillChar = ' '): 
		"""Print a text at the given line and column. Missing character will be 
		filled with fillChar, default is space. If fillChar is None, then the text
		will be printed as-is"""
		if not self._textMode:
			return
		if line < 1 or line > HCGROM_LINES or col < 1 or col > HCGROM_COLS:
			# Ignore invalid position.
			return
		if fillChar is not None:
			text = self._fillTextLine(text, col, HCGROM_COLS, fillChar)
			col = 1
		# Trim text longer than display.
		if (len(text) + col - 1 > HCGROM_COLS):
			text = text[0:HCGROM_COLS - col + 1]
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

	def _printGfxText(self, text, line = 1, col = 1, fillChar = ' '):
		if self._textMode:
			return
		font = self._gfxFont
		LINES = HEIGHT // font['height']
		COLS = WIDTH // font['width']
		if line < 1 or line > LINES or col < 1 or col > COLS:
			# Ignore invalid position.
			return
		if fillChar is not None:
			text = self._fillTextLine(text, col, COLS, fillChar)
			col = 1
		# Trim text longer than display.
		if (len(text) + col - 1 > COLS):
			text = text[0:COLS - col + 1]
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
							if dx > font['width']:
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

	def _demoCountdown(self, duration = 3, init = False):
		if init:
			self.printText("Next in  s", line = 4, col = 3)
		for i in range(duration, 0, -1):
			self.printText(str(i), line = 4, col = 11, fillChar = None)
			sleep(1.0)

	def _demoGfxCountdown(self, duration = 3, init = False):
		if init:
			self.printText("Next in  s", line = 4, col = 3)
			self.redraw()
		for i in range(duration, 0, -1):
			self.printText(str(i), line = 4, col = 11, fillChar = None)
			self.redraw()
			sleep(1.0)

	def _demo4x6(self):
		self.clearScreen()
		self.setGfxMode()
		self.clearScreen(0)
		sleep(0.5)
		self.setGfxFont('4x6')
		#6x8 font ruler:  "---------------------"
		self.printText("The 4x6 font demo!")
		self.printText("A custom font in gfx", line = 2)
		self.printText("4px width, 6px height", line = 3)
		sleep(1.0)
		self.printText("Please wait...", line = 3)
		sleep(0.5)
		for i in range(WIDTH // self._gfxFont['width']):
			self.printText(">".rjust(i + 1, '='), line = 4)
			sleep(0.05)
		self.printText("Numbers:", line = 1)
		self.printText("0123456789-+=<>/", line = 2, redraw = False)
		self.printText("~!@#$%^&*()_,.;?", line = 3, redraw = False)
		self.redraw()
		self._demoGfxCountdown(init = True)
		self.printText("Lower cases:", line = 1)
		self.printText("abcdefghijklmnop", line = 2, redraw = False);
		self.printText("qrstuvwxyz", line = 3, redraw = False)
		self.redraw()
		self._demoGfxCountdown(5)
		self.printText("Upper cases:", line = 1)
		self.printText("ABCDEFGHIJKLMNOP", line = 2, redraw = False);
		self.printText("QRSTUVWXYZ", line = 3, redraw = False)
		self.redraw()
		self._demoGfxCountdown(5)

	def _demo6x8(self):
		self.clearScreen()
		self.setGfxMode()
		self.clearScreen(0)
		self.redraw()
		sleep(0.5)
		self.setGfxFont('6x8')
		#6x8 font ruler:  "---------------------"
		self.printText("The 6x8 font demo!")
		self.printText("A custom font in gfx", line = 2)
		self.printText("6px width, 8px height", line = 3)
		sleep(1.0)
		self.printText("Please wait...", line = 3)
		sleep(0.5)
		for i in range(WIDTH // self._gfxFont['width']):
			self.printText(">".rjust(i + 1, '='), line = 4)
			sleep(0.05)
		self.printText("Numbers:", line = 1)
		self.printText("0123456789-+=<>/", line = 2, redraw = False)
		self.printText("~!@#$%^&*()_,.;?", line = 3, redraw = False)
		self.redraw()
		self._demoGfxCountdown(init = True)
		self.printText("Lower cases:", line = 1)
		self.printText("abcdefghijklmnop", line = 2, redraw = False);
		self.printText("qrstuvwxyz", line = 3, redraw = False)
		self.redraw()
		self._demoGfxCountdown(5)
		self.printText("Upper cases:", line = 1)
		self.printText("ABCDEFGHIJKLMNOP", line = 2, redraw = False);
		self.printText("QRSTUVWXYZ", line = 3, redraw = False)
		self.redraw()
		self._demoGfxCountdown(5)

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

	def printText(self, text, line = 1, col = 1, fillChar = ' ', redraw = True): 
		"""Print a text at the given line and column. Missing character will be 
		filled with fillChar, default is space. If fillChar is None, then the text
		will be printed as-is"""
		if self._textMode:
			self._printText(text, line, col, fillChar)
		else:
			self._printGfxText(text, line, col, fillChar)
			if redraw:
				self.redraw()

	def setGfxFont(self, name):
		for s in self._gfxFonts:
			if s == name:
				self._gfxFont = self._gfxFonts[s]
	
	def listGfxFonts(self):
		for s in self._gfxFonts:
			print(s, end = '')
		print('')

	def clearTextLine(self, line):
		"""Clear given line of text by filling it with spaces"""
		self.printText('', line)

	def demo(self, option = "all"):
		self.init()
		self.backlight(True)

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
			self._demoCountdown(init = True, duration = 3)
			self._demoGfx()
			self._demo4x6()
			self._demo6x8()
			self.setTextMode()
			self.printText("Turn off in  s", line = 4, col = 2)
			for i in range(3, 0, -1):
				self.printText(str(i), line = 4, col = 14, fillChar = None)
				sleep(1.0)
			self.clearScreen()
			self.backlight(False)
		elif option == "gfx":
			self._demoGfx()
		elif option == "4x6":
			self._demo4x6()
		elif option == "6x8":
			self._demo6x8()

