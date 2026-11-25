"""Original mounted rider physics and the pose points used to draw the rider."""

import math


def extend_rider(body):
    states = {point['id']: point for point in body['states'] if 'x' in point}

    def bent(start, end, offset):
        a, b = states[start], states[end]
        dx, dy = b['x'] - a['x'], b['y'] - a['y']
        length = math.hypot(dx, dy)
        return (a['x'] + b['x']) / 2 - dy / length * offset, (a['y'] + b['y']) / 2 + dx / length * offset

    extra_points = [
        ('LELBOW', *bent('SHOULDER', 'LHAND', 1.2)),
        ('RELBOW', *bent('SHOULDER', 'RHAND', -1.2)),
        ('LKNEE', 10, 0), ('RKNEE', 10, 0), ('HEAD', 5, -8.2),
    ]
    for name, x, y in extra_points:
        body['states'].append(dict(id=name, type='CollisionPoint', x=x, y=y, friction=.1))
    return body


def install(api):
    globals().update(api)
    i, j = V('i'), V('j')
    lists['Initial air'] = ['Initial air', lists['Air'][1][:]]
    proc('reset rider', [
        setv('i', 1),
        loop(len(pts), [
            replace('X', i, L('Initial X', i) + V('Spawn X')),
            replace('Y', i, L('Initial Y', i) + V('Spawn Y')),
            replace('PX', i, L('Initial X', i) + V('Spawn X') - .4),
            replace('PY', i, L('Initial Y', i) + V('Spawn Y')),
            replace('VX', i, .4), replace('VY', i, 0),
            replace('Air', i, L('Initial air', i)), change('i', 1),
        ]),
        setv('Mounted', 1), setv('Frame', 0), call('update rider pose'),
    ])
    dx, dy, distance, diff = V('dx'), V('dy'), V('distance'), V('diff')
    # The first 17 points are physical, including the scarf. Indices and the
    # build-time Air values are literals; (1 - air) stays an explicit operator.
    integrate = []
    for k in range(1, 18):
        drag = op('subtract', 1, lists['Air'][1][k - 1])
        integrate += [
            setv('vx', (L('X', k) - L('PX', k)) * drag),
            setv('vy', (L('Y', k) - L('PY', k)) * drag + .175),
            replace('VX', k, V('vx')), replace('VY', k, V('vy')),
            replace('PX', k, L('X', k)), replace('PY', k, L('Y', k)),
            replace('X', k, L('X', k) + V('vx')), replace('Y', k, L('Y', k) + V('vy')),
        ]
    proc('integrate points', integrate)

    def solve_stick(n):
        # Stick constraint n (0-based) with its build-time endpoints, kind and endurance as literals.
        a, b = lists['CA'][1][n], lists['CB'][1][n]
        rest, kind, endurance = lists['Rest'][1][n], lists['Kind'][1][n], lists['Endurance'][1][n]
        move = [
            replace('X', a, L('X', a) - dx * diff),
            replace('Y', a, L('Y', a) - dy * diff),
            replace('X', b, L('X', b) + dx * diff),
            replace('Y', b, L('Y', b) + dy * diff),
        ]
        relax = [setv('diff', (distance - rest) / distance * .5)]
        if kind == 0:
            body = relax + move
        elif kind == 1:
            body = relax + [iff(cmp('gt', diff, endurance), [setv('Mounted', 0)], move)]
        else:
            body = relax + [iff(cmp('lt', distance, rest), move)]
        block = [
            setv('dx', L('X', a) - L('X', b)), setv('dy', L('Y', a) - L('Y', b)),
            setv('distance', mathop('sqrt', dx * dx + dy * dy)),
            iff(cmp('gt', distance, 0), body),
        ]
        # Bind sticks stop applying once the rider is detached.
        if kind == 1:
            block = [iff(cmp('equals', V('Mounted'), 1), block)]
        return block

    solve = []
    for n in range(len(lists['CA'][1])):
        solve += solve_stick(n)
    proc('solve sticks', solve)

    nx, ny, material = L('NX', j), L('NY', j), L('Material', j)
    ox, oy, depth, along = V('ox'), V('oy'), V('depth'), V('along')
    fx, fy, friction = V('fx'), V('fy'), V('friction factor')
    tangent_speed = V('tangent speed')
    resolve_contact = [
        replace('X', i, L('X', i) - nx * depth), replace('Y', i, L('Y', i) - ny * depth),
        setv('friction factor', 1),
        iff(cmp('equals', material, 2), [setv('friction factor', 0)]),
        setv('fx', ny * L('Friction', i) * friction * depth),
        setv('fy', 0 - nx * L('Friction', i) * friction * depth),
        iff(cmp('gt', L('PX', i), L('X', i) - .0000001), [setv('fx', 0 - fx)]),
        iff(cmp('lt', L('PY', i), L('Y', i)), [setv('fy', 0 - fy)]),
        replace('PX', i, L('PX', i) + fx), replace('PY', i, L('PY', i) + fy),
        iff(cmp('equals', material, 1), [
            setv('tangent speed', (L('X', i) - L('PX', i)) * ny - (L('Y', i) - L('PY', i)) * nx),
            replace('PX', i, L('PX', i) + ny * tangent_speed * .08),
            replace('PY', i, L('PY', i) - nx * tangent_speed * .08),
        ]),
    ]
    # Match lr-core's directed acceleration impulse.
    for material_id, direction in [(4, 1), (5, -1)]:
        resolve_contact.append(iff(cmp('equals', material, material_id), [
            replace('PX', i, L('PX', i) - ny * .1 * direction),
            replace('PY', i, L('PY', i) + nx * .1 * direction),
            setv('Frame boost', 1),
        ]))
    # Refresh the cached point position after every resolve so later candidates see it.
    resolve_contact += [setv('point x', L('X', i)), setv('point y', L('Y', i))]
    contact = [
        setv('ox', V('point x') - L('LX', j)), setv('oy', V('point y') - L('LY', j)),
        setv('depth', ox * nx + oy * ny),
        # Scratch evaluates both operands of and/or, so nest the tests to skip later work.
        iff(cmp('gt', depth, 0), [
            iff(cmp('lt', depth, 10), [
                setv('along', (ox * L('DX', j) + oy * L('DY', j)) * L('InvSq', j)),
                iff(cmp('gt', along, -.000001), [
                    iff(cmp('lt', along, 1.000001), [
                        iff(cmp('gt', nx * L('VX', i) + ny * L('VY', i), 0), resolve_contact),
                    ]),
                ]),
            ]),
        ]),
    ]
    proc('collide points with lines', [
        setv('i', 1),
        loop(10, [
            call('nearby lines'),
            setv('point x', L('X', i)), setv('point y', L('Y', i)),
            setv('k', 1),
            loop(length('Candidates'), [
                setv('j', L('Candidates', V('k'))),
                iff(NOT(cmp('equals', material, 3)), contact), change('k', 1),
            ]),
            change('i', 1),
        ]),
    ])

    finish = []
    for constraint in body['constraints']:
        if constraint['type'] == 'BindJoint' and constraint['binding'] == 'RIDER_MOUNTED':
            a, b, q, r = [idx[constraint[k]] for k in ('p1', 'p2', 'q1', 'q2')]
            cross = (L('X', b) - L('X', a)) * (L('Y', r) - L('Y', q)) - (L('Y', b) - L('Y', a)) * (L('X', r) - L('X', q))
            finish.append(iff(cmp('lt', cross, 0), [setv('Mounted', 0)]))
    scarf = [idx[name] for name in body['parts']['SCARF']]
    for a, b in zip(scarf, scarf[1:]):
        rest = math.hypot(pts[a-1]['x'] - pts[b-1]['x'], pts[a-1]['y'] - pts[b-1]['y'])
        finish += [
            setv('dx', L('X', a) - L('X', b)), setv('dy', L('Y', a) - L('Y', b)),
            setv('distance', mathop('sqrt', dx * dx + dy * dy)),
            iff(cmp('gt', distance, 0), [
                setv('diff', (distance - rest) / distance),
                replace('X', b, L('X', b) + dx * diff), replace('Y', b, L('Y', b) + dy * diff),
            ]),
        ]
    proc('finish frame', finish)

    pose = []
    pose_dx, pose_dy, pose_length = V('pose dx'), V('pose dy'), V('pose length')
    for horizontal, vertical in [('X', 'Y'), ('PX', 'PY')]:
        for dest, a, b, bend in [(18, 6, 8, 1.2), (19, 6, 7, -1.2), (20, 5, 9, -math.sqrt(12.5)), (21, 5, 10, -math.sqrt(12.5))]:
            pose += [
                setv('pose dx', L(horizontal, b) - L(horizontal, a)),
                setv('pose dy', L(vertical, b) - L(vertical, a)),
                setv('pose length', mathop('sqrt', pose_dx * pose_dx + pose_dy * pose_dy)),
                iff(cmp('lt', pose_length, .001), [setv('pose length', .001)]),
                replace(horizontal, dest, (L(horizontal, a) + L(horizontal, b)) / 2 - pose_dy / pose_length * bend),
                replace(vertical, dest, (L(vertical, a) + L(vertical, b)) / 2 + pose_dx / pose_length * bend),
            ]
        pose += [
            setv('pose dx', L(horizontal, 6) - L(horizontal, 5)),
            setv('pose dy', L(vertical, 6) - L(vertical, 5)),
            setv('pose length', mathop('sqrt', pose_dx * pose_dx + pose_dy * pose_dy)),
            iff(cmp('lt', pose_length, .001), [setv('pose length', .001)]),
            replace(horizontal, 22, L(horizontal, 6) + pose_dx / pose_length * 2.7),
            replace(vertical, 22, L(vertical, 6) + pose_dy / pose_length * 2.7),
        ]
    proc('update rider pose', pose)
    proc('physics frame', [
        call('integrate points'),
        loop(6, [call('solve sticks'), call('collide points with lines')]),
        call('finish frame'), call('update rider pose'), change('Frame', 1),
    ])
