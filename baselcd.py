import sys

class BaseLCD:
	"""Base class for all LCDs"""

	def __init__(self, driver = "Base", 
			rs = None, en = None, rw = None, rst = None, bl = None,
			d0 = None, d1 = None, d2 = None, d3 = None, 
			d4 = None, d5 = None, d6 = None, d7 = None, 
			columns = None, lines = None, width = None, height = None):
		if rw is None:
			self.interface = "Parallel"
		else:
			self.interface = "SPI"
		if d0 is None:
			# 4 bits mode.
			self.bits = 4
		else:
			# 8 bits mode.
			selft.bits = 8
		self.d0 = d0 # Bit 0
		self.d1 = d1 # Bit 1
		self.d2 = d2 # Bit 2
		self.d3 = d3 # Bit 3
		self.d4 = d4 # Bit 4
		self.d5 = d5 # Bit 5
		self.d6 = d6 # Bit 6
		self.d7 = d7 # Bit 7
		self.driver = driver
		self.rs = rs # Register select
		self.en = en # Clock enable
		self.rw = rw # Read/Write
		self.rst = rst # Reset
		self.bl = bl # Backlight
		self.columns = columns # Max text columns
		self.lines = lines # Max text lines 
		self.width = width # Max width in pixels
		self.height = height # Max height in pixels

	def demo(self):
		"""Perform demonstration on supported LCD"""
		print("ERROR: Demo is not supported in base class", file = sys.stderr)
		return False

	def printParams(self):
		"""Print all LCD's parameters to stdout"""
		self.driver and print("Driver:", self.driver)
		self.interface and print("Interface:", self.interface)
		self.bits and print("Bits:", self.bits)
		self.rs and print("RS  = ", self.rs)
		self.en and print("EN  = ", self.en)
		self.rw and print("RW  = ", self.rw)
		self.rst and print("RST = ", self.rst)
		self.bl and print("BLA = ", self.bl)
		self.d0 and print("D0  = ", self.d0)
		self.d1 and print("D0  = ", self.d1)
		self.d2 and print("D0  = ", self.d2)
		self.d3 and print("D0  = ", self.d3)
		self.d4 and print("D0  = ", self.d4)
		self.d5 and print("D0  = ", self.d5)
		self.d6 and print("D0  = ", self.d6)
		self.d7 and print("D0  = ", self.d7)
		self.columns and print("Columns = ", self.columns)
		self.lines and print("Lines = ", self.lines)
		self.width and print("Width = ", self.width)
		self.height and print("Height = ", self.height)

