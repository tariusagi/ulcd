import sys

class BaseLCD:
	"""Base class for all LCDs"""

	def __init__(self, driver = "Base", 
			rs = None, e = None, rw = None, rst = None, bla = None,
			d0 = None, d1 = None, d2 = None, d3 = None, 
			d4 = None, d5 = None, d6 = None, d7 = None, 
			columns = None, lines = None, width = None, height = None):
		if rw is None:
			self._interface = "Parallel"
		else:
			self._interface = "SPI"
		if d0 is None:
			# 4 bits mode.
			self._bits = 4
		else:
			# 8 bits mode.
			selft.bits = 8
		self._d0 = d0 # Bit 0
		self._d1 = d1 # Bit 1
		self._d2 = d2 # Bit 2
		self._d3 = d3 # Bit 3
		self._d4 = d4 # Bit 4
		self._d5 = d5 # Bit 5
		self._d6 = d6 # Bit 6
		self._d7 = d7 # Bit 7
		self._driver = driver
		self._rs = rs # Register select
		self._e = e # Clock enable
		self._rw = rw # Read/Write
		self._rst = rst # Reset
		self._bla = bla # Backlight anode
		self._maxCols = columns # Max text columns
		self._maxLines = lines # Max text lines 
		self._width = width # Max width in pixels
		self._height = height # Max height in pixels
		self._backlight = False

	def backlight(self, state):
		"""Set backlight on if state is True, or off if False. The real operation
		must be implemented by child classes"""
		self._backlight = state

	def demo(self):
		"""Perform demonstration on supported LCD"""
		print("ERROR: Demo is not supported in base class", file = sys.stderr)
		return False

	def printParams(self):
		"""Print all LCD's parameters to stdout"""
		self._driver and print("Driver:", self._driver)
		self._interface and print("Interface:", self._interface)
		self._bits and print("Bits:", self._bits)
		self._rs and print("RS  = ", self._rs)
		self._e and print("EN  = ", self._e)
		self._rw and print("RW  = ", self._rw)
		self._rst and print("RST = ", self._rst)
		self._bla and print("BLA = ", self._bla)
		self._d0 and print("D0  = ", self._d0)
		self._d1 and print("D0  = ", self._d1)
		self._d2 and print("D0  = ", self._d2)
		self._d3 and print("D0  = ", self._d3)
		self._d4 and print("D0  = ", self._d4)
		self._d5 and print("D0  = ", self._d5)
		self._d6 and print("D0  = ", self._d6)
		self._d7 and print("D0  = ", self._d7)
		self._maxCols and print("Columns = ", self._maxCols)
		self._maxLines and print("Lines = ", self._maxLines)
		self._width and print("Width = ", self._width)
		self._height and print("Height = ", self._height)

