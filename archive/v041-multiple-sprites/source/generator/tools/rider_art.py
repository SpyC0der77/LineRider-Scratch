"""Clipped, bone-attached black and white rider artwork."""
import math

def draw_rider(api):
 globals().update(api)
 out=[]
 def stroke(points,width=0.3,ink='#000000'):
  seq=[color(ink),size(width*V('Zoom'))]
  for a,b in zip(points,points[1:]):seq.extend(worldline(*a,*b))
  return seq
 def frame(a,b):
  return [setv('art dx',L('X',b)-L('X',a)),setv('art dy',L('Y',b)-L('Y',a)),setv('art length',mathop('sqrt',V('art dx')*V('art dx')+V('art dy')*V('art dy'))),iff(cmp('lt',V('art length'),.001),[setv('art length',.001)]),setv('art ux',V('art dx')/V('art length')),setv('art uy',V('art dy')/V('art length')),setv('art x',L('X',a)),setv('art y',L('Y',a))]
 def pt(x,y):return (V('art x')+V('art ux')*x-V('art uy')*y,V('art y')+V('art uy')*x+V('art ux')*y)
 def path(coords,w=.3,c='#000000'):return stroke([pt(*p) for p in coords],w,c)
 def ring(x,y,r,w=.3,c='#000000',start=0,end=360):
  return path([(x+r*math.cos(math.radians(t)),y+r*math.sin(math.radians(t))) for t in range(start,end+1,15)],w,c)
 # White runner with black outlines and a curled nose.
 out+=frame(idx['TAIL'],idx['NOSE'])
 out+=path([(-1,0),(15,0)],.85)+path([(-1,0),(15,0)],.38,'#ffffff')
 out+=ring(13,-2.5,2.5,.75)+ring(13,-2.5,2.5,.28,'#ffffff')
 out+=path([(0,0),(0,-5),(-1,-5)],.65)+path([(0,0),(0,-5),(-1,-5)],.22,'#ffffff')
 out+=path([(0,-4),(13,0)],.3)
 # The rope meets the curled runner rather than extending into empty space.
 rope=pt(15.5,-2.5)
 out+=stroke([(L('X',idx['RHAND']),L('Y',idx['RHAND'])),rope],.18)
 def polygon(coords,fill='#ffffff',outline=.25):
  # Fill with clipped pen spans so artwork obeys the same canvas bounds.
  seq=[]
  low=min(y for x,y in coords);high=max(y for x,y in coords)
  for n in range(math.ceil((high-low)/.12)):
   y=low+(n+.5)*.12;cross=[]
   for (x1,y1),(x2,y2) in zip(coords,coords[1:]+coords[:1]):
    if min(y1,y2)<=y<max(y1,y2):cross.append(x1+(y-y1)*(x2-x1)/(y2-y1))
   cross.sort()
   for left,right in zip(cross[::2],cross[1::2]):seq+=path([(left,y),(right,y)],.14,fill)
  return seq+path(coords+[coords[0]],outline)
 # Each trouser leg is one straight taper from the seat to the ankle.
 # Knee simulation points remain available to the crash solver but do not draw.
 for foot in ['LFOOT','RFOOT']:
  out+=frame(5,idx[foot])
  out+=polygon([(0,-.68),(0,.68),(6.1,.43),(6.1,-.43)],'#000000',.16)
  out+=frame(idx[foot],5)
  out+=polygon([(1.35,-.5),(-.4,-.5),(-.4,1.35),(.12,1.35),(.55,.5),(1.35,.5)])
 # Broad white coat, black back edge and a straight black sleeve.
 out+=frame(5,6)
 out+=polygon([(-.1,-.65),(5.8,-.65),(5.8,.95),(.2,.75)],'#ffffff',.24)
 out+=path([(.1,-.62),(5.7,-.62)],.48)
 for hand in ['LHAND','RHAND']:
  out+=stroke([(L('X',6),L('Y',6)),(L('X',idx[hand]),L('Y',idx[hand]))],1.3)
  out+=frame(idx[hand],6)
  out+=polygon([(1.25,-.57),(-.15,-.57),(-.4,-.3),(-.4,.35),(-.12,.55),(1.25,.55)],'#ffffff',.22)
 # Scarf retains the existing flutter simulation and reference colors.
 scarf=['#3898ed','#00a51b','#ff5340']
 for i in range(6):
  a=idx['SCARF_'+str(i)];b=idx['SCARF_'+str(i+1)]
  out+=stroke([(L('X',a),L('Y',a)),(L('X',a)+(L('X',b)-L('X',a))*.45,L('Y',a)+(L('Y',b)-L('Y',a))*.45)],1.05,scarf[i%3])
 out+=frame(6,idx['HEAD'])
 # Face sits below the brim; one broad black band and a white dome.
 out+=path([(1.35,0),(2.8,0)],2.5)+path([(1.35,0),(2.8,0)],2.0,'#ffffff')
 out+=path([(1.8,.55),(1.8,.56)],.4)
 # Positive transverse coordinates face forward; hair hangs at the back.
 out+=path([(.9,-.95),(3.05,-.95)],.85)
 out+=ring(3.2,0,1.45,.26,start=-90,end=90)
 out+=path([(3.2,-1.45),(3.2,1.45)],.65)
 out+=path([(4.8,0),(4.8,.01)],.8)
 return out
