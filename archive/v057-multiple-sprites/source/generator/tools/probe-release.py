import physics_model as m
from course import default_track
original=m.p['reset rider']
def reset():original();m.v.update({'Release duration':8,'Release compression':.8,'Binding mass':.1})
m.p['reset rider']=reset
r=m.run(default_track())
print('end',r[-1]['frame'],m.v['Landing error']);print([(a['frame'],a['release'],a['landing'],round(a['h'],1),round(a['a'],1),round((a['x'][2]-a['x'][1])/15,2),round(a['x'][4]),round(a['y'][4])) for a in r if a['release']==1 or a['landing']==2 or a['frame']%10==0 and a['frame']>=110 or a['state']==3]);print([(i+1,c) for i,c in enumerate(m.l['R contact depth']) if c>.05])
