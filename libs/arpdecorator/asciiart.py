
import random, importlib
from functools import wraps

from arpdecorator.elements import RANDOM_ART, RANDOM_TEXT
# importlib.reload(RANDOM_ART)
# importlib.reload(RANDOM_TEXT)

def surprise_art():
		# Restore the original selection
		# Get a RANDOM index from the list
		RANDOM_ART_index = random.randint(0, len(RANDOM_ART) - 1)

		# Retrieve the element at the RANDOM index
		RANDOM_string = RANDOM_ART[RANDOM_ART_index]
		print(RANDOM_string)


def draw_random_art(func):
		"""
		A decorator to save the current selection, run a function, and restore the selection afterward.
		"""
		@wraps(func)
		def wrapper(*args, **kwargs):
				# Get the current selection
				RANDOM_TEXT
				# Get a RANDOM index from the list
				RANDOM_TEXT_index = random.randint(0, len(RANDOM_TEXT) - 1)

				# Retrieve the element at the RANDOM index
				RANDOM_string = RANDOM_TEXT[RANDOM_TEXT_index]
				print(RANDOM_string)
				try:
					# Run the decorated function
					return func(*args, **kwargs)
				finally:
					pass
		return wrapper