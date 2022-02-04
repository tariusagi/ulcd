import sys

class BaseLCD:
	"""Base class for all LCDs"""

	def __init__(self, driver = "Base"):
		self._driver = driver

	def backlight(self, state):
		"""Set backlight on if state is True, or off if False."""
		raise NotImplementedError

	def setFreq(self, freq):
		"""Set communication frequency (speed) in Hz. Revert to default if None was
		given."""
		raise NotImplementedError

	def setWriteDelay(self, usec):
		"""Set delay between byte writes in microsec. Revert to default if None was
		given."""
		raise NotImplementedError

	def setTextMode(self):	
		raise NotImplementedError

	def setGfxMode(self):	
		raise NotImplementedError

	def setGfxFont(self, name):
		raise NotImplementedError

	def printText(self, text, line = 1, col = 1, fillChar = ' '): 
		"""Print a text at the given line and column. Missing character will be 
		filled with fillChar, default is space. If fillChar is None, then the text
		will be printed as-is"""
		raise NotImplementedError

	def clearTextLine(self, line):
		"""Clear given line of text by filling it with spaces"""
		raise NotImplementedError

	def clearScreen(self, pattern = 0): 
		"""Clear the entire screen, both text and graphic mode."""
		raise NotImplementedError

	def demo(self):
		"""Perform demonstration on supported LCD"""
		raise NotImplementedError

	def printParams(self):
		"""Print all LCD's parameters to stdout"""
		print("Driver:", self._driver)
