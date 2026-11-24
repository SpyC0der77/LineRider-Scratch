import contact_reference as m
from course import default_track
r=m.run(default_track());print([(a['frame'],round(a['h'],3),round(a['load'],3),round(a['x'][4],2),round(a['y'][4],2)) for a in r[:20]])
