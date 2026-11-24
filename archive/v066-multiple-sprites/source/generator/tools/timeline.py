"""Precompute the ride in native Scratch and display it at an independent playhead."""

CACHE_LISTS = ('X', 'Y', 'PX', 'PY', 'VX', 'VY', 'Ground contact', 'Sled contact', 'Grip force')
CACHE_VARIABLES = (
    'Ride result', 'Mounted', 'Sled intact', 'Flight frames', 'Flight departed',
    'Flight failed', 'Ragdoll sleep frames', 'Ragdoll speed squared',
    'Support load', 'Seat load', 'Seat gap', 'Seat along',
)
CANVAS_BOTTOM = -130
RAIL_LEFT = -226
RAIL_RIGHT = 68


def simulation_api(api):
    """Give the solver its own position and result data while the editor shows a frame."""
    def variable(name):
        if name == 'State':
            name = 'Ride result'
        if name in CACHE_VARIABLES or name == 'Frame':
            return 'Physics ' + name
        return name

    def points(name):
        return 'Physics ' + name if name in CACHE_LISTS else name

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
            OR(cmp('equals', V('Flight failed'), 1), cmp('equals', V('Sled intact'), 0)),
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


def install(api):
    globals().update(api)
    point_count = len(pts)
    # Scratch lists hold at most 200,000 items. Frame zero occupies the first row.
    last_storable_frame = 200_000 // point_count - 1
    for name in CACHE_LISTS:
        lists['Physics ' + name] = ['Physics ' + name, lists[name][1][:]]
    for name in CACHE_LISTS + CACHE_VARIABLES:
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
    ] + [add('Timeline ' + name, V('Physics ' + name)) for name in CACHE_VARIABLES])

    define_result_check(simulation_api(api))
    hip_x = L('Physics X', 5)
    hip_y = L('Physics Y', 5)

    proc('update timeline', [
        iff(OR(cmp('equals', V('Grid ready'), 0), cmp('equals', V('Timeline restart'), 1)), [
            iff(cmp('equals', V('Grid ready'), 0), [call('build spatial grid')]),
            setv('Timeline restart', 0),
            setv('Timeline ready', 0),
            setv('Timeline current pose', 0),
        ] + [clear('Timeline ' + name) for name in CACHE_LISTS + CACHE_VARIABLES] + [
            call('reset rider'),
            setv('Physics Ride result', 1),
            call('record timeline frame'),
            setv('Timeline end', 0),
            iff(cmp('gt', target, 0), [setv('Timeline refocus', 1)]),
        ]),
        iff(cmp('equals', ready, 0), [
            # Yield to input and drawing between batches while computing the
            # complete ride. The budget limits work per tick, not ride length.
            setv('Timeline budget', Expr('sensing_timer') + .035),
            until(OR(cmp('equals', ready, 1), cmp('gt', Expr('sensing_timer'), V('Timeline budget'))), [
                setv('Previous hip X', hip_x),
                setv('Previous hip Y', hip_y),
                iff(cmp('equals', physics_frame + 1, requested_detach), [
                    setv('Physics Flight failed', 1),
                ]),
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

    proc('read timeline frame', [
        setv('Timeline selected', target),
        iff(cmp('gt', target, end), [setv('Timeline selected', end)]),
        iff(AND(
            OR(cmp('equals', ready, 1), NOT(cmp('gt', target, end))),
            OR(NOT(cmp('equals', V('Frame'), V('Timeline selected'))), cmp('equals', V('Timeline current pose'), 0)),
        ), [
            setv('Frame', V('Timeline selected')),
            setv('Timeline index', V('Frame') * point_count + 1),
            setv('Timeline point', 1),
            loop(point_count, [
                replace(name, point, L('Timeline ' + name, offset)) for name in CACHE_LISTS
            ] + [change('Timeline point', 1), change('Timeline index', 1)]),
        ] + [setv(name, L('Timeline ' + name, V('Frame') + 1)) for name in CACHE_VARIABLES] + [
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
        iff(cmp('equals', ready, 1), [
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
    return stamp('timeline rail', (RAIL_LEFT + RAIL_RIGHT) / 2, -142) + [
        iff(cmp('equals', V('Timeline ready'), 1), [
            setv('Timeline thumb X', RAIL_LEFT),
            iff(cmp('gt', V('Timeline end'), 0), [setv('Timeline thumb X', thumb_x)]),
        ] + stamp(cat('timeline playhead ', V('Timeline dragging')), V('Timeline thumb X'), -142) + text(
            cat('Frame ', V('Frame'), ' / ', V('Timeline end')), 85, -142,
        ), text('Calculating ride...', 85, -142)),
    ]


def build_assets(api):
    globals().update(api)
    width = RAIL_RIGHT - RAIL_LEFT + 2
    rail = f'<path d="M1 2v8M1 6h{width - 2}m0-4v8" fill="none" stroke="#918b82"/>'
    costumes.append(costume('timeline rail', svg(width, 12, rail), width / 2, 6))
    for dragging, fill in enumerate(('#58766d', '#30332f')):
        playhead = (
            '<path d="M7 10v10" stroke="#30332f" stroke-width="1.5"/>'
            f'<path d="M1.5 3.5h11v4L7 12l-5.5-4.5z" fill="{fill}" '
            'stroke="#30332f" stroke-linejoin="round"/>'
        )
        # Set the costume origin at the rail so the stem marks the exact frame.
        costumes.append(costume(f'timeline playhead {dragging}', svg(14, 21, playhead), 7, 11))
