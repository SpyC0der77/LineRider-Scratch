"""Place native procedures in focused sprites with explicit synchronous messages.

Only calls that cross a sprite boundary become broadcast-and-wait requests.
Solver iterations, collision queries, code parsing, and pen drawing stay local.
The controller remains the sole owner of the frame loop and serializes requests.
"""
import copy
import hashlib
from collections import Counter

from clean_project import walk, children

ROLES = {
    'Game controller': {
        'restore edit camera','home view','edit track','start run','play or pause',
        'retry','prepare paused preview','step once','pointer down','keyboard',
        'keyboard normal','editor keyboard','select edit mode','select play mode',
        'toggle full play','full play pointer','start timeline scrub','scrub timeline',
        'show timeline frame','read timeline frame','follow rider','keep rider visible',
        'clear timeline detach','detach rider',
    },
    'Physics': {
        'reset rider','integrate points','physics frame','solve sticks','finish frame','update rider pose',
        'collide points with lines','build spatial grid','nearby lines',
        'check result','update timeline','record timeline frame','resolve timeline resume',
        'dead end start','dead end step','replay dead ends','scan dead ends',
    },
    'Track editor': {
        'begin change','push Undo','push Redo','restore Undo','restore Redo','undo','redo',
        'mark restore Undo','mark restore Redo',
        'save track','load track','new track','demo track','fit track','mouse world',
        'snap endpoint','append segment','append stroke','erase under pointer','erase cell walk',
        'begin erase gesture','erase endpoints touch','remove erase source',
        'bridge erased neighbor','delete eraser hit','pointer down normal','pointer drag',
        'pointer up','toggle finish goal','zoom in','zoom out','toggle grid',
        'pull brush','sweep erase','erase sample',
    },
    'Menus': {
        'menu pointer','menu hover','menu keyboard','menu selection disabled',
        'execute menu selection','handle toolbar','request edit action',
        'perform requested edit action','request undo','request redo','request save track',
        'request load track','request return to editor','cancel edit confirmation',
        'accept edit confirmation','confirmation pointer','confirmation keyboard',
        'code pointer','code keyboard','toggle help',
    },
    'Track codes': {
        'save track code','load track code','close track code','decode track code',
        'commit track code','prompt track code','code write unsigned','code write signed',
        'code read unsigned','code read signed',
    },
    'Renderer': {
        'render','render scene','render chrome','render overlays','stamp costume',
        'write text','draw clipped segment','clip boundary',
    },
}
PURPOSE = {
    'Game controller': 'Owns the only frame loop, input dispatch, camera, and Play/Edit state. Waits for physics and rendering before starting the next frame.',
    'Physics': 'Rider, sled, collisions, spatial grid and cached timeline frames. Solver iterations and snapshot writes are local custom-block calls.',
    'Track editor': 'Drawing, erasing, touch gap repair, flags, track mutations, saved slot, and undo/redo.',
    'Menus': 'Dropdown input, keyboard navigation, toolbar dispatch, and mode-change confirmations. Rendering belongs to Renderer.',
    'Track codes': 'Compact LR1 serialization, staged validation, import, and native answer prompts.',
    'Renderer': 'The only sprite that clears or draws the shared pen layer. Draws terrain/rider, then chrome, then overlays. All costumes and glyphs live here.',
}


def split(project, make_costume, svg):
    result=copy.deepcopy(project)
    stage=next(t for t in result['targets'] if t['isStage'])
    original=next(t for t in result['targets'] if t['name']=='Line Rider core')
    blocks=original['blocks'];owner={};roots={}
    for module,names in ROLES.items():
        for name in names:
            assert name not in owner,name
            owner[name]=module
    for key,block in blocks.items():
        if block['opcode']=='procedures_definition':
            name=blocks[block['inputs']['custom_block'][1]]['mutation']['proccode']
            assert name in owner,('Unassigned procedure',name)
            roots[name]=key
    calls={name:{blocks[k]['mutation']['proccode'] for k in walk(blocks,[key]) if blocks[k]['opcode']=='procedures_call'} for name,key in roots.items()}
    asynchronous={name for name,key in roots.items() if any(owner[callee]!=owner[name] for callee in calls[name]) or any(blocks[k]['opcode']=='sensing_askandwait' for k in walk(blocks,[key]))}
    while True:
        expanded=asynchronous|{name for name,callees in calls.items() if callees&asynchronous}
        if expanded==asynchronous:break
        asynchronous=expanded
    used=set();targets={};short_names=['Game','Physics','Editor','Menus','Codes','Render']
    for index,(module,_) in enumerate(ROLES.items()):
        target=copy.deepcopy(original);target['name']=module;target['blocks']={};target['comments']={}
        target['visible']=False;target['layerOrder']=index+1;target['currentCostume']=0
        if module!='Renderer':
            label=short_names[index]
            target['costumes']=[make_costume(module,svg(48,48,
                '<rect x="5" y="5" width="38" height="38" rx="3" fill="#faf8f5" stroke="#59574f" stroke-width="2"/>'
                f'<text x="24" y="28" text-anchor="middle" font-family="sans-serif" font-size="9" fill="#30332f">{label}</text>'),24,24)]
        for name,key in roots.items():
            if owner[name]==module:
                keys=walk(blocks,[key]);assert not used.intersection(keys);used.update(keys)
                target["blocks"].update({k:copy.deepcopy(blocks[k]) for k in blocks if k in keys})
        if module=='Game controller':
            for key,block in blocks.items():
                if block.get('topLevel') and block['opcode'].startswith('event_'):
                    keys=walk(blocks,[key]);assert not used.intersection(keys);used.update(keys)
                    target["blocks"].update({k:copy.deepcopy(blocks[k]) for k in blocks if k in keys})
        targets[module]=target
    assert used==set(blocks),'Unassigned blocks'
    exported=set();requests=Counter()
    for module,target in targets.items():
        for key,block in list(target['blocks'].items()):
            if block['opcode']!='procedures_call':continue
            name=block['mutation']['proccode'];destination=owner[name]
            if destination==module:continue
            exported.add(name);requests[(module,destination)]+=1
            broadcast_id='module-'+hashlib.sha1((destination+' / '+name).encode()).hexdigest()[:16]
            message=destination+' / '+name;stage['broadcasts'][broadcast_id]=message
            menu_id=key+'-message'
            block.update(opcode='event_broadcastandwait',inputs={'BROADCAST_INPUT':[1,menu_id]},fields={})
            block.pop('mutation',None)
            target['blocks'][menu_id]={'opcode':'event_broadcast_menu','next':None,'parent':key,'inputs':{},'fields':{'BROADCAST_OPTION':[message,broadcast_id]},'shadow':True,'topLevel':False}
    for name in sorted(exported):
        module=owner[name];broadcast_id='module-'+hashlib.sha1((module+' / '+name).encode()).hexdigest()[:16]
        message=module+' / '+name;hat='receive-'+broadcast_id;invoke='invoke-'+broadcast_id
        targets[module]['blocks'][hat]={'opcode':'event_whenbroadcastreceived','next':invoke,'parent':None,'inputs':{},'fields':{'BROADCAST_OPTION':[message,broadcast_id]},'shadow':False,'topLevel':True}
        targets[module]['blocks'][invoke]={'opcode':'procedures_call','next':None,'parent':hat,'inputs':{},'fields':{},'shadow':False,'topLevel':False,'mutation':{'tagName':'mutation','children':[],'proccode':name,'argumentids':'[]','warp':'true'}}
    for index,(module,target) in enumerate(targets.items()):
        if module!='Game controller':
            hat='hide-module-'+str(index);hide=hat+'-hide'
            target['blocks'][hat]={'opcode':'event_whenflagclicked','next':hide,'parent':None,'inputs':{},'fields':{},'shadow':False,'topLevel':True}
            target['blocks'][hide]={'opcode':'looks_hide','next':None,'parent':hat,'inputs':{},'fields':{},'shadow':False,'topLevel':False}
        target['comments']['module-guide']={'blockId':None,'x':20,'y':0,'width':620,'height':100,'minimized':False,'text':module+'\n\n'+PURPOSE[module]+'\nShared state is on Stage. Cross-sprite requests use broadcast and wait; do not start another frame loop.'}
        target['comments']['interface-guide']={'blockId':None,'x':820,'y':0,'width':620,'height':150,'minimized':True,'text':'Requests received\n\n'+'\n'.join(name for name in sorted(exported) if owner[name]==module)}
        if module=='Physics' and 'credits' in original['comments']:
            target['comments']['credits']=copy.deepcopy(original['comments']['credits']);target['comments']['credits'].update(x=1620,y=0,minimized=True)
        _separate_waits(target,asynchronous)
        _layout(target)
        _validate(target,stage['broadcasts'])
    others=[t for t in result['targets'] if not t['isStage'] and t['name']!='Line Rider core']
    for index,t in enumerate(others):t['layerOrder']=len(targets)+index+1
    result['targets']=[stage]+list(targets.values())+others
    report={'sprites':{t['name']:len(t['blocks']) for t in result['targets']},'cross_sprite_call_sites':sum(requests.values()),'exported_requests':len(exported),'shared_state':'Stage','frame_loop_owner':'Game controller','pen_layer_owner':'Renderer'}
    return result,report


def _separate_waits(target,asynchronous):
    """Keep message waits outside warp mode, and heavy local work inside it.

    A broadcast-and-wait inside a warp procedure busy-waits before letting the
    receiver run. Merely disabling warp would instead make large list loops run
    one iteration per frame. Outline pure runs as local warp batches, leaving
    thin request wrappers in normal mode. No calculation or mutation is reordered.
    """
    blocks=target['blocks'];counter=0
    def statement_nodes(key):
        seen=set();pending=[key]
        while pending:
            node=pending.pop()
            if node in seen:continue
            seen.add(node)
            if node!=key and blocks[node].get('next'):pending.append(blocks[node]['next'])
            for value in blocks[node]['inputs'].values():
                pending.extend(v for v in value[1:] if isinstance(v,str))
        return seen
    def waits(key):
        return any(blocks[n]['opcode'] in ['event_broadcastandwait','sensing_askandwait'] or (blocks[n]['opcode']=='procedures_call' and blocks[n]['mutation']['proccode'] in asynchronous) for n in statement_nodes(key))
    def outline(start,parent,name):
        nonlocal counter
        sequence=[];key=start
        while key:
            sequence.append(key);key=blocks[key].get('next')
        output=[];at=0
        while at<len(sequence):
            key=sequence[at]
            if waits(key):
                for input_name in ['SUBSTACK','SUBSTACK2']:
                    if input_name in blocks[key]['inputs']:
                        child=blocks[key]['inputs'][input_name][1]
                        blocks[key]['inputs'][input_name][1]=outline(child,key,name)
                output.append(key);at+=1;continue
            end=at+1
            while end<len(sequence) and not waits(sequence[end]):end+=1
            run=sequence[at:end]
            has_loop=any(blocks[node]['opcode'] in ['control_repeat','control_repeat_until','control_forever'] for k in run for node in statement_nodes(k))
            if len(run)>1 or has_loop:
                counter+=1;prefix='batch-'+hashlib.sha1(target['name'].encode()).hexdigest()[:6]+'-'+str(counter)
                definition=prefix+'-definition';prototype=prefix+'-prototype';invoke=prefix+'-call';batch_name=name+' / batch '+str(counter)
                blocks[definition]={'opcode':'procedures_definition','next':run[0],'parent':None,'inputs':{'custom_block':[1,prototype]},'fields':{},'shadow':False,'topLevel':True}
                mutation={'tagName':'mutation','children':[],'proccode':batch_name,'argumentids':'[]','argumentnames':'[]','argumentdefaults':'[]','warp':'true'}
                blocks[prototype]={'opcode':'procedures_prototype','next':None,'parent':definition,'inputs':{},'fields':{},'shadow':True,'topLevel':False,'mutation':mutation}
                blocks[invoke]={'opcode':'procedures_call','next':None,'parent':None,'inputs':{},'fields':{},'shadow':False,'topLevel':False,'mutation':{'tagName':'mutation','children':[],'proccode':batch_name,'argumentids':'[]','warp':'true'}}
                blocks[run[0]]['parent']=definition;blocks[run[-1]]['next']=None;output.append(invoke)
            else:output.extend(run)
            at=end
        for i,key in enumerate(output):
            blocks[key]['parent']=parent if i==0 else output[i-1]
            blocks[key]['next']=output[i+1] if i+1<len(output) else None
        return output[0] if output else None
    for key,block in list(blocks.items()):
        if block['opcode']!='procedures_definition':continue
        prototype=blocks[block['inputs']['custom_block'][1]];name=prototype['mutation']['proccode']
        if name in asynchronous:
            prototype['mutation']['warp']='false'
            if block['next']:block['next']=outline(block['next'],key,name)


def _layout(target):
    blocks=target['blocks'];columns=[190,190,190];width=1900
    # Procedure implementations are separate from their small message entry hats.
    for key,b in sorted(blocks.items(),key=lambda kv:(kv[1]['opcode']!='event_whenflagclicked',kv[1].get('mutation',{}).get('proccode',''),kv[0])):
        if not b.get('topLevel'):continue
        column=2 if b['opcode']=='event_whenbroadcastreceived' else 0 if b['opcode']=='event_whenflagclicked' else min(range(2),key=lambda i:columns[i])
        b['x']=20+column*width;b['y']=columns[column]
        statements=sum(1 for child in walk(blocks,[key]) if not blocks[child]['opcode'].startswith('operator_') and blocks[child]['opcode'] not in ['procedures_prototype','event_broadcast_menu'] and ('SUBSTACK' in blocks[child]['inputs'] or blocks[child].get('next') is not None or blocks[child]['opcode'].startswith(('data_set','data_change','data_add','data_replace','data_delete','pen_','looks_','motion_','procedures_','event_broadcast','control_'))))
        columns[column]+=max(150,statements*32+90)


def _validate(target,broadcasts):
    blocks=target['blocks'];definitions={b['mutation']['proccode'] for b in blocks.values() if b['opcode']=='procedures_prototype'}
    reached=walk(blocks,[k for k,b in blocks.items() if b.get('topLevel')])
    assert reached==set(blocks),(target['name'],'orphan blocks')
    for key,b in blocks.items():
        if b['parent']:assert b['parent'] in blocks
        for child in children(b):assert child in blocks
        if b['opcode']=='procedures_call':assert b['mutation']['proccode'] in definitions,(target['name'],b['mutation']['proccode'])
        if b['opcode'] in ['event_broadcast_menu','event_whenbroadcastreceived']:assert b['fields']['BROADCAST_OPTION'][1] in broadcasts
