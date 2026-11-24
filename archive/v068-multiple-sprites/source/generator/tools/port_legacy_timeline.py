"""Add the current timeline to the earlier split-sprite Scratch editor."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from clean_project import children, splice, walk
from timeline import CANVAS_BOTTOM


ROOT = Path(__file__).resolve().parents[1]
POINT_LISTS = ('X', 'Y', 'PX', 'PY', 'VX', 'VY')
LEGACY_SOLVER = (
    'reset rider', 'integrate points', 'solve sticks', 'finish frame', 'physics frame',
    'build spatial grid', 'nearby lines', 'collide points with lines', 'update ragdoll pose',
)
TIMELINE_PHYSICS = ('update timeline', 'record timeline frame', 'check result')
DEMO_FLAGS = ('Spawn X', 'Spawn Y', 'Goal X', 'Goal Y', 'Goal enabled')


def procedures(blocks):
    return {
        blocks[block['inputs']['custom_block'][1]]['mutation']['proccode']: key
        for key, block in blocks.items() if block['opcode'] == 'procedures_definition'
    }


def live_blocks(blocks):
    return walk(blocks, [key for key, block in blocks.items() if block['topLevel']])


def selected_blocks(blocks, names):
    roots = procedures(blocks)
    return {key: deepcopy(blocks[key]) for key in walk(blocks, [roots[name] for name in names])}


def graft(blocks, source):
    for old_key, block in source.items():
        for field in ('parent', 'next'):
            if block[field] in source:
                block[field] = 'legacy-' + block[field]
        for value in block['inputs'].values():
            for index, child in enumerate(value[1:], 1):
                if isinstance(child, str) and child in source:
                    value[index] = 'legacy-' + child
        blocks['legacy-' + old_key] = block


def unwrap(blocks, key, branch):
    block = blocks[key]
    beginning = last = block['inputs'][branch][1]
    while blocks[last]['next'] is not None:
        last = blocks[last]['next']
    blocks[last]['next'] = block['next']
    block['next'] = beginning
    splice(blocks, {key})
    del blocks[key]


def field_name(block, field):
    return block['fields'].get(field, [None])[0]


def uses_variable(blocks, root, name):
    if not isinstance(root, str):
        return isinstance(root, list) and root[:2] == [12, name]
    return any(
        field_name(blocks[key], 'VARIABLE') == name
        or any(value[:2] == [12, name] for value in primitives(blocks[key]))
        for key in walk(blocks, [root])
    )


def primitives(block):
    return (
        part for input_ in block['inputs'].values()
        for part in input_[1:] if isinstance(part, list)
    )


def substitute_reporter(blocks, key, input_):
    for block in blocks.values():
        for name, old in block['inputs'].items():
            if old[1] == key:
                block['inputs'][name] = deepcopy(input_)


def mounted_solver(source):
    # Keep the original contact, binding, and pose blocks. Strip the branches
    # that only run after the mounted binding breaks.
    blocks = selected_blocks(source, LEGACY_SOLVER)
    removed = set()
    for key, block in list(blocks.items()):
        op = block['opcode']
        inputs = block['inputs']
        name = block.get('mutation', {}).get('proccode')
        if name == 'activate ragdoll':
            removed.add(block['parent'])
        elif name == 'begin ragdoll contacts':
            if blocks[block['parent']]['opcode'] != 'control_if':
                removed.add(key)
        elif name == 'update ragdoll pose':
            block['mutation']['proccode'] = 'update rider pose'
        if op == 'data_setvariableto' and field_name(block, 'VARIABLE') in {
            'Camera X', 'Camera Y', 'Ragdoll active', 'Ragdoll sleep frames',
            'Ragdoll speed squared', 'Preserve contact velocity', 'Crash complete',
        }:
            removed.add(key)
        if op == 'operator_or' and uses_variable(blocks, inputs['OPERAND2'][1], 'Ragdoll active'):
            substitute_reporter(blocks, key, inputs['OPERAND1'])
        if op == 'control_repeat' and uses_variable(blocks, inputs['TIMES'][1], 'Ragdoll active'):
            inputs['TIMES'] = [1, [10, '6']]
        if 'CONDITION' in inputs and uses_variable(blocks, inputs['CONDITION'][1], 'Ragdoll active'):
            if op == 'control_if_else':
                unwrap(blocks, key, 'SUBSTACK2')
            elif op == 'control_if':
                condition = blocks[inputs['CONDITION'][1]]
                if condition['opcode'] != 'operator_equals':
                    continue
                if condition['inputs']['OPERAND2'][1][1] == '0':
                    unwrap(blocks, key, 'SUBSTACK')
                else:
                    removed.add(key)

    splice(blocks, removed)
    for key in removed:
        del blocks[key]
    blocks = {key: blocks[key] for key in live_blocks(blocks)}
    assert not any(uses_variable(blocks, key, 'Ragdoll active') for key in procedures(blocks).values())
    for block in blocks.values():
        for field, names in (('VARIABLE', ('Mounted', 'Frame')), ('LIST', POINT_LISTS)):
            name = field_name(block, field)
            if name in names:
                block['fields'][field] = ['Physics ' + name] * 2
        for part in primitives(block):
            if part[0] == 12 and part[1] in ('Mounted', 'Frame'):
                part[1:3] = ['Physics ' + part[1]] * 2
    return blocks


def literal_replace(blocks, substitutions):
    for block in blocks.values():
        for part in primitives(block):
            if part[0] in (4, 5, 6, 7, 8, 10) and str(part[1]) in substitutions:
                part[1] = str(substitutions[str(part[1])])


def adapt_timeline(physics, controller, template_count, count):
    # The timeline blocks are shared with the current editor. The older solver
    # has fewer points and reports a broken binding through Mounted.
    cache_names = {'Timeline ' + name for name in (*POINT_LISTS, 'Mounted', 'Ride result')}
    for blocks in (physics, controller):
        selected = walk(blocks, [
            key for name, key in procedures(blocks).items() if name in
            (*TIMELINE_PHYSICS, 'read timeline frame')
        ])
        removed = set()
        for key in selected:
            block = blocks[key]
            name = field_name(block, 'LIST')
            if name and ((name.startswith('Timeline ') and name not in cache_names)
                         or name in ('Ground contact', 'Sled contact', 'Grip force')):
                removed.add(key)
            if field_name(block, 'VARIABLE') == 'Physics Flight failed':
                block['fields']['VARIABLE'] = ['Physics Mounted'] * 2
                block['inputs']['VALUE'] = [1, [10, '0']]
            if block['opcode'] == 'operator_equals' and uses_variable(blocks, key, 'Physics Flight failed'):
                block['inputs']['OPERAND1'] = [2, [12, 'Physics Mounted', 'Physics Mounted']]
                block['inputs']['OPERAND2'] = [1, [10, '0']]
            if block['opcode'] == 'operator_or':
                inputs = block['inputs']
                if uses_variable(blocks, inputs['OPERAND2'][1], 'Physics Sled intact'):
                    substitute_reporter(blocks, key, inputs['OPERAND1'])

        splice(blocks, removed)
        for key in removed:
            del blocks[key]
        literal_replace({key: blocks[key] for key in selected - removed}, {
            str(template_count): count,
            str(200_000 // template_count - 1): 200_000 // count - 1,
        })


def named_assignments(blocks, name, fields):
    starts = [key for proc, key in procedures(blocks).items() if proc.startswith(name)]
    return {
        field_name(blocks[key], 'VARIABLE'): blocks[key]['inputs']['VALUE']
        for key in walk(blocks, starts) if blocks[key]['opcode'] == 'data_setvariableto'
        and field_name(blocks[key], 'VARIABLE') in fields
    }


def used_stage_data(targets):
    variables, lists = set(), set()
    for target in targets:
        for block in target['blocks'].values():
            if 'VARIABLE' in block['fields']:
                variables.add(block['fields']['VARIABLE'][1])
            if 'LIST' in block['fields']:
                lists.add(block['fields']['LIST'][1])
            for part in primitives(block):
                if part[0] == 12:
                    variables.add(part[2])
                if part[0] == 13:
                    lists.add(part[2])
    return variables, lists


def port(legacy, template):
    original = {target['name']: target for target in legacy['targets']}
    result = {target['name']: target for target in template['targets']}
    stage, old_stage = result['Stage'], original['Stage']
    template_count = len(stage['lists']['Initial X'][1])
    count = len(old_stage['lists']['Initial X'][1])
    physics = result['Physics']['blocks']
    keep = walk(physics, [
        key for name, key in procedures(physics).items() if name in TIMELINE_PHYSICS
    ] + [key for key, block in physics.items() if block['topLevel'] and block['opcode'].startswith('event_')])
    physics = result['Physics']['blocks'] = {key: physics[key] for key in keep}
    adapt_timeline(physics, result['Game controller']['blocks'], template_count, count)
    graft(physics, mounted_solver(original['Physics']['blocks']))

    # Keep the attachment's scene drawing and artwork under the new chrome.
    renderer = result['Renderer']
    scene = selected_blocks(original['Renderer']['blocks'], ('render scene',))
    bottom = next(block for block in scene.values() if field_name(block, 'VARIABLE') == 'Canvas bottom')
    adjustment = scene[bottom['inputs']['VALUE'][1]]['inputs']['NUM2'][1]
    literal_replace({key: scene[key] for key in walk(scene, [adjustment])}, {'26': 179 + CANVAS_BOTTOM})
    literal_replace(scene, {'-153': CANVAS_BOTTOM})
    old_scene = procedures(renderer['blocks'])['render scene']
    for key in walk(renderer['blocks'], [old_scene]):
        del renderer['blocks'][key]
    graft(renderer['blocks'], scene)
    legacy_costumes = {costume['name']: costume for costume in original['Renderer']['costumes']}
    renderer['costumes'] = [
        legacy_costumes.get(costume['name'], costume) if costume['name'] != 'chrome' else costume
        for costume in renderer['costumes']
    ]

    demo = named_assignments(original['Track editor']['blocks'], 'demo track', DEMO_FLAGS)
    replacements = named_assignments(result['Track editor']['blocks'], 'demo track', DEMO_FLAGS)
    assert set(demo) == set(replacements) == set(DEMO_FLAGS)
    for flag in DEMO_FLAGS:
        replacements[flag][:] = demo[flag]

    result['Prompt history'] = original['Prompt history']
    stage['costumes'] = old_stage['costumes']
    targets = list(result.values())
    for target in targets:
        blocks = target['blocks']
        target['blocks'] = blocks = {key: blocks[key] for key in live_blocks(blocks)}
        for block in blocks.values():
            block['parent'] = None
        definitions = procedures(blocks)
        for key, block in blocks.items():
            for child in children(block):
                blocks[child]['parent'] = key
            if block['opcode'] == 'procedures_call':
                assert block['mutation']['proccode'] in definitions, (target['name'], block)

    variables, lists = used_stage_data(targets)
    for monitor in legacy['monitors']:
        (lists if monitor['opcode'] == 'data_listcontents' else variables).add(monitor['id'])
    stage['variables'] = {key: (old_stage['variables'].get(key) or stage['variables'][key]) for key in sorted(variables)}
    for name in POINT_LISTS:
        stage['lists']['Physics ' + name] = ['Physics ' + name, old_stage['lists'][name][1][:]]
    stage['lists'] = {key: (old_stage['lists'].get(key) or stage['lists'][key]) for key in sorted(lists)}
    return {**legacy, 'targets': targets}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, nargs='?', default=ROOT / '[AI] Line Rider.sb3')
    parser.add_argument('output', type=Path, nargs='?', default=ROOT / 'dist/[AI] Line Rider - Timeline.sb3')
    args = parser.parse_args()
    template = ROOT / 'dist/Line Rider.sb3'
    if args.output.resolve() in (args.source.resolve(), template.resolve()):
        parser.error('Choose an output path separate from both input projects.')
    with ZipFile(args.source) as legacy, ZipFile(template) as current:
        data = port(json.loads(legacy.read('project.json')), json.loads(current.read('project.json')))
        source_assets = set(legacy.namelist())
        assets = {item['md5ext'] for target in data['targets'] for field in ('costumes', 'sounds') for item in target[field]}
        with ZipFile(args.output, 'w', ZIP_DEFLATED) as output:
            output.writestr('project.json', json.dumps(data))
            for name in sorted(assets):
                output.writestr(name, (legacy if name in source_assets else current).read(name))
    print('Built ' + str(args.output))


if __name__ == '__main__':
    main()
