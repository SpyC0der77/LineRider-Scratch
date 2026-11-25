"""Precompute the ride in native Scratch and display it at an independent playhead."""

# Positions are cached per frame. Velocities are not: integrate points rebuilds
# them from the restored positions before collisions read them.
CACHE_LISTS = ('X', 'Y', 'PX', 'PY')
SOLVER_LISTS = CACHE_LISTS + ('VX', 'VY')
CACHE_VARIABLES = ('Ride result', 'Mounted')
# Per frame, the bounding box of grid cells queried by collisions. A line can
# only influence a frame if one of its cells falls inside that box.
CELL_BOUNDS = ('Cell X0', 'Cell X1', 'Cell Y0', 'Cell Y1')
DIRTY_BOUNDS = (('X0', 'MinX'), ('X1', 'MaxX'), ('Y0', 'MinY'), ('Y1', 'MaxY'))
SNAPSHOT = ('Spawn X', 'Spawn Y', 'Goal X', 'Goal Y', 'Goal enabled', 'Lowest track', 'Timeline detach frame')
CANVAS_BOTTOM = -130
RAIL_LEFT = -226
RAIL_RIGHT = 68
# Wall-clock work allowed per editor tick while the ride timeline is computed.
TIMELINE_BUDGET_MS = 60


def simulation_api(api):
    """Give the solver its own position and result data while the editor shows a frame."""
    def variable(name):
        if name == 'State':
            name = 'Ride result'
        if name in CACHE_VARIABLES or name == 'Frame':
            return 'Physics ' + name
        return name

    def points(name):
        return 'Physics ' + name if name in SOLVER_LISTS else name

    return {
        **api,
        'V': lambda name: api['V'](variable(name)),
        'setv': lambda name, value: api['setv'](variable(name), value),
        'change': lambda name, value: api['change'](variable(name), value),
        'L': lambda name, index: api['L'](points(name), index),
        'replace': lambda name, index, value: api['replace'](points(name), index, value),
    }


def define_result_check(api):
    V, L, proc, iff, cmp, OR, AND, NOT, setv, mathop = (
        api[name] for name in ('V', 'L', 'proc', 'iff', 'cmp', 'OR', 'AND', 'NOT', 'setv', 'mathop')
    )
    # Use the hip's crossing of the goal flag, in either direction. Interpolation
    # keeps fast passes accurate and avoids treating a flag behind the spawn as a win.
    hip_x = L('X', 5)
    hip_y = L('Y', 5)
    goal_x = V('Goal X')
    previous_x = V('Previous hip X')
    previous_y = V('Previous hip Y')
    proc('check result', [
        iff(OR(
            cmp('equals', V('Mounted'), 0),
            OR(cmp('gt', hip_y, V('Lowest track') + 160), cmp('gt', mathop('abs', hip_x), 30000)),
        ), [setv('State', 3)], [
            iff(AND(
                AND(cmp('equals', V('Mounted'), 1), cmp('equals', V('Goal enabled'), 1)),
                NOT(cmp('gt', (previous_x - goal_x) * (hip_x - goal_x), 0)),
            ), [
                setv('Goal crossing Y', hip_y),
                iff(NOT(cmp('equals', hip_x, previous_x)), [
                    setv('Goal crossing Y', previous_y + (hip_y - previous_y) * (goal_x - previous_x) / (hip_x - previous_x)),
                ]),
                iff(cmp('lt', mathop('abs', V('Goal crossing Y') - V('Goal Y')), 30), [
                    setv('State', 4),
                ]),
            ]),
        ]),
    ])


def mark_box(api, read):
    """Union one line's padded AABB into the dirty box. read(field) gives its value."""
    V, setv, iff, cmp = (api[name] for name in ('V', 'setv', 'iff', 'cmp'))
    grow = []
    for bound, field in DIRTY_BOUNDS:
        test = 'lt' if bound.endswith('0') else 'gt'
        grow.append(iff(cmp(test, read(field), V('Timeline dirty ' + bound)),
                        [setv('Timeline dirty ' + bound, read(field))]))
    return [
        iff(cmp('equals', V('Timeline dirty'), 0),
            [setv('Timeline dirty ' + bound, read(field)) for bound, field in DIRTY_BOUNDS] + [setv('Timeline dirty', 1)],
            grow),
    ]


def mark_line(api, index, delta):
    """Record a line added or about to be removed so the cache before it survives."""
    V, change = api['V'], api['change']
    L = api['L']
    return mark_box(api, lambda field: L(field, index)) + [change('Timeline expected lines', delta)]


def mark_restore(api, prefix, fields, cap=400):
    """Before a snapshot replaces the track, dirty only the lines that differ.

    Survivors are the common prefix and suffix, which keep their relative order.
    Snapshot line i (1-based) lives at list index 'snap base' + i in '<prefix> <field>'.
    """
    V, L, setv, iff, cmp, change, loop, until = (
        api[name] for name in ('V', 'L', 'setv', 'iff', 'cmp', 'change', 'loop', 'until'))
    AND, OR, NOT, length = api['AND'], api['OR'], api['NOT'], api['length']
    count_name = prefix + ' Count'

    def same(cur, snap):
        out = None
        for field in fields:
            term = cmp('equals', L(field, cur), L(prefix + ' ' + field, snap))
            out = term if out is None else AND(out, term)
        return out

    cur = V('snap cur')
    new = V('snap count')
    base = V('snap base')
    prefix_n = V('snap prefix')
    suffix_n = V('snap suffix')
    index = V('snap i')
    return [
        setv('snap count', L(count_name, length(count_name))),
        setv('snap base', length(prefix + ' LX') - new),
        setv('snap cur', length('LX')),
        setv('snap min', cur),
        iff(cmp('gt', cur, new), [setv('snap min', new)]),
        setv('snap prefix', 0),
        until(OR(cmp('equals', prefix_n, V('snap min')),
                 NOT(same(prefix_n + 1, base + prefix_n + 1))), [change('snap prefix', 1)]),
        setv('snap suffix', 0),
        until(OR(cmp('equals', suffix_n, V('snap min') - prefix_n),
                 NOT(same(cur - suffix_n, base + new - suffix_n))), [change('snap suffix', 1)]),
        setv('snap cur mid', cur - prefix_n - suffix_n),
        setv('snap new mid', new - prefix_n - suffix_n),
        iff(cmp('gt', V('snap cur mid') + V('snap new mid'), cap), mark_all(api), [
            setv('snap i', prefix_n + 1),
            loop(V('snap cur mid'), mark_box(api, lambda field: L(field, index)) + [change('snap i', 1)]),
            setv('snap i', base + prefix_n + 1),
            loop(V('snap new mid'), mark_box(api, lambda field: L(prefix + ' ' + field, index)) + [change('snap i', 1)]),
        ]),
        change('Timeline expected lines', new - length('LX')),
    ]


def mark_all(api):
    return [api['setv']('Timeline dirty all', 1)]


def reset_frame_cells(api):
    setv = api['setv']
    return [setv('Candidates key', 'none'), setv('Frame cell X0', 1e9), setv('Frame cell X1', -1e9),
            setv('Frame cell Y0', 1e9), setv('Frame cell Y1', -1e9)]


def track_frame_cells(api):
    """Called with grid gx/gy on each collision query that rebuilds candidates."""
    V, setv, iff, cmp = (api[name] for name in ('V', 'setv', 'iff', 'cmp'))
    out = []
    for axis, cell in (('X', 'grid gx'), ('Y', 'grid gy')):
        out.append(iff(cmp('lt', V(cell), V('Frame cell ' + axis + '0')), [setv('Frame cell ' + axis + '0', V(cell))]))
        out.append(iff(cmp('gt', V(cell), V('Frame cell ' + axis + '1')), [setv('Frame cell ' + axis + '1', V(cell))]))
    return out


def install(api):
    globals().update(api)
    point_count = len(pts)
    # Scratch lists hold at most 200,000 items. Frame zero occupies the first row.
    last_storable_frame = 200_000 // point_count - 1
    for name in SOLVER_LISTS:
        lists['Physics ' + name] = ['Physics ' + name, lists[name][1][:]]
    for name in CACHE_LISTS + CACHE_VARIABLES + CELL_BOUNDS:
        lists['Timeline ' + name] = ['Timeline ' + name, []]

    point = V('Timeline point')
    offset = V('Timeline index')
    physics_frame = V('Physics Frame')
    end = V('Timeline end')
    ready = V('Timeline ready')
    target = V('Timeline target')
    result = V('Ride result')
    physics_result = V('Physics Ride result')
    requested_detach = V('Timeline detach frame')

    proc('record timeline frame', [
        setv('Timeline point', 1),
        loop(point_count, [
            add('Timeline ' + name, L('Physics ' + name, point))
            for name in CACHE_LISTS
        ] + [change('Timeline point', 1)]),
    ] + [add('Timeline ' + name, V('Physics ' + name)) for name in CACHE_VARIABLES]
      + [add('Timeline ' + name, V('Frame ' + name.replace('Cell', 'cell'))) for name in CELL_BOUNDS])

    define_result_check(simulation_api(api))
    hip_x = L('Physics X', 5)
    hip_y = L('Physics Y', 5)

    # Frames before the first one an edit can influence are kept, and the
    # solver resumes from the last kept frame. Physics is sequential, so a
    # frame after an influenced one cannot be computed before it.
    resume = V('Timeline resume')
    scan = V('Timeline scan')
    def first_frame(condition):
        return [setv('Timeline scan', 1), until(NOT(cmp('lt', scan, resume)), [
            iff(condition, [setv('Timeline resume', scan)]), change('Timeline scan', 1),
        ])]
    def frame_value(name, frame_offset):
        return L('Timeline ' + name, scan + frame_offset + 1)
    def hip(name, frame_offset):
        return L('Timeline ' + name, (scan + frame_offset) * point_count + 5)
    def changed(name):
        return NOT(cmp('equals', V(name), V('Timeline used ' + name)))
    def crosses(goal):
        return NOT(cmp('gt', (hip('X', -1) - goal) * (hip('X', 0) - goal), 0))
    dirty_cells = [setv('Timeline dirty g' + bound, mathop('floor', V('Timeline dirty ' + bound) / 64)) for bound, _ in DIRTY_BOUNDS]
    overlaps = AND(
        AND(NOT(cmp('gt', frame_value('Cell X0', 0), V('Timeline dirty gX1'))),
            NOT(cmp('lt', frame_value('Cell X1', 0), V('Timeline dirty gX0')))),
        AND(NOT(cmp('gt', frame_value('Cell Y0', 0), V('Timeline dirty gY1'))),
            NOT(cmp('lt', frame_value('Cell Y1', 0), V('Timeline dirty gY0')))),
    )
    lowest = V('Timeline lowest threshold')
    proc('resolve timeline resume', [
        setv('Timeline resume', end + 1),
        iff(OR(OR(cmp('equals', length('Timeline Ride result'), 0), cmp('equals', V('Timeline dirty all'), 1)),
               OR(OR(changed('Spawn X'), changed('Spawn Y')),
                  NOT(cmp('equals', length('LX'), V('Timeline expected lines'))))), [
            setv('Timeline resume', 0),
        ]),
        iff(AND(cmp('equals', V('Timeline dirty'), 1), cmp('gt', resume, 1)),
            dirty_cells + first_frame(overlaps)),
        iff(changed('Lowest track'), [
            setv('Timeline lowest threshold', V('Lowest track')),
            iff(cmp('lt', V('Timeline used Lowest track'), lowest), [setv('Timeline lowest threshold', V('Timeline used Lowest track'))]),
            setv('Timeline lowest threshold', lowest + 160),
        ] + first_frame(cmp('gt', hip('Y', 0), lowest))),
        iff(OR(OR(changed('Goal X'), changed('Goal Y')), changed('Goal enabled')),
            first_frame(OR(crosses(V('Goal X')), crosses(V('Timeline used Goal X'))))),
        iff(changed('Timeline detach frame'), [
            iff(AND(cmp('gt', requested_detach, 0), cmp('lt', requested_detach, resume)), [setv('Timeline resume', requested_detach)]),
            iff(AND(cmp('gt', V('Timeline used Timeline detach frame'), 0), cmp('lt', V('Timeline used Timeline detach frame'), resume)),
                [setv('Timeline resume', V('Timeline used Timeline detach frame'))]),
        ]),
    ] + [setv('Timeline used ' + name, V(name)) for name in SNAPSHOT] + [
        setv('Timeline dirty', 0), setv('Timeline dirty all', 0), setv('Timeline expected lines', length('LX')),
    ])

    proc('update timeline', [
        iff(OR(cmp('equals', V('Grid ready'), 0), cmp('equals', V('Timeline restart'), 1)), [
            iff(cmp('equals', V('Grid ready'), 0), [call('build spatial grid')]),
            setv('Timeline restart', 0),
            setv('Timeline ready', 0),
            setv('Timeline current pose', 0),
            call('resolve timeline resume'),
            iff(cmp('equals', resume, 0), [
                clear('Timeline ' + name) for name in CACHE_LISTS + CACHE_VARIABLES + CELL_BOUNDS
            ] + [
                call('reset rider'),
                setv('Physics Ride result', 1),
            ] + reset_frame_cells(api) + [
                call('record timeline frame'),
                setv('Timeline end', 0),
            ], [
                # Restore the solver from the last kept frame and drop the rest.
                setv('Timeline index', (resume - 1) * point_count + 1),
                setv('Timeline point', 1),
                loop(point_count, [
                    replace('Physics ' + name, point, L('Timeline ' + name, offset)) for name in CACHE_LISTS
                ] + [change('Timeline point', 1), change('Timeline index', 1)]),
            ] + [setv('Physics ' + name, L('Timeline ' + name, resume)) for name in CACHE_VARIABLES] + [
                setv('Physics Frame', resume - 1),
                loop((end - resume + 1) * point_count, [delete('Timeline ' + name) for name in CACHE_LISTS]),
                loop(end - resume + 1, [delete('Timeline ' + name) for name in CACHE_VARIABLES + CELL_BOUNDS]),
                setv('Timeline end', resume - 1),
                iff(cmp('gt', physics_result, 1), [setv('Timeline ready', 1)]),
            ]),
            iff(cmp('gt', target, 0), [setv('Timeline refocus', 1)]),
        ]),
        iff(cmp('equals', ready, 0), [
            # Yield to input and drawing between batches while computing the
            # complete ride. sensing_timer is frozen during a step (scratch-vm
            # reads runtime.currentMSecs), so the budget uses the live clock
            # sensing_dayssince2000 (Date.now) converted to milliseconds.
            setv('Timeline budget', Expr('sensing_dayssince2000') * 86400000 + TIMELINE_BUDGET_MS),
            until(OR(cmp('equals', ready, 1), cmp('gt', Expr('sensing_dayssince2000') * 86400000, V('Timeline budget'))), [
                setv('Previous hip X', hip_x),
                setv('Previous hip Y', hip_y),
                iff(cmp('equals', physics_frame + 1, requested_detach), [
                    setv('Physics Mounted', 0),
                ]),
            ] + reset_frame_cells(api) + [
                call('physics frame'),
                call('check result'),
                iff(AND(cmp('equals', physics_result, 1), cmp('equals', physics_frame, last_storable_frame)), [
                    setv('Physics Ride result', 5),
                ]),
                call('record timeline frame'),
                setv('Timeline end', physics_frame),
                iff(cmp('gt', physics_result, 1), [setv('Timeline ready', 1)]),
            ]),
        ]),
    ])

    previous = (V('Frame') - 1) * point_count + 5
    speed_x = (L('Timeline X', previous) - L('Timeline PX', previous)) * (1 - L('Air', 5))
    speed_y = (L('Timeline Y', previous) - L('Timeline PY', previous)) * (1 - L('Air', 5)) + .175
    proc('read timeline frame', [
        setv('Timeline selected', target),
        iff(cmp('gt', target, end), [setv('Timeline selected', end)]),
        iff(AND(
            AND(cmp('gt', length('Timeline Ride result'), 0),
                OR(cmp('equals', ready, 1), NOT(cmp('gt', target, end)))),
            OR(NOT(cmp('equals', V('Frame'), V('Timeline selected'))), cmp('equals', V('Timeline current pose'), 0)),
        ), [
            setv('Frame', V('Timeline selected')),
            setv('Timeline index', V('Frame') * point_count + 1),
            setv('Timeline point', 1),
            loop(point_count, [
                replace(name, point, L('Timeline ' + name, offset)) for name in CACHE_LISTS
            ] + [change('Timeline point', 1), change('Timeline index', 1)]),
        ] + [setv(name, L('Timeline ' + name, V('Frame') + 1)) for name in CACHE_VARIABLES] + [
            # The hip's speed is the velocity integrate points used on this frame, which the previous frame's cached positions define.
            iff(cmp('gt', V('Frame'), 0), [setv('Timeline speed', mathop('sqrt', speed_x * speed_x + speed_y * speed_y))],
                [setv('Timeline speed', .4)]),
            setv('Timeline current pose', 1),
        ]),
        iff(cmp('equals', V('Timeline current pose'), 1), [
            iff(cmp('gt', result, 1), [setv('State', result), setv('Playing', 0)], [
                iff(cmp('equals', V('Editing'), 1), [setv('State', 0)], [setv('State', 2 - V('Playing'))]),
            ]),
        ]),
    ])

    proc('keep rider visible', [
        iff(OR(
            cmp('gt', mathop('abs', (L('X', 5) - V('Camera X')) * V('Zoom')), 210),
            cmp('gt', mathop('abs', (L('Y', 5) - V('Camera Y')) * V('Zoom')), 93),
        ), [call('follow rider')]),
    ])
    proc('show timeline frame', [
        call('read timeline frame'),
        iff(cmp('equals', V('Timeline current pose'), 1), [
            iff(cmp('equals', V('Timeline seek focus'), 1), [
                call('follow rider'),
            ], [
                iff(AND(cmp('equals', V('Timeline refocus'), 1), cmp('equals', V('Drawing'), 0)), [
                    call('keep rider visible'),
                ]),
            ]),
            iff(cmp('equals', V('Drawing'), 0), [setv('Timeline refocus', 0)]),
            setv('Timeline seek focus', 0),
        ]),
    ])
    proc('clear timeline detach', [
        iff(cmp('gt', requested_detach, 0), [
            setv('Timeline detach frame', 0),
            setv('Timeline restart', 1),
        ]),
    ])
    proc('detach rider', [
        iff(AND(AND(cmp('equals', V('Editing'), 0), cmp('equals', ready, 1)), cmp('lt', V('State'), 3)), [
            setv('Playing', 0),
            setv('Timeline detach frame', V('Frame') + 1),
            setv('Timeline target', requested_detach),
            setv('Timeline restart', 1),
        ]),
    ])
    proc('start timeline scrub', [
        iff(AND(cmp('equals', ready, 1), cmp('equals', V('Timeline loading'), 0)), [
            setv('Timeline dragging', 1),
            setv('Playing', 0),
            setv('Drawing', 0),
            call('scrub timeline'),
        ]),
    ])
    proc('scrub timeline', [
        setv('Timeline target', mathop('round', (V('Mouse X') - RAIL_LEFT) / (RAIL_RIGHT - RAIL_LEFT) * end)),
        iff(cmp('lt', target, 0), [setv('Timeline target', 0)]),
        iff(cmp('gt', target, end), [setv('Timeline target', end)]),
        iff(NOT(cmp('equals', target, V('Frame'))), [setv('Timeline seek focus', 1)]),
    ])


def hit(api):
    V, cmp, AND = (api[name] for name in ('V', 'cmp', 'AND'))
    return AND(
        AND(cmp('gt', V('Mouse X'), RAIL_LEFT - 9), cmp('lt', V('Mouse X'), RAIL_RIGHT + 9)),
        AND(cmp('lt', V('Mouse Y'), CANVAS_BOTTOM), cmp('gt', V('Mouse Y'), -154)),
    )


def render(api):
    globals().update(api)
    thumb_x = RAIL_LEFT + (RAIL_RIGHT - RAIL_LEFT) * V('Frame') / V('Timeline end')
    playhead = [
        setv('Timeline thumb X', RAIL_LEFT),
        iff(cmp('gt', V('Timeline end'), 0), [setv('Timeline thumb X', thumb_x)]),
    ] + stamp(cat('timeline playhead ', V('Timeline dragging')), V('Timeline thumb X'), -142) + text(
        cat('Frame ', V('Frame'), ' / ', V('Timeline end')), 85, -142,
    )
    phase = op('mod', mathop('floor', Expr('sensing_timer') * 12), 8)
    loading = stamp(cat('timeline spinner ', phase), 91, -142) + text('Calculating ride...', 103, -142)
    return stamp('timeline rail', (RAIL_LEFT + RAIL_RIGHT) / 2, -142) + [
        iff(cmp('equals', V('Timeline loading'), 1), loading, [
            iff(cmp('equals', V('Timeline ready'), 1), playhead),
        ]),
    ]


def build_assets(api):
    globals().update(api)
    width = RAIL_RIGHT - RAIL_LEFT + 2
    rail = f'<path d="M1 2v8M1 6h{width - 2}m0-4v8" fill="none" stroke="#918b82"/>'
    costumes.append(costume('timeline rail', svg(width, 12, rail), width / 2, 6))
    for dragging, fill in enumerate(('#58766d', '#30332f')):
        playhead = (
            f'<path d="M1.5 3.5h11v4L7 12l-5.5-4.5z" fill="{fill}" '
            'stroke="#30332f" stroke-linejoin="round"/>'
        )
        # The outlined point meets the top edge of the rail.
        costumes.append(costume(f'timeline playhead {dragging}', svg(14, 14, playhead), 7, 12))
    for phase in range(8):
        spinner = (
            '<circle cx="7" cy="7" r="4.5" fill="none" stroke="#b6b1a9" stroke-width="1.5"/>'
            '<path d="M7 2.5a4.5 4.5 0 0 1 3.9 6.75" fill="none" stroke="#30332f" '
            f'stroke-width="1.5" stroke-linecap="round" transform="rotate({phase * 45} 7 7)"/>'
        )
        costumes.append(costume(f'timeline spinner {phase}', svg(14, 14, spinner), 7, 7))
