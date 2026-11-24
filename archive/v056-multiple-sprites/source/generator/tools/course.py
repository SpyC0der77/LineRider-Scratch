"""A launch bowl followed by a sloping sled catch and runout."""
import math

def course_height(x):
 return 28+.4*x+44*math.exp(-((x-350)/58)**2)

DEFAULT_GOAL=(1050,course_height(1050))

def default_track():
 return [(x,course_height(x),x+4,course_height(x+4),0) for x in range(-100,1152,4)]
