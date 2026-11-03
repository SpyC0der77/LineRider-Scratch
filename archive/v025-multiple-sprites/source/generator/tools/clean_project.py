"""Remove unreachable Scratch code and organize the executable procedures."""
import copy


def children(block):
    if block.get('next'):
        yield block['next']
    for value in block.get('inputs', {}).values():
        for item in value[1:]:
            if isinstance(item, str):
                yield item


def walk(blocks, starts):
    seen, pending = set(), list(starts)
    while pending:
        key = pending.pop()
        if key in seen or key not in blocks:
            continue
        seen.add(key)
        pending.extend(children(blocks[key]))
    return seen


def reachable(blocks):
    definitions = {}
    for key, block in blocks.items():
        if block['opcode'] == 'procedures_definition':
            prototype = blocks[block['inputs']['custom_block'][1]]
            definitions[prototype['mutation']['proccode']] = key
    seen, pending = set(), [k for k,b in blocks.items() if b.get('topLevel') and b['opcode'].startswith('event_')]
    while pending:
        key = pending.pop()
        if key in seen:
            continue
        seen.add(key)
        block = blocks[key]
        pending.extend(k for k in children(block) if k not in seen)
        if block['opcode'] == 'procedures_call':
            pending.append(definitions[block['mutation']['proccode']])
    return seen


def splice(blocks, removed):
    def skip(key):
        while key in removed:
            key = blocks[key].get('next')
        return key
    for key, block in blocks.items():
        if key in removed:
            continue
        block['next'] = skip(block.get('next'))
        for name, value in list(block['inputs'].items()):
            if len(value)>1 and isinstance(value[1],str) and value[1] in removed:
                target=skip(value[1])
                if target:
                    value[1]=target
                else:
                    del block['inputs'][name]


def clean(project, *, test_hooks=False):
    result=copy.deepcopy(project)
    before=sum(len(t['blocks']) for t in result['targets'])
    unused_procedures=[]
    for target in result['targets']:
        blocks=target['blocks']
        removed=set()
        if not test_hooks:
            for key,block in blocks.items():
                if block['opcode'].startswith('control_if'):
                    condition=block.get('inputs',{}).get('CONDITION',[None,None])[1]
                    if isinstance(condition,str) and any(blocks[k].get('fields',{}).get('VARIABLE',[None])[0] in ['Capture hold','Queued steps'] for k in walk(blocks,[condition])):
                        removed.add(key)
                if block['opcode'] in ['data_setvariableto','data_changevariableby'] and block['fields']['VARIABLE'][0] in ['Capture hold','Capture ready','Queued steps']:
                    removed.add(key)
            splice(blocks,removed)
        keep=reachable(blocks)
        for key,block in blocks.items():
            if block['opcode']=='procedures_definition' and key not in keep:
                unused_procedures.append(blocks[block['inputs']['custom_block'][1]]['mutation']['proccode'])
        target['blocks']={k:b for k,b in blocks.items() if k in keep}
    # Remove scalar scratchwork that is written but never read. Iterate because
    # removing a dead write can make its RHS-only scratchwork unused as well.
    while True:
        reads={b['fields']['VARIABLE'][1] for t in result['targets'] for b in t['blocks'].values() if b['opcode']=='data_variable'}
        reads.update(m['id'] for m in result.get('monitors',[]) if m['opcode']=='data_variable')
        if test_hooks:
            reads.add('Capture ready')
        changed=False
        for target in result['targets']:
            blocks=target['blocks']
            removed={k for k,b in blocks.items() if b['opcode'] in ['data_setvariableto','data_changevariableby'] and b['fields']['VARIABLE'][1] not in reads}
            if removed:
                changed=True;splice(blocks,removed)
                keep=reachable(blocks);target['blocks']={k:b for k,b in blocks.items() if k in keep}
        if not changed:
            break
    # Scratch normally performs this compact reporter serialization after a
    # manual save. Emit it directly so no standalone variable reporters remain.
    compressed=0
    for target in result['targets']:
        blocks=target['blocks'];removed=set()
        for block in blocks.values():
            for name,value in block['inputs'].items():
                if len(value)>1 and isinstance(value[1],str):
                    reporter=blocks[value[1]]
                    if reporter['opcode']=='data_variable':
                        field=reporter['fields']['VARIABLE']
                        # Preserve input kind. Adding a text shadow to a boolean
                        # socket produces phantom reporter IDs in Scratch GUI.
                        block['inputs'][name]=[value[0],[12,field[0],field[1]]]+value[2:]
                        removed.add(value[1])
        compressed+=len(removed)
        for key in removed:
            del blocks[key]
        for block in blocks.values():
            block['parent']=None
        for key,block in blocks.items():
            for child in children(block):
                blocks[child]['parent']=key
        assert len(reachable(blocks))==len(blocks),'Unreachable native blocks survived cleanup'
        target['comments']={k:c for k,c in target.get('comments',{}).items() if not c.get('blockId') or c['blockId'] in blocks}
        layout(target)
    variable_ids,set_lists=set(),set()
    for target in result['targets']:
        for block in target['blocks'].values():
            if 'VARIABLE' in block.get('fields',{}):variable_ids.add(block['fields']['VARIABLE'][1])
            if 'LIST' in block.get('fields',{}):set_lists.add(block['fields']['LIST'][1])
            for value in block['inputs'].values():
                for item in value[1:]:
                    if isinstance(item,list) and item and item[0]==12:variable_ids.add(item[2])
    for monitor in result.get('monitors',[]):
        (set_lists if monitor['opcode']=='data_listcontents' else variable_ids).add(monitor['id'])
    removed_variables=removed_lists=0
    for target in result['targets']:
        old=len(target['variables']);target['variables']={k:v for k,v in target['variables'].items() if k in variable_ids};removed_variables+=old-len(target['variables'])
        old=len(target['lists']);target['lists']={k:v for k,v in target['lists'].items() if k in set_lists};removed_lists+=old-len(target['lists'])
    report=dict(blocks_before=before,blocks_after=sum(len(t['blocks']) for t in result['targets']),compressed_variable_reporters=compressed,
                unused_procedures=sorted(set(unused_procedures)),removed_variables=removed_variables,removed_lists=removed_lists,
                orphaned_blocks=0,test_hooks=test_hooks)
    return result,report


def layout(target):
    # The documentation sprite already arranges its comments for reading.
    if 'prompt-history-index' in target.get('comments',{}):
        return
    blocks=target['blocks']
    groups={name:[] for name in ['Start and input','Editor and history','Tracks and codes','Menus and dialogs','Rider physics','Ragdoll','Rendering']}
    for key,block in blocks.items():
        if not block.get('topLevel'):
            continue
        if block['opcode'].startswith('event_'):
            group='Start and input';name=block['opcode']+str(block.get('fields',{}))
        else:
            name=blocks[block['inputs']['custom_block'][1]]['mutation']['proccode']
            if any(word in name for word in ['ragdoll','endpoints touch']):group='Ragdoll' if 'ragdoll' in name else 'Editor and history'
            elif any(word in name for word in ['code','track']):group='Tracks and codes'
            elif any(word in name for word in ['menu','confirmation','help','requested edit','mode','toolbar','full play']):group='Menus and dialogs'
            elif any(word in name for word in ['render','draw clipped','clip boundary','stamp','text']):group='Rendering'
            elif name in ['reset rider','integrate points','solve sticks','finish frame','physics frame','collide points with lines','nearby lines','build spatial grid','check result','follow rider']:group='Rider physics'
            else:group='Editor and history'
        groups[group].append((name,key))
    x=20
    for group,roots in groups.items():
        if not roots:continue
        target['comments']['section-'+group]={'blockId':None,'x':x,'y':0,'width':360,'height':48,'minimized':False,'text':group}
        y=90
        for name,key in sorted(roots):
            blocks[key]['x']=x;blocks[key]['y']=y
            statements=sum(1 for child in walk(blocks,[key]) if blocks[child]['opcode'] not in ['data_variable','procedures_prototype'] and not blocks[child]['opcode'].startswith('operator_') and (blocks[child].get('next') is not None or blocks[child]['opcode'].startswith(('control_','procedures_','data_set','data_change','data_add','data_delete','data_replace','motion_','pen_','looks_','sensing_ask'))))
            y+=max(150,statements*32+100)
        x+=2000
    if 'credits' in target['comments']:
        target['comments']['credits'].update(x=x,y=0,minimized=True)
