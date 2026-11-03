"""A continuous all-normal descent with a rounded dip that unseats the rider."""
import math

def course_height(x):
 return 28+.30*x+35*math.sin(x/140)+25*math.exp(-((x-350)/35)**2)

DEFAULT_GOAL=(700,course_height(700))

def default_track():
 # The same smooth function defines every endpoint. Finer sampling around the dip
 # preserves its curvature; there are no gaps, vertical stops or overlapping barriers.
 xs=sorted(set(list(range(-100,241,20))+list(range(240,461,2))+list(range(460,721,20))))
 return [(x,course_height(x),xx,course_height(xx),0) for x,xx in zip(xs,xs[1:])]
