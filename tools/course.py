"""Long rolling descent with broad bowls and progressively larger hills."""
import math


def course_height(x):
 return 28 + .24*x + 18*math.sin(x/180) + 32*(1-math.cos(x/300)) + 12*(1-math.cos(x/95))

DEFAULT_SPAWN=(0,0)
DEFAULT_GOAL=(3100,course_height(3100))


def default_track():
 xs=range(-100,3201,8)
 return [(x,course_height(x),x+8,course_height(x+8),0) for x in xs if x<3200]
