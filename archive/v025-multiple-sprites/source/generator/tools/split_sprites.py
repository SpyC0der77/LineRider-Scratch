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
        'toggle full play','full play pointer',
    },
    'Physics': {
        'reset rider','integrate points','solve sticks','finish frame','physics frame',
        'collide points with lines','build spatial grid','nearby lines','follow rider',
        'check result','advance ride','detach rider','solve ragdoll','update ragdoll pose',
        'resolve ragdoll velocities','ragdoll circle contact','activate ragdoll',
        'begin ragdoll contacts','project ragdoll contacts',
    },
    'Track editor': {
        'begin change','push Undo','push Redo','restore Undo','restore Redo','undo','redo',
        'save track','load track','new track','demo track','fit track','mouse world',
        'snap endpoint','append segment','append stroke','erase under pointer',
        'begin erase gesture','erase endpoints touch','remove erase source',
        'bridge erased neighbor','delete eraser hit','pointer down normal','pointer drag',
        'pointer up','toggle finish goal','zoom in','zoom out','toggle grid',
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
    'Physics': 'Rider, sled, ragdoll, line collisions, and the spatial grid. Every solver iteration and nearby-line query is a local custom-block call.',
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
                target['blocks'].update({k:copy.deepcopy(blocks[k]) for k in keys})
        if module=='Game controller':
            for key,block in blocks.items():
                if block.get('topLevel') and block['opcode'].startswith('event_'):
                    keys=walk(blocks,[key]);assert not used.intersection(keys);used.update(keys)
                    target['blocks'].update({k:copy.deepcopy(blocks[k]) for k in keys})
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
        _layout(target)
        _validate(target,stage['broadcasts'])
    others=[t for t in result['targets'] if not t['isStage'] and t['name']!='Line Rider core']
    for index,t in enumerate(others):t['layerOrder']=len(targets)+index+1
    result['targets']=[stage]+list(targets.values())+others
    report={'sprites':{t['name']:len(t['blocks']) for t in result['targets']},'cross_sprite_call_sites':sum(requests.values()),'exported_requests':len(exported),'shared_state':'Stage','frame_loop_owner':'Game controller','pen_layer_owner':'Renderer'}
    return result,report


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
