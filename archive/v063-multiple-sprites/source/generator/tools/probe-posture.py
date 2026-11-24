import contact_reference as m
from course import default_track
orig=m.p['reset rider']
def reset():orig();m.v['Posture spring']=.05
m.p['reset rider']=reset;r=m.run(default_track())
print([(a['frame'],round(a['x'][0]),round(a['x'][4]),round(a['y'][0]),round(a['y'][4]),round(a['h'],1),round(a['a'],1)) for a in r if a['frame']%5==0 and a['frame']>=100]);print([(i+1,c) for i,c in enumerate(m.l['Ground contact']) if c>.05])
