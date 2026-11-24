"""Initial anatomy for the continuously simulated articulated rider."""
import math

def extend_rider(body):
 states={p['id']:p for p in body['states'] if 'x' in p}
 def bent(a,b,offset):
  a,b=states[a],states[b];dx,dy=b['x']-a['x'],b['y']-a['y'];le=math.hypot(dx,dy)
  return ((a['x']+b['x'])/2-dy/le*offset,(a['y']+b['y'])/2+dx/le*offset)
 extras=[('LELBOW',*bent('SHOULDER','LHAND',1.2)),('RELBOW',*bent('SHOULDER','RHAND',-1.2)),('LKNEE',10,0),('RKNEE',10,0),('HEAD',5,-8.2)]
 for name,x,y in extras:body['states'].append(dict(id=name,type='CollisionPoint',x=x,y=y,friction=.1))
 body['parts'].update(LEFT_ARM=['SHOULDER','LELBOW','LHAND'],RIGHT_ARM=['SHOULDER','RELBOW','RHAND'],LEFT_LEG=['BUTT','LKNEE','LFOOT'],RIGHT_LEG=['BUTT','RKNEE','RFOOT'])
 return body
