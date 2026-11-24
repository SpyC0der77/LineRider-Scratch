"""A physical launch lip, short drop, and braked catch runway."""

def approach_height(x):
 return 28+.3*x

def course_height(x):
 return approach_height(x) if x<=350 else approach_height(350)+8+.3*(x-350)

DEFAULT_SPAWN=(0,approach_height(0)-6)
DEFAULT_GOAL=(1050,course_height(1050))

def default_track():
 xs=list(range(-100,350,4))+[350]
 lines=[(a,approach_height(a),b,approach_height(b),0) for a,b in zip(xs,xs[1:])]
 # This upward-oriented lip contacts the sled runner before the rider reaches it.
 lines.append((350,approach_height(350)+1,350,approach_height(350)-.1,0))
 # Reverse boost slows the sled just enough for the airborne rider to meet it.
 lines += [(x,course_height(x),x+4,course_height(x+4),5 if 392<=x<408 else 0) for x in range(354,1200,4)]
 return lines
