import contact_reference as m
from course import default_track
r=m.run(default_track());a=r[59];x,y=a['x'],a['y'];u,v=(x[2]-x[1])/15,(y[2]-y[1])/15
print([(i+1,round((x[i]-x[0])*u+(y[i]-y[0])*v,2),round((y[i]-y[0])*u-(x[i]-x[0])*v,2)) for i in [4,5,6,7,8,9,21,22]])
