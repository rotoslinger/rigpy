import random

from rpdecorator import asciiart
def surprise_art():
    # Restore the original selection
    # Get a RANDOM index from the list
    RANDOM_ART_index = random.randint(0, len(asciiart.RANDOM_ART) - 1)

    # Retrieve the element at the RANDOM index
    RANDOM_string = asciiart.RANDOM_ART[RANDOM_ART_index]
    print(RANDOM_string)
surprise_art()