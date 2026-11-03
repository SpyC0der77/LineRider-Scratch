"""LR1 compact, checksummed track codes implemented with stock Scratch blocks.

Base-32 digits carry four data bits and a continuation bit. Coordinates use
hundredths of a world unit, signed zigzag values, and endpoint deltas. Connected
segments omit their start entirely. No collision caches or simulation state are
serialized. All decode work is staged before the undoable commit.
"""
ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
LIMIT = 1_000_000
SCALE = 100


def install(api):
    globals().update(api)
    for name in ['Code output', 'Code input', 'Track code', 'Code start X', 'Code start Y', 'Code end X', 'Code end Y', 'Code material']:
        lists[name] = [name, []]
    lists['Code alphabet'] = ['Code alphabet', list(ALPHABET)]
    for name, value in [('Code open', 0), ('Code error', ''), ('Code text', ''), ('Code raw', '')]:
        V(name); variables[name][1] = value
    def mod(a, b): return Expr('operator_mod', {'NUM1': a, 'NUM2': b})
    def char(s, at): return Expr('operator_letter_of', {'LETTER': at, 'STRING': s})
    def slen(s): return Expr('operator_length', {'STRING': s})
    def absval(v): return mathop('abs', v)
    def bad(message): return [iff(cmp('equals', V('Code error'), ''), [setv('Code error', message)])]
    def write(value, signed=False):
        return [setv('Code number', value), call('code write signed' if signed else 'code write unsigned')]
    def read(dest, signed=False):
        return [call('code read signed' if signed else 'code read unsigned'), setv(dest, V('Code number'))]
    def coordinate(dest):
        return read(dest, True) + [iff(cmp('gt', absval(V(dest)), LIMIT*SCALE), bad('A coordinate is out of range.'))]
    staged = ['Code start X', 'Code start Y', 'Code end X', 'Code end Y', 'Code material']
    proc('code write unsigned', [setv('Code more', 1), until(cmp('equals', V('Code more'), 0), [
        setv('Code digit', mod(V('Code number'), 16)), setv('Code number', mathop('floor', V('Code number')/16)),
        setv('Code more', 0), iff(cmp('gt', V('Code number'), 0), [change('Code digit', 16), setv('Code more', 1)]),
        add('Code output', L('Code alphabet', V('Code digit')+1)),
        iff(cmp('equals', V('Code hashing'), 1), [setv('Code hash', mod(V('Code hash')*33+V('Code digit'), 65521))])
    ])])
    proc('code write signed', [setv('Code number', V('Code number')*2),
        iff(cmp('lt', V('Code number'), 0), [setv('Code number', -1-V('Code number'))]), call('code write unsigned')])
    proc('code read unsigned', [setv('Code number', 0), setv('Code factor', 1), setv('Code digits', 0), setv('Code more', 1),
        until(OR(cmp('equals', V('Code more'), 0), NOT(cmp('equals', V('Code error'), ''))), [
            iff(OR(cmp('gt', V('Code at'), length('Code input')), cmp('gt', V('Code digits'), 7)), bad('The code is incomplete or too long.'), [
                setv('Code digit', itemindex('Code alphabet', L('Code input', V('Code at')))-1),
                iff(cmp('lt', V('Code digit'), 0), bad('The code contains an invalid character.'), [
                    iff(cmp('equals', V('Code hashing'), 1), [setv('Code hash', mod(V('Code hash')*33+V('Code digit'), 65521))]),
                    change('Code at', 1), change('Code digits', 1), change('Code number', mod(V('Code digit'), 16)*V('Code factor')),
                    setv('Code more', 0), iff(cmp('gt', V('Code digit'), 15), [setv('Code more', 1)]),
                    iff(AND(cmp('equals', V('Code more'), 0), AND(cmp('gt', V('Code digits'), 1), cmp('equals', V('Code digit'), 0))), bad('A number has an invalid encoding.')),
                    iff(cmp('gt', V('Code number'), 400_000_000), bad('A number is out of range.')),
                    setv('Code factor', V('Code factor')*16)
                ])
            ])
        ])])
    proc('code read signed', [call('code read unsigned'), setv('Code odd', mod(V('Code number'), 2)),
        setv('Code number', mathop('floor', V('Code number')/2)),
        iff(cmp('equals', V('Code odd'), 1), [setv('Code number', -1-V('Code number'))])])

    export_segment = [
        setv('Code sx', mathop('round', L('LX', V('Code line'))*SCALE)),
        setv('Code sy', mathop('round', L('LY', V('Code line'))*SCALE)),
        setv('Code ex', mathop('round', (L('LX', V('Code line'))+L('DX', V('Code line')))*SCALE)),
        setv('Code ey', mathop('round', (L('LY', V('Code line'))+L('DY', V('Code line')))*SCALE)),
        setv('Code connected', 0),
        iff(AND(cmp('equals', V('Code sx'), V('Code previous X')), cmp('equals', V('Code sy'), V('Code previous Y'))), [setv('Code connected', 1)])
    ]
    for name in ['sx', 'sy', 'ex', 'ey']:
        export_segment += [iff(cmp('gt', absval(V('Code '+name)), LIMIT*SCALE), bad('A coordinate is out of range.'))]
    export_segment += write(L('Material', V('Code line'))*2+V('Code connected'))
    export_segment += [iff(cmp('equals', V('Code connected'), 0), write(V('Code sx')-V('Code previous X'), True)+write(V('Code sy')-V('Code previous Y'), True))]
    export_segment += write(V('Code ex')-V('Code sx'), True)+write(V('Code ey')-V('Code sy'), True)
    export_segment += [setv('Code previous X', V('Code ex')), setv('Code previous Y', V('Code ey')), change('Code line', 1)]
    export = [setv('Code error', ''), clear('Code output'), setv('Code hash', 1), setv('Code hashing', 1)]
    export += write(length('LX'))+write(V('Goal enabled'))
    for name in ['Spawn X', 'Spawn Y', 'Goal X', 'Goal Y']:
        export += [iff(cmp('gt', absval(V(name)), LIMIT), bad('A coordinate is out of range.'))] + write(mathop('round', V(name)*SCALE), True)
    export += [setv('Code previous X', 0), setv('Code previous Y', 0), setv('Code line', 1), loop(length('LX'), export_segment),
        setv('Code hashing', 0)] + write(V('Code hash')) + [
        iff(cmp('equals', V('Code error'), ''), [
            setv('Code text', join('LR1', Expr('data_listcontents', {}, {'LIST':['Code output','Code output']}))),
            clear('Track code'), add('Track code', V('Code text')), setv('Code size', slen(V('Code text'))),
            setv('Code open', 1), stmt('data_showlist', {}, {'LIST':['Track code','Track code']})
        ], [setv('Code open', 3)]), clear('Code output'), setv('Drawing', 0), setv('Menu', 0)]
    proc('save track code', export)

    proc('close track code', [setv('Code open', 0), stmt('data_hidelist', {}, {'LIST':['Track code','Track code']}),
        setv('Queued click', 0), setv('Drawing', 0), clear('Input keys')])
    proc('load track code', [call('close track code'), setv('Code error', ''), setv('Code open', 2)])
    # All decoded records are validated before any actual track/history mutation.
    segment = read('Code token') + [iff(cmp('gt', V('Code token'), 7), bad('A segment material is invalid.')),
        setv('Code material value', mathop('floor', V('Code token')/2)),
        setv('Code sx', V('Code previous X')), setv('Code sy', V('Code previous Y')),
        iff(cmp('equals', mod(V('Code token'), 2), 0), read('Code delta X', True)+read('Code delta Y', True)+[
            change('Code sx', V('Code delta X')), change('Code sy', V('Code delta Y'))])]
    segment += read('Code delta X', True)+read('Code delta Y', True)+[
        setv('Code ex', V('Code sx')+V('Code delta X')), setv('Code ey', V('Code sy')+V('Code delta Y')),
        iff(AND(cmp('equals', V('Code sx'), V('Code ex')), cmp('equals', V('Code sy'), V('Code ey'))), bad('A segment has zero length.')),
        iff(cmp('lt', V('Code ex'), V('Code sx')), bad('A segment direction is invalid.'))]
    for name in ['sx', 'sy', 'ex', 'ey']:
        segment += [iff(cmp('gt', absval(V('Code '+name)), LIMIT*SCALE), bad('A coordinate is out of range.'))]
    segment += [iff(cmp('equals', V('Code error'), ''), [add(name, value) for name, value in zip(staged, [V('Code sx')/SCALE,V('Code sy')/SCALE,V('Code ex')/SCALE,V('Code ey')/SCALE,V('Code material value')])]),
        setv('Code previous X', V('Code ex')), setv('Code previous Y', V('Code ey'))]
    decode = [setv('Code error', ''), clear('Code input')] + [clear(name) for name in staged] + [
        iff(cmp('gt', slen(V('Code raw')), 120000), bad('The code exceeds the size limit.')),
        setv('Code scan', 1), iff(cmp('equals', V('Code error'), ''), [loop(slen(V('Code raw')), [
            setv('Code character', char(V('Code raw'), V('Code scan'))),
            iff(NOT(OR(OR(cmp('equals', join('x', V('Code character')), 'x '), cmp('equals', join('x', V('Code character')), 'x-')),
                OR(OR(cmp('equals', join('x', V('Code character')), 'x\n'), cmp('equals', join('x', V('Code character')), 'x\r')), cmp('equals', join('x', V('Code character')), 'x\t')))), [add('Code input', V('Code character'))]),
            change('Code scan', 1)
        ])]),
        iff(NOT(AND(cmp('equals', L('Code input', 1), 'L'), AND(cmp('equals', L('Code input', 2), 'R'), cmp('equals', L('Code input', 3), '1')))), bad('This is not an LR1 track code.')),
        setv('Code at', 4), setv('Code hash', 1), setv('Code hashing', 1)
    ] + read('Code count') + [iff(cmp('gt', V('Code count'), 3000), bad('The track exceeds 3000 segments.'))] + read('Code goal enabled') + [
        iff(cmp('gt', V('Code goal enabled'), 1), bad('The goal setting is invalid.'))]
    for name in ['Spawn X', 'Spawn Y', 'Goal X', 'Goal Y']:
        decode += coordinate('Code '+name)
    decode += [setv('Code previous X', 0), setv('Code previous Y', 0), setv('Code line', 0),
        until(OR(NOT(cmp('equals', V('Code error'), '')), cmp('equals', V('Code line'), V('Code count'))), segment+[change('Code line', 1)]),
        setv('Code expected hash', V('Code hash')), setv('Code hashing', 0), call('code read unsigned'),
        iff(NOT(cmp('equals', V('Code number'), V('Code expected hash'))), bad('The checksum does not match.')),
        iff(NOT(cmp('equals', V('Code at'), length('Code input')+1)), bad('The code has extra or missing data.')),
        iff(cmp('equals', V('Code error'), ''), [call('commit track code')]), clear('Code input')]
    decode += [clear(name) for name in staged]
    proc('decode track code', decode)

    geometry = [setv('ax', L('Code start X', V('Code line'))), setv('ay', L('Code start Y', V('Code line'))),
        setv('dx', L('Code end X', V('Code line'))-V('ax')), setv('dy', L('Code end Y', V('Code line'))-V('ay')),
        setv('distance', mathop('sqrt', V('dx')*V('dx')+V('dy')*V('dy')))]
    geometry += [add(k, v) for k, v in [('LX',V('ax')),('LY',V('ay')),('DX',V('dx')),('DY',V('dy')),
        ('NX',(0-V('dy'))/V('distance')),('NY',V('dx')/V('distance')),('InvSq',1/(V('distance')*V('distance'))),
        ('Material',L('Code material',V('Code line'))),('MinX',V('ax')-10),('MaxX',V('ax')+V('dx')+10),
        ('MinY',V('ay')+V('dy')*.5-absval(V('dy'))*.5-10),('MaxY',V('ay')+V('dy')*.5+absval(V('dy'))*.5+10)]]
    proc('commit track code', [call('begin change')] + [clear(f) for f in FIELDS] + [
        setv('Code line', 1), loop(V('Code count'), geometry+[change('Code line',1)])] + [
        setv(name, V('Code '+name)/SCALE) for name in ['Spawn X','Spawn Y','Goal X','Goal Y']] + [
        setv('Goal enabled', V('Code goal enabled')), call('home view'), setv('Notice', 4), setv('Notice until', Expr('sensing_timer')+5)])
    proc('prompt track code', [stmt('sensing_askandwait', {'QUESTION':'Paste a track code. Leave blank to cancel.'}),
        setv('Code raw', Expr('sensing_answer')), clear('Input keys'), setv('Queued click',0),
        iff(cmp('equals', V('Code raw'), ''), [call('close track code')], [call('decode track code'),
            iff(cmp('equals', V('Code error'), ''), [call('close track code')], [setv('Code open',3)])]), setv('Code raw','')])


def render_code(api):
    globals().update(api)
    return [iff(cmp('equals', V('Code open'), 1), stamp('save code dialog') + text(cat(length('LX'),' lines  ',V('Code size'),' characters'), -208, 67)),
            iff(cmp('equals', V('Code open'), 2), stamp('load code dialog')),
            iff(cmp('equals', V('Code open'), 3), stamp('code error dialog') + text(V('Code error'), -201, 14))]


def assets_code(api):
    globals().update(api)
    def panel(lines, buttons):
        content = '<path fill="#30332f" fill-opacity=".28" d="M0 0h480v360H0z"/><rect x="12.5" y="85.5" width="455" height="237" rx="4" fill="#faf8f5" stroke="#b6b1a9"/>'
        for y,label in lines:
            content += f'<text x="28" y="{y}" font-family="sans-serif" font-size="12" fill="#30332f">{html.escape(label)}</text>'
        for x,w,label in buttons:
            content += f'<rect x="{x}" y="281" width="{w}" height="29" rx="3" fill="#faf8f5" stroke="#b6b1a9"/><text x="{x+w/2}" y="300" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#30332f">{label}</text>'
        return svg(480,360,content)
    costumes.append(costume('save code dialog', panel([(106,'Save track code'),(258,'Double-click the code row, then Ctrl+A and Ctrl+C.')], [(354,96,'Close')]),240,180))
    costumes.append(costume('load code dialog', panel([(113,'Load track code'),(145,'Paste your saved code in the answer box below.'),(174,'The current track changes only after the code is valid.'),(204,'Submit an empty answer to cancel.')], []),240,180))
    costumes.append(costume('code error dialog', panel([(116,'Could not load track code'),(201,'The current track and saved slot have been kept.')], [(234,96,'Cancel'),(342,108,'Try again')]),240,180))
