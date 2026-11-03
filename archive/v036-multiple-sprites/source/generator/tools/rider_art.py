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
 # Thin reins run from each hand to the front of the runner.
 for hand in ['LHAND','RHAND']:out+=stroke([(L('X',idx[hand]),L('Y',idx[hand])),(L('X',idx['STRING']),L('Y',idx['STRING']))],.2)
 # Black trousers, white boots, black sleeves and white mittens.
 for part in ['LEFT_LEG','RIGHT_LEG','LEFT_ARM','RIGHT_ARM']:
  ids=[idx[x] for x in body['parts'][part]]
  for a,b in zip(ids,ids[1:]):out+=stroke([(L('X',a),L('Y',a)),(L('X',b),L('Y',b))],1.25)
  out+=frame(ids[-1],ids[-2])
  out+=path([(1,0),(0,0),(0,-.65)],1.05)+path([(1,0),(0,0),(0,-.65)],.65,'#ffffff')
 out+=frame(5,6)
 out+=path([(0,0),(V('art length'),0)],1.65)+path([(.2,0),(V('art length')-.2,0)],1.05,'#ffffff')
 # Scarf retains the existing flutter simulation and reference colors.
 scarf=['#3898ed','#00a51b','#ff5340']
 for i in range(6):
  a=idx['SCARF_'+str(i)];b=idx['SCARF_'+str(i+1)]
  out+=stroke([(L('X',a),L('Y',a)),(L('X',b),L('Y',b))],1.1,scarf[i%3])
 out+=frame(6,idx['HEAD'])
 # Oval face, black cap band, white crown and pompom.
 out+=path([(1.6,0),(3.5,0)],2.65)+path([(1.6,0),(3.5,0)],2.05,'#ffffff')
 out+=path([(2.65,-1.4),(2.65,1.4)],.65)
 out+=ring(3.35,0,1.45,.3,start=-90,end=90)
 out+=path([(3.35,-1.45),(3.35,1.45)],.6)
 out+=path([(4.9,0),(4.9,.01)],.85)
 out+=path([(2.05,-.65),(2.05,-.64)],.4)
 return out
