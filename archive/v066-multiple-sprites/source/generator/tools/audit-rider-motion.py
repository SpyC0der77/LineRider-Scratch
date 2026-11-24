"""Measure rider anomalies without changing the delivered physics or course."""
import hashlib
import json
import math
from pathlib import Path

import contact_reference as m
from course import default_track

OUT = Path('artifacts/extra-qa')
OUT.mkdir(parents=True, exist_ok=True)
BODY = [4, 5, 6, 7, 8, 9, 17, 18, 19, 20, 21]
original_reset = m.p['reset rider']
case = {}


def reset():
    m.v['Spawn X'] += case.get('x', 0)
    m.v['Spawn Y'] += case.get('y', 0)
    original_reset()
    dv = case.get('vx', 0)
    for i in range(len(m.l['PX'])):
        m.l['PX'][i] -= dv


m.p['reset rider'] = reset


def local(row, i, origin=4):
    x, y = row['x'], row['y']
    u, v = (x[2] - x[1]) / 15, (y[2] - y[1]) / 15
    return ((x[i] - x[origin]) * u + (y[i] - y[origin]) * v,
            (y[i] - y[origin]) * u - (x[i] - x[origin]) * v)


def analyze(rows):
    bone_errors = []
    step_changes = []
    for row in rows:
        for a, b, rest, kind in zip(m.l['Bone A'], m.l['Bone B'], m.l['Bone rest'], m.l['Bone kind']):
            if kind != 0:
                continue
            distance = math.hypot(row['x'][a-1] - row['x'][b-1], row['y'][a-1] - row['y'][b-1])
            bone_errors.append(dict(frame=row['frame'], a=a, b=b, rest=rest,
                                    distance=distance, relative_error=abs(distance/rest - 1)))
    for before, after in zip(rows, rows[1:]):
        for i in BODY:
            step_changes.append(dict(frame=after['frame'], point=i+1,
                                     local_step=math.dist(local(before, i), local(after, i))))
    grip_frames = [row['frame'] for row in rows if max(row['grips']) > 1e-7]
    free = []
    for row in rows:
        hip = local(row, 4, 0)
        if (math.hypot(hip[0]-5, hip[1]) > 5
                and max(row['contacts'][i] for i in BODY) < 1e-7
                and max(row['ground'][i] for i in BODY) < 1e-7
                and max(row['grips']) < 1e-7):
            free.append(row['frame'])
    foot_rows = [dict(frame=row['frame'], left=local(row, 8)[0], right=local(row, 9)[0], mounted=row['m'])
                 for row in rows if row['frame'] >= 130]
    # A fully restored leg pose must persist through the remainder of the run.
    settled = next((r['frame'] for i, r in enumerate(foot_rows)
                    if all(4 < q['left'] < 6 and 4 < q['right'] < 6 for q in foot_rows[i:])), None)
    at60 = rows[min(59, len(rows)-1)]
    rope_distances = [math.dist((at60['x'][i], at60['y'][i]),
                               (at60['x'][22], at60['y'][22])) for i in [6, 7]]
    return dict(end_state=rows[-1]['state'], end_frame=rows[-1]['frame'],
                finite=all(math.isfinite(z) for r in rows for axis in ['x', 'y'] for z in r[axis]),
                whole_body_free_frames=free, grip_frames=grip_frames,
                hand_to_rope_distance_at_60=rope_distances, leg_pose_settles_at=settled,
                worst_bone_errors=sorted(bone_errors, key=lambda r:r['relative_error'], reverse=True)[:12],
                largest_local_steps=sorted(step_changes, key=lambda r:r['local_step'], reverse=True)[:20],
                post_landing_feet=foot_rows)


rows = m.run(default_track(), 400)
baseline = analyze(rows)
digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
repeats = []
for _ in range(2):
    repeat = m.run(default_track(), 400)
    repeats.append(hashlib.sha256(json.dumps(repeat, sort_keys=True).encode()).hexdigest() == digest)

variations = []
for field, deltas in [('x', [-.1, -.01, .01, .1]), ('y', [-.1, -.01, .01, .1]),
                      ('vx', [-.001, .001])]:
    for delta in deltas:
        case = {field:delta}
        run = m.run(default_track(), 400)
        variations.append(dict(field=field, delta=delta, state=run[-1]['state'], frame=run[-1]['frame']))

report = dict(baseline=baseline, repeated_runs_identical=repeats, spawn_sensitivity=variations)
(OUT/'motion-audit.json').write_text(json.dumps(report, indent=2))
(OUT/'baseline-particles.json').write_text(json.dumps(rows))
print(json.dumps({k:v for k,v in baseline.items() if k not in ['post_landing_feet', 'largest_local_steps', 'worst_bone_errors']}, indent=2))
print('Largest bone error:', baseline['worst_bone_errors'][0])
print('Largest local step:', baseline['largest_local_steps'][0])
print('Repeated runs identical:', repeats)
print('Start variations:', variations)
