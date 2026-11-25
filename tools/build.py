"""Build a native Scratch editor around the lr-core point solver."""
from core import *
import argparse, core, html
from course import DEFAULT_GOAL, DEFAULT_SPAWN
from timeline import (
 CANVAS_BOTTOM, build_assets as build_timeline_assets, hit as timeline_hit,
 install as install_timeline, render as render_timeline, simulation_api,
 mark_all, mark_line, mark_restore, track_frame_cells,
)
# History and persistence are ordinary Scratch lists, saved with the project.
FIELDS=['LX','LY','DX','DY','NX','NY','InvSq','Material','MinX','MaxX','MinY','MaxY']
META=['Spawn X','Spawn Y','Goal X','Goal Y','Goal enabled']
def join(a,b):return Expr('operator_join',{'STRING1':a,'STRING2':b})
def cat(*xs):
 out=xs[0]
 for x in xs[1:]:out=join(out,x)
 return out
def NOT(a):return Expr('operator_not',{'OPERAND':a})
def itemindex(k,v):return Expr('data_itemnumoflist',{'ITEM':v},{'LIST':[k,k]})
def delete(k,i='last'):return stmt('data_deleteoflist',{'INDEX':i},{'LIST':[k,k]})
def insert(k,i,v):return stmt('data_insertatlist',{'INDEX':i,'ITEM':v},{'LIST':[k,k]})
def until(c,seq):return ('until',c,seq)
# Extend the small block builder with repeat-until without depending on a compiler.
basechain=core.chain
def editorchain(seq,parent):
 first=None;prev=None
 for s in seq:
  if s[0] in ('repeat','if','forever','until'):
   typ=s[0];opcode={'repeat':'control_repeat','if':'control_if_else' if typ=='if' and s[3] else 'control_if','forever':'control_forever','until':'control_repeat_until'}[typ]
   id=core.emit(opcode,{'TIMES':s[1]} if typ=='repeat' else {'CONDITION':s[1]} if typ in ('if','until') else {},parent=prev or parent)
   body=s[1] if typ=='forever' else s[2];sub=editorchain(body,id)
   if sub:B[id]['inputs']['SUBSTACK']=[2,sub]
   if typ=='if' and s[3]:B[id]['inputs']['SUBSTACK2']=[2,editorchain(s[3],id)]
  else:id=core.emit(*s,parent=prev or parent)
  if prev:B[prev]['next']=id
  else:first=id
  prev=id
 return first
core.chain=editorchain
for k in ['Grid cell','Grid heads','Grid line','Grid next','Demo '+FIELDS[0]]:lists.setdefault(k,[k,[]])
for f in FIELDS:lists['Demo '+f]=['Demo '+f,lists[f][1][:]];lists['Saved '+f]=['Saved '+f,[]]
for prefix in ['Undo','Redo']:
 for f in FIELDS+['Count']+META:lists[prefix+' '+f]=[prefix+' '+f,[]]
for k,v in [('Spawn X',DEFAULT_SPAWN[0]),('Spawn Y',DEFAULT_SPAWN[1]),('Goal X',DEFAULT_GOAL[0]),('Goal Y',DEFAULT_GOAL[1]),('Goal enabled',1),('Saved Goal enabled',1),('Zoom',1.8),('Edit zoom',1.8),('Saved exists',0),('Saved Spawn X',0),('Saved Spawn Y',0),('Saved Goal X',DEFAULT_GOAL[0]),('Saved Goal Y',DEFAULT_GOAL[1]),('Setting smooth draw',1),('Setting sweep erase',1),('Setting large eraser',0)]:V(k);variables[k][1]=v
# A 64-unit uniform grid. Each line is indexed in every padded AABB cell.
# Cells are numeric keys (gx*100000+gy) in a chained hash: 'Grid heads' has Grid size slots.
proc('build spatial grid',[clear(k) for k in ['Grid cell','Grid heads','Grid line','Grid next']]+[setv('Candidates key','none'),setv('Grid size',1024),iff(cmp('gt',length('LX')*4,1024),[setv('Grid size',length('LX')*4)]),loop(V('Grid size'),[add('Grid heads',0)]),setv('gj',1),setv('Lowest track',V('Spawn Y')+80),loop(length('LX'),[iff(cmp('gt',L('MaxY',V('gj')),V('Lowest track')),[setv('Lowest track',L('MaxY',V('gj')))]),setv('gx0',mathop('floor',L('MinX',V('gj'))/64)),setv('gx1',mathop('floor',L('MaxX',V('gj'))/64)),setv('gy0',mathop('floor',L('MinY',V('gj'))/64)),setv('gy1',mathop('floor',L('MaxY',V('gj'))/64)),setv('gx',V('gx0')),loop(V('gx1')-V('gx0')+1,[setv('gy',V('gy0')),loop(V('gy1')-V('gy0')+1,[setv('grid key',V('gx')*100000+V('gy')),setv('grid slot',op('mod',V('gx')*7919+V('gy'),V('Grid size'))+1),add('Grid line',V('gj')),add('Grid cell',V('grid key')),add('Grid next',L('Grid heads',V('grid slot'))),replace('Grid heads',V('grid slot'),length('Grid line')),change('gy',1)]),change('gx',1)]),change('gj',1)]),setv('Grid ready',1)])
proc('nearby lines',[setv('grid gx',mathop('floor',L('Physics X',V('i'))/64)),setv('grid gy',mathop('floor',L('Physics Y',V('i'))/64)),setv('grid key',V('grid gx')*100000+V('grid gy')),setv('grid slot',op('mod',V('grid gx')*7919+V('grid gy'),V('Grid size'))+1),iff(NOT(cmp('equals',V('Candidates key'),V('grid key'))),track_frame_cells(globals())+[clear('Candidates'),setv('node',L('Grid heads',V('grid slot'))),until(cmp('equals',V('node'),0),[iff(cmp('equals',L('Grid cell',V('node')),V('grid key')),[setv('line id',L('Grid line',V('node'))),insert('Candidates',1,V('line id'))]),setv('node',L('Grid next',V('node')))]),setv('Candidates key',V('grid key'))])])
from mounted_rider import install as install_mounted_rider
install_mounted_rider(simulation_api(globals()))
install_timeline(globals())
# Whole-stroke undo/redo, bounded to twelve snapshots per stack.
def clearstack(prefix):return [clear(prefix+' '+f) for f in FIELDS+['Count']+META]
for prefix in ['Undo','Redo']:
 proc('push '+prefix,[iff(cmp('gt',length(prefix+' Count'),11),[setv('trim',L(prefix+' Count',1)),loop(V('trim'),[delete(prefix+' '+f,1) for f in FIELDS])]+[delete(prefix+' '+f,1) for f in ['Count']+META]),add(prefix+' Count',length('LX'))]+[add(prefix+' '+f,V(f)) for f in META]+[setv('h',1),loop(length('LX'),[add(prefix+' '+f,L(f,V('h'))) for f in FIELDS]+[change('h',1)])])
 proc('mark restore '+prefix,mark_restore(globals(),prefix,FIELDS))
 proc('restore '+prefix,[call('mark restore '+prefix),setv('restore count',L(prefix+' Count',length(prefix+' Count'))),setv('restore at',length(prefix+' LX')-V('restore count')+1)]+[setv(f,L(prefix+' '+f,length(prefix+' '+f))) for f in META]+[clear(f) for f in FIELDS]+[loop(V('restore count'),[add(f,L(prefix+' '+f,V('restore at'))) for f in FIELDS]+[change('restore at',1)]),loop(V('restore count'),[delete(prefix+' '+f) for f in FIELDS])]+[delete(prefix+' '+f) for f in ['Count']+META]+[setv('Grid ready',0),setv('Dirty',1)])
proc('begin change',[call('push Undo')]+clearstack('Redo')+[setv('Dirty',1)])
proc('undo',[iff(AND(cmp('equals',V('Editing'),1),cmp('gt',length('Undo Count'),0)),[call('push Redo'),call('restore Undo'),setv('Notice',0)])])
proc('redo',[iff(AND(cmp('equals',V('Editing'),1),cmp('gt',length('Redo Count'),0)),[call('push Undo'),call('restore Redo'),setv('Notice',0)])])
# Persistent track slot. Scratch saves these lists inside .sb3, including empty tracks.
proc('save track',[iff(cmp('equals',V('Editing'),1),[clear('Saved '+f) for f in FIELDS]+[setv('h',1),loop(length('LX'),[add('Saved '+f,L(f,V('h'))) for f in FIELDS]+[change('h',1)])]+[setv('Saved '+f,V(f)) for f in META]+[setv('Saved exists',1),setv('Dirty',0),setv('Notice',1),setv('Notice until',Expr('sensing_timer')+5)])])
proc('load track',[iff(AND(cmp('equals',V('Editing'),1),cmp('equals',V('Saved exists'),1)),[call('begin change')]+[clear(f) for f in FIELDS]+[setv('h',1),loop(length('Saved LX'),[add(f,L('Saved '+f,V('h'))) for f in FIELDS]+[change('h',1)])]+[setv(f,V('Saved '+f)) for f in META]+[setv('Dirty',0),*mark_all(globals()),setv('Grid ready',0),call('home view'),setv('Notice',2),setv('Notice until',Expr('sensing_timer')+3)])])
proc('new track',[iff(cmp('equals',V('Editing'),1),[call('begin change')]+[clear(f) for f in FIELDS]+[setv('Spawn X',0),setv('Spawn Y',0),setv('Goal X',180),setv('Goal Y',50),setv('Goal enabled',1),*mark_all(globals()),setv('Grid ready',0),call('home view'),setv('Notice',3),setv('Notice until',Expr('sensing_timer')+5)])])
proc('demo track',[iff(cmp('equals',V('Editing'),1),[call('begin change')]+[clear(f) for f in FIELDS]+[setv('h',1),loop(length('Demo LX'),[add(f,L('Demo '+f,V('h'))) for f in FIELDS]+[change('h',1)]),setv('Spawn X',DEFAULT_SPAWN[0]),setv('Spawn Y',DEFAULT_SPAWN[1]),setv('Goal X',DEFAULT_GOAL[0]),setv('Goal Y',DEFAULT_GOAL[1]),setv('Goal enabled',1),*mark_all(globals()),setv('Grid ready',0),call('home view'),setv('Notice',0)])])
proc('restore edit camera',[setv('Camera X',V('Edit camera X')),setv('Camera Y',V('Edit camera Y')),setv('Zoom',V('Edit zoom'))])
proc('home view',[setv('Camera X',V('Spawn X')+90),setv('Camera Y',V('Spawn Y')+40),setv('Zoom',1.8),setv('Edit camera X',V('Camera X')),setv('Edit camera Y',V('Camera Y')),setv('Edit zoom',V('Zoom'))])
proc('edit track',[
 setv('Full play',0),setv('Editing',1),setv('Playing',0),setv('Drawing',0),call('clear timeline detach'),
 iff(cmp('equals',V('Frame'),0),[call('restore edit camera')]),
])
proc('follow rider',[setv('Camera X',L('X',5)+60/V('Zoom')),setv('Camera Y',L('Y',5)+20/V('Zoom'))])
proc('start run',[
 call('prepare paused preview'),
 iff(AND(cmp('equals',V('Timeline ready'),1),cmp('equals',V('Frame'),V('Timeline end'))),[
  call('clear timeline detach'),setv('Timeline target',0),
 ]),
 setv('Playing',1),setv('Timeline seek focus',1),
])
proc('play or pause',[iff(cmp('equals',V('Playing'),1),[
 setv('Playing',0),
], [call('start run')])])
proc('new or edit',[iff(cmp('equals',V('Editing'),1),[call('new track')],[call('edit track')])])
proc('retry',[
 call('clear timeline detach'),setv('Timeline target',0),
 iff(cmp('equals',V('Editing'),1),[call('home view')],[setv('Playing',1),setv('Timeline seek focus',1)]),
])
proc('prepare paused preview',[
 iff(cmp('equals',V('Editing'),1),[
  setv('Edit camera X',V('Camera X')),setv('Edit camera Y',V('Camera Y')),setv('Edit zoom',V('Zoom')),
  setv('Editing',0),setv('Drawing',0),setv('Notice',0),
 ]),
])
proc('step once',[
 iff(AND(cmp('equals',V('Playing'),0),cmp('lt',V('State'),3)),[
  call('prepare paused preview'),
  iff(cmp('lt',V('Timeline target'),V('Frame')),[setv('Timeline target',V('Frame'))]),
  change('Timeline target',1),setv('Timeline refocus',1),
 ]),
])
# Zoom fits a canvas, not the full stage including toolbars.
proc('fit track',[setv('fit minx',V('Spawn X')-20),setv('fit maxx',V('Goal X')+20),setv('fit miny',V('Spawn Y')-20),setv('fit maxy',V('Goal Y')+20),iff(cmp('equals',V('Goal enabled'),0),[setv('fit maxx',V('Spawn X')+20),setv('fit maxy',V('Spawn Y')+20)]),setv('h',1),loop(length('LX'),[iff(cmp('lt',L('MinX',V('h')),V('fit minx')),[setv('fit minx',L('MinX',V('h')))]),iff(cmp('gt',L('MaxX',V('h')),V('fit maxx')),[setv('fit maxx',L('MaxX',V('h')))]),iff(cmp('lt',L('MinY',V('h')),V('fit miny')),[setv('fit miny',L('MinY',V('h')))]),iff(cmp('gt',L('MaxY',V('h')),V('fit maxy')),[setv('fit maxy',L('MaxY',V('h')))]),change('h',1)]),setv('Zoom',420/(V('fit maxx')-V('fit minx'))),iff(cmp('gt',V('Zoom'),210/(V('fit maxy')-V('fit miny'))),[setv('Zoom',210/(V('fit maxy')-V('fit miny')))]),iff(cmp('gt',V('Zoom'),4),[setv('Zoom',4)]),iff(cmp('lt',V('Zoom'),.15),[setv('Zoom',.15)]),setv('Camera X',(V('fit minx')+V('fit maxx'))/2),setv('Camera Y',(V('fit miny')+V('fit maxy'))/2)])
# Editable points: endpoint snapping at stroke ends; optional five-unit grid.
proc('mouse world',[setv('World X',V('Mouse X')/V('Zoom')+V('Camera X')),setv('World Y',(-20-V('Mouse Y'))/V('Zoom')+V('Camera Y')),iff(cmp('equals',V('Grid'),1),[setv('World X',mathop('round',V('World X')/5)*5),setv('World Y',mathop('round',V('World Y')/5)*5)])])
proc('snap endpoint',[setv('snap distance',7/V('Zoom')),setv('h',1),loop(length('LX'),[setv('snap x',L('LX',V('h'))),setv('snap y',L('LY',V('h'))),loop(2,[setv('snap d',mathop('sqrt',(V('World X')-V('snap x'))*(V('World X')-V('snap x'))+(V('World Y')-V('snap y'))*(V('World Y')-V('snap y')))),iff(cmp('lt',V('snap d'),V('snap distance')),[setv('World X',V('snap x')),setv('World Y',V('snap y')),setv('snap distance',V('snap d'))]),setv('snap x',L('LX',V('h'))+L('DX',V('h'))),setv('snap y',L('LY',V('h'))+L('DY',V('h')))]),change('h',1)])])
# All geometry mutations update twelve aligned lists in one warp transaction.
proc('append segment',[setv('dx',V('Draw X')-V('Last X')),setv('dy',V('Draw Y')-V('Last Y')),setv('distance',mathop('sqrt',V('dx')*V('dx')+V('dy')*V('dy'))),iff(AND(cmp('gt',V('distance'),.05),cmp('lt',length('LX'),3000)),[setv('ax',V('Last X')),setv('ay',V('Last Y')),iff(cmp('lt',V('dx'),0),[setv('ax',V('Draw X')),setv('ay',V('Draw Y')),setv('dx',0-V('dx')),setv('dy',0-V('dy'))])]+[add(k,v) for k,v in [('LX',V('ax')),('LY',V('ay')),('DX',V('dx')),('DY',V('dy')),('NX',(0-V('dy'))/V('distance')),('NY',V('dx')/V('distance')),('InvSq',1/(V('distance')*V('distance'))),('Material',V('Brush')),('MinX',V('ax')-10),('MaxX',V('ax')+V('dx')+10),('MinY',V('ay')+V('dy')*.5-mathop('abs',V('dy'))*.5-10),('MaxY',V('ay')+V('dy')*.5+mathop('abs',V('dy'))*.5+10)]]+mark_line(globals(),length('LX'),1)+[setv('Grid ready',0)]),setv('Last X',V('Draw X')),setv('Last Y',V('Draw Y'))])
proc('append stroke',[setv('target x',V('World X')),setv('target y',V('World Y')),setv('stroke dx',V('target x')-V('Last X')),setv('stroke dy',V('target y')-V('Last Y')),setv('stroke length',mathop('sqrt',V('stroke dx')*V('stroke dx')+V('stroke dy')*V('stroke dy'))),iff(cmp('gt',V('stroke length'),.1),[setv('parts',mathop('ceiling',V('stroke length')/8)),setv('step dx',V('stroke dx')/V('parts')),setv('step dy',V('stroke dy')/V('parts')),loop(V('parts'),[setv('Draw X',V('Last X')+V('step dx')),setv('Draw Y',V('Last Y')+V('step dy')),call('append segment')])])])
# Pencil stabilizer: the brush trails the pointer by 8 screen px when smoothing is on.
proc('pull brush',[setv('pull dx',V('World X')-V('Pen brush X')),setv('pull dy',V('World Y')-V('Pen brush Y')),setv('pull distance',mathop('sqrt',V('pull dx')*V('pull dx')+V('pull dy')*V('pull dy'))),setv('pull reach',8/V('Zoom')),iff(cmp('equals',V('Setting smooth draw'),0),[setv('Pen brush X',V('World X')),setv('Pen brush Y',V('World Y'))]),iff(AND(cmp('equals',V('Setting smooth draw'),1),cmp('gt',V('pull distance'),V('pull reach'))),[setv('pull keep',(V('pull distance')-V('pull reach'))/V('pull distance')),change('Pen brush X',V('pull dx')*V('pull keep')),change('Pen brush Y',V('pull dy')*V('pull keep'))]),setv('World X',V('Pen brush X')),setv('World Y',V('Pen brush Y'))])
# Erase distance test for line index 'name'. The best line keeps the lowest index among equal distances, matching an ascending scan.
def erase_test(name):
 i=V(name)
 return [setv('along',((V('World X')-L('LX',i))*L('DX',i)+(V('World Y')-L('LY',i))*L('DY',i))*L('InvSq',i)),iff(cmp('lt',V('along'),0),[setv('along',0)]),iff(cmp('gt',V('along'),1),[setv('along',1)]),setv('erase dx',V('World X')-L('LX',i)-L('DX',i)*V('along')),setv('erase dy',V('World Y')-L('LY',i)-L('DY',i)*V('along')),setv('erase distance',mathop('sqrt',V('erase dx')*V('erase dx')+V('erase dy')*V('erase dy'))),
  iff(OR(cmp('lt',V('erase distance'),V('best distance')),AND(cmp('equals',V('erase distance'),V('best distance')),AND(cmp('gt',V('erase id'),0),cmp('lt',i,V('erase id'))))),[setv('best distance',V('erase distance')),setv('erase id',i)])]
# Cell walk: every line whose padded AABB reaches the cell is in its chain.
proc('erase cell walk',[setv('erase slot',op('mod',V('erase cx')*7919+V('erase cy'),V('Grid size'))+1),setv('erase key',V('erase cx')*100000+V('erase cy')),setv('erase node',L('Grid heads',V('erase slot'))),until(cmp('equals',V('erase node'),0),[iff(cmp('equals',L('Grid cell',V('erase node')),V('erase key')),[setv('erase h',L('Grid line',V('erase node')))]+erase_test('erase h')),setv('erase node',L('Grid next',V('erase node')))])])
# With the grid valid and the eraser radius <= 74 world units, a line within the radius lies in one of the 3x3 cells around the pointer (its padded AABB is within 10 of the segment; the radius minus 10 is at most 64).
# After a deletion the grid is stale until the next timeline rebuild, so the full scan is used.
walk_cells=[]
for dx in (-1,0,1):
 for dy in (-1,0,1):
  walk_cells+=[setv('erase cx',V('erase gx')+dx),setv('erase cy',V('erase gy')+dy),call('erase cell walk')]
proc('erase under pointer',[setv('Erase radius',(9+9*V('Setting large eraser'))/V('Zoom')),setv('best distance',V('Erase radius')),setv('erase id',0),
 iff(AND(cmp('equals',V('Grid ready'),1),NOT(cmp('gt',V('Erase radius'),74))),[
  setv('erase gx',mathop('floor',V('World X')/64)),setv('erase gy',mathop('floor',V('World Y')/64)),
 ]+walk_cells,[
  setv('h',1),loop(length('LX'),erase_test('h')+[change('h',1)]),
 ]),
 iff(cmp('gt',V('erase id'),0),[call('delete eraser hit'),setv('Erase hit',1)])])
# Continuous erasing: a sample erases until the radius is clear, at most 12 lines per sample.
proc('erase sample',[setv('Erase hit',1),setv('erase passes',0),until(OR(cmp('equals',V('Erase hit'),0),cmp('gt',V('erase passes'),11)),[setv('Erase hit',0),change('erase passes',1),call('erase under pointer')])])
# Sweep from the previous pointer position to the current one, sampling every radius/2 world units.
proc('sweep erase',[setv('sweep end X',V('World X')),setv('sweep end Y',V('World Y')),setv('sweep dx',V('sweep end X')-V('Erase last X')),setv('sweep dy',V('sweep end Y')-V('Erase last Y')),setv('sweep count',mathop('ceiling',mathop('sqrt',V('sweep dx')*V('sweep dx')+V('sweep dy')*V('sweep dy'))/((9+9*V('Setting large eraser'))/V('Zoom')/2))),iff(cmp('lt',V('sweep count'),1),[setv('sweep count',1)]),setv('sweep k',0),loop(V('sweep count'),[change('sweep k',1),setv('World X',V('Erase last X')+V('sweep dx')*V('sweep k')/V('sweep count')),setv('World Y',V('Erase last Y')+V('sweep dy')*V('sweep k')/V('sweep count')),call('erase sample')]),setv('World X',V('sweep end X')),setv('World Y',V('sweep end Y'))])
# Input is coordinated in one loop. No UI hat can race a render's work variables.
from track_code import install as install_track_code, render_code, assets_code
install_track_code(globals())
from mobile import install as install_mobile
install_mobile(globals())
from play_view import install as install_play_view, define_input as define_play_input, render as render_play_view, build_assets as build_play_assets
install_play_view(globals())
from menus import define_controls, render_controls, render_popups, build_assets
menus,controls=define_controls(globals())
from menus import hit
define_play_input(globals())
in_canvas=AND(cmp('lt',V('Mouse Y'),100),cmp('gt',V('Mouse Y'),CANVAS_BOTTOM))
proc('pointer down normal',[iff(cmp('equals',V('Help'),1),[setv('Help',0)],[call('handle toolbar'),iff(AND(cmp('equals',V('UI hit'),0),AND(in_canvas,cmp('equals',V('Editing'),1))),[call('mouse world'),setv('Drawing',1),setv('Last mouse X',V('Mouse X')),setv('Last mouse Y',V('Mouse Y')),iff(NOT(cmp('equals',V('Tool'),3)),[call('begin change')]),iff(cmp('equals',V('Tool'),2),[call('begin erase gesture'),setv('Erase last X',V('World X')),setv('Erase last Y',V('World Y'))]),iff(OR(cmp('equals',V('Tool'),0),cmp('equals',V('Tool'),1)),[call('snap endpoint'),setv('Last X',V('World X')),setv('Last Y',V('World Y')),setv('Anchor X',V('World X')),setv('Anchor Y',V('World Y')),setv('Pen brush X',V('World X')),setv('Pen brush Y',V('World Y'))]),iff(cmp('equals',V('Tool'),4),[setv('Spawn X',V('World X')),setv('Spawn Y',V('World Y')),setv('Grid ready',0),setv('Drawing',0)]),iff(cmp('equals',V('Tool'),5),[setv('Goal X',V('World X')),setv('Goal Y',V('World Y')),setv('Goal enabled',1),setv('Timeline restart',1),setv('Drawing',0)])])])])
proc('pointer down',[
 iff(cmp('gt',V('Code open'),0),[call('code pointer')],[
  iff(cmp('equals',V('Confirm open'),1),[call('confirmation pointer')],[
   iff(cmp('equals',V('Full play'),1),[call('full play pointer')],[
    iff(AND(timeline_hit(globals()),AND(cmp('equals',V('Menu'),0),cmp('equals',V('Help'),0))),
        [call('start timeline scrub')],[call('pointer down normal')]),
   ]),
  ]),
 ]),
])
proc('pointer drag',[iff(AND(cmp('equals',V('Drawing'),1),cmp('equals',V('Editing'),1)),[iff(cmp('equals',V('Tool'),3),[change('Camera X',(V('Last mouse X')-V('Mouse X'))/V('Zoom')),change('Camera Y',(V('Mouse Y')-V('Last mouse Y'))/V('Zoom'))],[iff(in_canvas,[call('mouse world'),iff(cmp('equals',V('Tool'),0),[call('pull brush'),iff(cmp('gt',mathop('sqrt',(V('World X')-V('Last X'))*(V('World X')-V('Last X'))+(V('World Y')-V('Last Y'))*(V('World Y')-V('Last Y')))*V('Zoom'),3),[call('append stroke')])]),iff(cmp('equals',V('Tool'),2),[iff(cmp('equals',V('Setting sweep erase'),1),[call('sweep erase')],[call('erase under pointer')]),setv('Erase last X',V('World X')),setv('Erase last Y',V('World Y'))])])]),setv('Last mouse X',V('Mouse X')),setv('Last mouse Y',V('Mouse Y'))])])
proc('pointer up',[iff(AND(cmp('equals',V('Drawing'),1),OR(cmp('equals',V('Tool'),0),cmp('equals',V('Tool'),1))),[iff(in_canvas,[call('mouse world'),call('snap endpoint'),call('append stroke')])]),setv('Drawing',0)])
# Liang-Barsky clipping prevents Scratch's sprite fencing from distorting offscreen lines.
def screenx(x):return (x-V('Camera X'))*V('Zoom')
def screeny(y):return -20+20*V('Full play')-(y-V('Camera Y'))*V('Zoom')
proc('clip boundary',[iff(cmp('equals',V('clip p'),0),[iff(cmp('lt',V('clip q'),0),[setv('clip valid',0)])],[setv('clip r',V('clip q')/V('clip p')),iff(cmp('lt',V('clip p'),0),[iff(cmp('gt',V('clip r'),V('clip t1')),[setv('clip valid',0)]),iff(cmp('gt',V('clip r'),V('clip t0')),[setv('clip t0',V('clip r'))])],[iff(cmp('lt',V('clip r'),V('clip t0')),[setv('clip valid',0)]),iff(cmp('lt',V('clip r'),V('clip t1')),[setv('clip t1',V('clip r'))])])])])
def costume_to(name):return stmt('looks_switchcostumeto',{'COSTUME':name})
# Fast paths: strictly inside the clip rectangle draws directly; strictly outside one side draws nothing.
# Boundary endpoints use the Liang-Barsky path, so every drawn point stays identical.
def clip_nest(conds,body):
 for c in reversed(conds):body=[iff(c,body)]
 return body
def clip_draw_direct():return [stmt('pen_penUp'),goto(V('sx1')+V('clip dx')*0,V('sy1')+V('clip dy')*0),stmt('pen_penDown'),goto(V('sx1')+V('clip dx')*1,V('sy1')+V('clip dy')*1),stmt('pen_penUp')]
def clip_fallback():return [setv('clip t0',0),setv('clip t1',1),setv('clip valid',1)]+sum(([setv('clip p',p),setv('clip q',q),call('clip boundary')] for p,q in [(0-V('clip dx'),V('sx1')+239),(V('clip dx'),239-V('sx1')),(0-V('clip dy'),V('sy1')-V('Canvas bottom')),(V('clip dy'),V('Canvas top')-V('sy1'))]),[])+[iff(cmp('equals',V('clip valid'),1),[stmt('pen_penUp'),goto(V('sx1')+V('clip dx')*V('clip t0'),V('sy1')+V('clip dy')*V('clip t0')),stmt('pen_penDown'),goto(V('sx1')+V('clip dx')*V('clip t1'),V('sy1')+V('clip dy')*V('clip t1')),stmt('pen_penUp')])]
inside=[cmp('gt',V('sx1'),-239),cmp('lt',V('sx1'),239),cmp('gt',V('sx2'),-239),cmp('lt',V('sx2'),239),cmp('gt',V('sy1'),V('Canvas bottom')),cmp('lt',V('sy1'),V('Canvas top')),cmp('gt',V('sy2'),V('Canvas bottom')),cmp('lt',V('sy2'),V('Canvas top'))]
outside=[iff(cmp('lt',V('sx1'),-239),[iff(cmp('lt',V('sx2'),-239),[setv('clip path',2)])]),iff(cmp('gt',V('sx1'),239),[iff(cmp('gt',V('sx2'),239),[setv('clip path',2)])]),iff(cmp('lt',V('sy1'),V('Canvas bottom')),[iff(cmp('lt',V('sy2'),V('Canvas bottom')),[setv('clip path',2)])]),iff(cmp('gt',V('sy1'),V('Canvas top')),[iff(cmp('gt',V('sy2'),V('Canvas top')),[setv('clip path',2)])])]
proc('draw clipped segment',[setv('clip dx',V('sx2')-V('sx1')),setv('clip dy',V('sy2')-V('sy1')),setv('clip path',0)]+clip_nest(inside,[setv('clip path',1)])+[iff(cmp('equals',V('clip path'),1),clip_draw_direct()),iff(cmp('equals',V('clip path'),0),outside+[iff(cmp('equals',V('clip path'),0),clip_fallback())])])
def line(x,y,xx,yy):return [setv('sx1',x),setv('sy1',y),setv('sx2',xx),setv('sy2',yy),call('draw clipped segment')]
def worldline(x,y,xx,yy):return line(screenx(x),screeny(y),screenx(xx),screeny(yy))
def segment(a,b):return worldline(L('X',a),L('Y',a),L('X',b),L('Y',b))
proc('stamp costume',[stmt('looks_show'),costume_to(V('Costume')),goto(V('Stamp X'),V('Stamp Y')),stmt('pen_stamp'),stmt('looks_hide')])
def stamp(name,x=0,y=0):return [setv('Costume',name),setv('Stamp X',x),setv('Stamp Y',y),call('stamp costume')]
proc('write text',[setv('letter',1),loop(Expr('operator_length',{'STRING':V('Text')}),[setv('Costume',cat('glyph ',Expr('operator_letter_of',{'LETTER':V('letter'),'STRING':V('Text')}))),setv('Stamp X',V('Text X')),setv('Stamp Y',V('Text Y')),call('stamp costume'),change('Text X',6),change('letter',1)])])
def text(t,x,y):return [setv('Text',t),setv('Text X',x),setv('Text Y',y),call('write text')]
# Static costumes carry actual labels; selected/hover/disabled states are explicit.
render=[setv('Canvas top',100+79*V('Full play')),setv('Canvas bottom',CANVAS_BOTTOM-(179+CANVAS_BOTTOM)*V('Full play')),stmt('pen_clear'),costume_to('blank'),iff(cmp('equals',V('Grid'),1),[color('#e5e1da'),size(1),setv('grid spacing',20),iff(cmp('lt',V('Zoom'),.7),[setv('grid spacing',100)]),setv('grid x',mathop('floor',(V('Camera X')-240/V('Zoom'))/V('grid spacing'))*V('grid spacing')),loop(480/(V('Zoom')*V('grid spacing'))+2,worldline(V('grid x'),V('Camera Y')-150/V('Zoom'),V('grid x'),V('Camera Y')+150/V('Zoom'))+[change('grid x',V('grid spacing'))]),setv('grid y',mathop('floor',(V('Camera Y')-140/V('Zoom'))/V('grid spacing'))*V('grid spacing')),loop(280/(V('Zoom')*V('grid spacing'))+2,worldline(V('Camera X')-240/V('Zoom'),V('grid y'),V('Camera X')+240/V('Zoom'),V('grid y'))+[change('grid y',V('grid spacing'))])]),setv('j',1),size(2),loop(length('LX'),[iff(AND(AND(cmp('gt',L('MaxX',V('j')),V('Camera X')-250/V('Zoom')),cmp('lt',L('MinX',V('j')),V('Camera X')+250/V('Zoom'))),AND(cmp('gt',L('MaxY',V('j')),V('Camera Y')-(130+55*V('Full play'))/V('Zoom')),cmp('lt',L('MinY',V('j')),V('Camera Y')+(140+45*V('Full play'))/V('Zoom')))),[color('#30332f'),iff(cmp('equals',L('Material',V('j')),1),[color('#a66328')]),iff(cmp('equals',L('Material',V('j')),2),[color('#58766d')]),iff(cmp('equals',L('Material',V('j')),3),[color('#b6b1a9')]),iff(cmp('gt',L('Material',V('j')),3),[color('#a13d32')])]+worldline(L('LX',V('j')),L('LY',V('j')),L('LX',V('j'))+L('DX',V('j')),L('LY',V('j'))+L('DY',V('j')))),change('j',1)]),color('#9a433b'),size(2)]
chainids=[idx[k] for k in body['parts']['SCARF']]
for a,b in zip(chainids,chainids[1:]):render+=segment(a,b)
# Artwork follows each simulated bone, including detached limbs.
from rider_art import draw_rider
render += draw_rider(globals())
# Flags and previews are clipped along with terrain.
render += [iff(cmp('equals',V('Editing'),1),[color('#58766d'),size(1.5)]+worldline(V('Spawn X'),V('Spawn Y')+5,V('Spawn X'),V('Spawn Y')-13)+worldline(V('Spawn X'),V('Spawn Y')-13,V('Spawn X')+6,V('Spawn Y')-10))]+ [iff(cmp('equals',V('Goal enabled'),1),[color('#58766d'),size(2)]+worldline(V('Goal X'),V('Goal Y')+7,V('Goal X'),V('Goal Y')-22)+worldline(V('Goal X'),V('Goal Y')-22,V('Goal X')+9,V('Goal Y')-22)+worldline(V('Goal X')+9,V('Goal Y')-22,V('Goal X')+9,V('Goal Y')-15)+worldline(V('Goal X')+9,V('Goal Y')-15,V('Goal X'),V('Goal Y')-15))]
render += [iff(AND(cmp('equals',V('Drawing'),1),cmp('equals',V('Tool'),1)),[color('#a66328'),size(1)]+worldline(V('Anchor X'),V('Anchor Y'),V('World X'),V('World Y')))]
render += [iff(AND(AND(cmp('equals',V('Editing'),1),cmp('equals',V('Help'),0)),in_canvas),[color('#918b82'),size(1),iff(cmp('equals',V('Tool'),2),[setv('angle',0),setv('Eraser px',9+9*V('Setting large eraser')),loop(12,line(V('Mouse X')+V('Eraser px')*mathop('cos',V('angle')),V('Mouse Y')+V('Eraser px')*mathop('sin',V('angle')),V('Mouse X')+V('Eraser px')*mathop('cos',V('angle')+30),V('Mouse Y')+V('Eraser px')*mathop('sin',V('angle')+30))+[change('angle',30)])]),iff(OR(cmp('equals',V('Tool'),4),cmp('equals',V('Tool'),5)),line(V('Mouse X'),V('Mouse Y'),V('Mouse X'),V('Mouse Y')+22)+line(V('Mouse X'),V('Mouse Y')+22,V('Mouse X')+10,V('Mouse Y')+22))])]
# Toolbar masking and stamps occupy the same pen layer after scene drawing.
chrome_render = stamp('chrome')
chrome_render += render_controls(globals())
chrome_render += render_timeline(globals())
# Status text is real runtime data, not a static label.
chrome_render += [setv('status','Edit'),iff(cmp('equals',V('State'),1),[setv('status','Riding')]),iff(cmp('equals',V('State'),2),[setv('status','Paused')]),iff(cmp('equals',V('State'),3),[setv('status','Crashed')]),iff(cmp('equals',V('State'),4),[setv('status','Finished')]),iff(cmp('equals',V('State'),5),[setv('status','Preview limit')])]+text(cat(V('status'),'   ',length('LX'),' lines   ',mathop('round',V('Zoom')*100),'%'),-228,-166)
chrome_render += [iff(OR(cmp('equals',V('Editing'),0),cmp('gt',V('Frame'),0)),text(cat(mathop('round',V('Frame')/30*100)/100,'s   ',mathop('round',V('Timeline speed')*30),'u/s'),85,-166),[iff(cmp('equals',V('Mobile'),0),text('G grid   H home   Space test',70,-166))])]
chrome_render += [iff(AND(cmp('gt',V('Notice'),0),cmp('lt',Expr('sensing_timer'),V('Notice until'))),stamp(cat('notice ',V('Notice')),0,-114))]
chrome_render += [iff(cmp('equals',V('Editing'),0),[
 iff(cmp('equals',V('State'),3),stamp(cat('crashed ',V('Mobile')),0,-95)),
 iff(cmp('equals',V('State'),4),stamp(cat('finished ',V('Mobile')),0,12)),
]),iff(cmp('equals',V('Help'),1),stamp(cat('help ',V('Mobile')),0,-15))]
proc('render scene',render)
proc('render chrome',chrome_render)
proc('render overlays',render_popups(globals())+render_code(globals()))
proc('render',[call('render scene'),iff(cmp('equals',V('Full play'),0),[call('render chrome')],render_play_view(globals())),call('render overlays')])
# Native hats queue taps; the coordinator executes actions between render transactions.
lists['Input keys']=['Input keys',[]]
shortcuts=[('space','play or pause'),('r','retry'),('n','step once'),('z','request undo'),('y','request redo'),('f','fit track'),('s','request save track'),('l','request load track'),('e','request return to editor'),('g','toggle grid'),('x','detach rider')]
proc('editor keyboard',[iff(cmp('equals',V('Input key'),k),[call(action)]) for k,action in shortcuts]+[iff(AND(cmp('equals',V('Input key'),'h'),cmp('equals',V('Editing'),1)),[call('home view')])]+[iff(AND(cmp('equals',V('Input key'),str(i+1)),cmp('equals',V('Editing'),1)),[setv('Tool',i)]) for i in range(6)])
proc('keyboard normal',[setv('Input key',''),iff(cmp('gt',length('Input keys'),0),[setv('Input key',L('Input keys',1)),delete('Input keys',1),iff(cmp('equals',V('Confirm open'),1),[call('confirmation keyboard')],[iff(cmp('equals',V('Menu'),0),[iff(cmp('equals',V('Help'),0),[call('editor keyboard')])],[call('menu keyboard')])])]),iff(AND(AND(cmp('equals',V('Editing'),1),cmp('equals',V('Help'),0)),cmp('equals',V('Menu'),0)),[iff(key('right arrow'),[change('Camera X',8/V('Zoom'))]),iff(key('left arrow'),[change('Camera X',-8/V('Zoom'))]),iff(key('up arrow'),[change('Camera Y',-8/V('Zoom'))]),iff(key('down arrow'),[change('Camera Y',8/V('Zoom'))])])])
proc('keyboard',[iff(cmp('gt',V('Code open'),0),[iff(cmp('gt',length('Input keys'),0),[setv('Input key',L('Input keys',1)),delete('Input keys',1),call('code keyboard')])],[call('keyboard normal')])])
# The controller serializes subsystem requests between input and rendering.
# Renderer requests a redraw before its message completes, supplying the frame
# boundary. An extra timed wait here would halve the native frame rate.
no_overlay = AND(AND(cmp('equals',V('Help'),0),cmp('equals',V('Menu'),0)),
                 AND(cmp('equals',V('Confirm open'),0),cmp('equals',V('Code open'),0)))
timeline_pending = OR(cmp('equals',V('Timeline ready'),0),
                      OR(cmp('equals',V('Grid ready'),0),cmp('equals',V('Timeline restart'),1)))
read_mouse_position = [setv('Mouse X',Expr('sensing_mousex')),setv('Mouse Y',Expr('sensing_mousey'))]
main_loop = read_mouse_position + [
 setv('Mouse down',Expr('sensing_mousedown')),
 iff(cmp('gt',V('Menu'),0),[call('menu hover')]),
 call('keyboard'),
 setv('Click handled',0),
 iff(AND(cmp('gt',V('Queued steps'),0),cmp('equals',V('Code open'),0)),[
  change('Queued steps',-1),call('step once'),
 ]),
 iff(cmp('equals',V('Queued click'),1),[
  setv('Click handled',1),setv('Mouse X',V('Click X')),setv('Mouse Y',V('Click Y')),
  setv('Queued click',0),call('pointer down'),
 ] + read_mouse_position),
 iff(AND(AND(cmp('equals',V('Click handled'),0),cmp('equals',V('Mouse down'),1)),
         AND(AND(cmp('equals',V('Mouse was down'),0),cmp('equals',V('Editing'),1)),
             AND(no_overlay,AND(in_canvas,cmp('lt',V('Tool'),4))))),[
  call('pointer down'),
 ]),
 iff(cmp('equals',V('Mouse down'),1),[
  iff(cmp('equals',V('Timeline dragging'),1),[call('scrub timeline')],[call('pointer drag')]),
 ],[
  iff(cmp('equals',V('Mouse was down'),1),[
   iff(cmp('equals',V('Timeline dragging'),1),[call('scrub timeline')],[call('pointer up')]),
  ]),
  setv('Timeline dragging',0),
 ]),
 setv('Mouse was down',V('Mouse down')),
 # Track edits invalidate the cache during the gesture. Paint the loading
 # indicator after release before running the first rebuild batch.
 iff(AND(cmp('equals',V('Drawing'),0),timeline_pending),[
  iff(cmp('equals',V('Timeline loading'),1),[
   call('update timeline'),setv('Timeline loading',1-V('Timeline ready')),
  ],[setv('Timeline loading',1)]),
 ],[setv('Timeline loading',0)]),
 iff(AND(AND(cmp('equals',V('Playing'),1),cmp('equals',V('Timeline ready'),1)),
         AND(cmp('equals',V('Timeline loading'),0),no_overlay)),[
  change('Timeline target',1),setv('Timeline seek focus',1),
 ]),
 call('show timeline frame'),
 iff(cmp('equals',V('Editing'),1),[
  setv('Edit camera X',V('Camera X')),setv('Edit camera Y',V('Camera Y')),setv('Edit zoom',V('Zoom')),
 ]),
 call('render'),
 iff(cmp('equals',V('Code open'),2),[call('prompt track code')]),
 iff(cmp('equals',V('Capture hold'),1),[
  setv('Capture ready',1),stmt('control_wait_until',{'CONDITION':cmp('equals',V('Capture hold'),0)}),setv('Capture ready',0),
 ]),
]
script('event_whenflagclicked',[stmt('looks_hide'),stmt('pen_penUp'),setv('Mobile',1),setv('Full play',0),setv('Editing',1),setv('Playing',0),setv('Tool',0),setv('Brush',0),setv('Drawing',0),setv('Mouse was down',0),setv('Help',0),setv('Menu',0),setv('Confirm open',0),setv('Code open',0),stmt('data_hidelist',{}, {'LIST':['Track code','Track code']}),setv('Pending edit action',0),setv('Requested edit action',0),setv('Queued click',0),setv('Queued steps',0),setv('Capture hold',0),setv('Capture ready',0),clear('Input keys'),setv('Grid',0),setv('Grid ready',0),setv('Notice',0)]+clearstack('Undo')+clearstack('Redo')+[
 setv('State',0),setv('Frame',0),setv('Ride result',1),setv('Timeline target',0),
 setv('Timeline loading',0),setv('Timeline ready',0),setv('Timeline current pose',0),clear('Timeline Ride result'),
 setv('Timeline dragging',0),setv('Timeline detach frame',0),setv('Timeline refocus',0),setv('Timeline seek focus',0),
 call('home view'),('forever',main_loop),
])
# SVG assets are geometric editor controls, not a generated mockup.
assets={}
def costume(name,svg,cx,cy):
 h=hashlib.md5(svg.encode()).hexdigest();assets[h+'.svg']=svg;return {'name':name,'assetId':h,'md5ext':h+'.svg','dataFormat':'svg','rotationCenterX':cx,'rotationCenterY':cy,'bitmapResolution':1}
def svg(w,h,content):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">{content}</svg>'
costumes=[costume('blank',svg(2,2,'<path fill="none" d="M0 0h2v2H0z"/>'),1,1)]
bg=costume('paper',svg(480,360,'<path fill="#faf8f5" d="M0 0h480v360H0z"/>'),240,180)
costumes += [costume('chrome',svg(480,360,'<path fill="#f1eee8" d="M0 0h480v80H0zM0 310h480v50H0z"/><path stroke="#d6d1c8" d="M0 79.5h480M0 310.5h480M0 334.5h480"/>'),240,180)]
build_assets(globals())
assets_code(globals())
build_play_assets(globals())
build_timeline_assets(globals())
for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .:/%+-?':
 costumes.append(costume('glyph '+ch,svg(9,16,f'<text x="0" y="11" font-family="monospace" font-size="10" fill="#48473f">{html.escape(ch)}</text>'),0,8))
for num,label in [(1,'Saved in this project. Download .sb3 to keep your work.'),(2,'Saved track loaded. Undo restores the previous track.'),(3,'Draw below the start flag, then place a goal and press Play.'),(4,'Track code loaded. Undo restores the previous track.')]:
 costumes.append(costume('notice '+str(num),svg(466,23,f'<rect width="466" height="23" rx="3" fill="#f1eee8" stroke="#d6d1c8"/><text x="233" y="15" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#30332f">{label}</text>'),233,11.5))
for name,label,sub in [('crashed','Crash','R: retry    E: edit track'),('finished','Finish reached','R: ride again    E: keep editing')]:
 for mobile in [0,1]:
  detail='Use Retry to ride again or Edit to change the track.' if mobile else sub
  costumes.append(costume(name+' '+str(mobile),svg(280,66,f'<rect x=".5" y=".5" width="279" height="65" rx="4" fill="#faf8f5" stroke="#b6b1a9"/><text x="140" y="26" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#30332f">{label}</text><text x="140" y="48" text-anchor="middle" font-family="sans-serif" font-size="10.5" fill="#48473f">{detail}</text>'),140,33))
help_common=['Draw a track. Keep the rider on the sled to reach the goal.','Pencil draws a stroke. Line previews a straight segment.','Erase removes lines. Pan drags the view. Start / Goal place flags.','Edit / Play selects mode. Run / Pause controls playback.','Drag the timeline to pause at a frame. Edit to update that frame.','Settings smooths pencil strokes, sweeps erasing and enlarges the eraser.']
for mobile in [0,1]:
 help_lines=help_common+(['Start with touch controls. Any key enables keyboard hints.','The eraser fills one skipped line between recent erased neighbors.'] if mobile else ['1-6 tools   Z undo   Y redo   Arrows pan   G grid + snap','H home   F fit track   S save slot   L load slot'])+['Track > Save track code gives a compact code you can copy.','Load track code restores it. Save slot stays inside the project.','Play has a fullscreen button to hide the editor. Tap to close.']
 content='<rect x=".5" y=".5" width="453" height="225" rx="4" fill="#faf8f5" stroke="#b6b1a9"/>'
 for i,label in enumerate(help_lines):content+=f'<text x="14" y="{22+i*19}" font-family="sans-serif" font-size="10.5" fill="#30332f">{html.escape(label)}</text>'
 costumes.append(costume('help '+str(mobile),svg(454,226,content),227,113))

def target(name,stage=False,blocks=None,costumes=None,**kw):return dict(isStage=stage,name=name,variables={},lists={},broadcasts={},blocks=blocks or {},comments={},currentCostume=0,costumes=costumes or [],sounds=[],volume=100,layerOrder=0 if stage else 1,**kw)
engine_blocks=B
B={};core.B=B
stage_pointer = NOT(no_overlay)
for condition in [
 cmp('equals',V('Full play'),1),cmp('gt',Expr('sensing_mousey'),100),
 cmp('lt',Expr('sensing_mousey'),CANVAS_BOTTOM),
 AND(cmp('equals',V('Editing'),1),cmp('gt',V('Tool'),3)),
]:
 stage_pointer = OR(stage_pointer,condition)
script('event_whenstageclicked',[iff(stage_pointer,[setv('Click X',Expr('sensing_mousex')),setv('Click Y',Expr('sensing_mousey')),setv('Queued click',1)])])
for input_key in ['space','r','n','z','y','h','f','s','l','e','g','x','q','enter','up arrow','down arrow']+[str(i+1) for i in range(6)]:
 script('event_whenkeypressed',[iff(AND(NOT(cmp('equals',V('Code open'),2)),OR(cmp('gt',V('Menu'),0),NOT(OR(cmp('equals',input_key,'up arrow'),cmp('equals',input_key,'down arrow'))))),[add('Input keys',input_key)])],{'KEY_OPTION':[input_key,None]})
script('event_whenkeypressed',[iff(cmp('equals',V('Mobile'),1),[setv('Mobile',0)])],{'KEY_OPTION':['any',None]})
stage_blocks=B
B=engine_blocks;core.B=B
stage=target('Stage',True,blocks=stage_blocks,costumes=[bg],tempo=60,videoTransparency=50,videoState='off',textToSpeechLanguage=None);stage['variables']=variables;stage['lists']=lists
engine=target('Line Rider core',blocks=B,costumes=costumes,visible=False,x=0,y=0,size=100,direction=90,draggable=False,rotationStyle='all around')
engine['comments']={'credits':{'blockId':None,'x':20,'y':0,'width':480,'height':260,'minimized':False,'text':'Physics adapted from lr-core 0.8.2 by David Lu (conundrumer). Commit ce48ebed967d24ff4582995b31342440901f913d. Native Scratch editor, uniform spatial grid, clipping and material extensions. See README.\n\n'+(ROOT/'LICENSE.lr-core.txt').read_text(encoding='utf-8-sig')}}
from prompt_history import make_sprite as make_prompt_history
history=make_prompt_history(ROOT,target,costume,svg)
project={'targets':[stage,engine,history],'monitors':[{'id':'Track code','mode':'list','opcode':'data_listcontents','params':{'LIST':'Track code'},'spriteName':None,'value':[],'width':444,'height':112,'x':18,'y':132,'visible':False}],'extensions':['pen'],'meta':{'semver':'3.0.0','vm':'0.2.0','agent':'lr-core-scratch-editor'}}
# Open on the same course restored by the Demo course action.
from clean_project import clean
release,report=clean(project)
from split_sprites import split as split_sprites
release,module_report=split_sprites(release,costume,svg)
report['blocks_after']=sum(len(t['blocks']) for t in release['targets'])
report['modules']=module_report
# Test hooks are separate; the delivered .sb3 contains no capture/step test state.
def write_project(path,data):
 used={c['md5ext'] for t in data['targets'] for c in t['costumes']}
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('project.json',json.dumps(data))
  for name in sorted(used):z.writestr(name,assets[name])
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--testing',action='store_true',help='also build a local project with test controls')
args=parser.parse_args()
write_project(ROOT/'dist/Line Rider.sb3',release)
if args.testing:
 test_project,_=clean(project,test_hooks=True)
 test_project,_=split_sprites(test_project,costume,svg)
 (ROOT/'dist/testing').mkdir(parents=True,exist_ok=True)
 write_project(ROOT/'dist/testing/Line Rider.sb3',test_project)
(ROOT/'dist/project.json').write_text(json.dumps(release,indent=2),encoding='utf-8')
(ROOT/'dist/build-report.json').write_text(json.dumps(report,indent=2))
print(f"Built editor: {report['blocks_after']} blocks, {len(costumes)} costumes, {len(stage['lists']['LX'][1])} current track segments.")
print(json.dumps(report))

(ROOT/'dist/ui-controls.json').write_text(json.dumps({c['name']:{'x':c['x']+c['w']/2,'y':c['y']+c['h']/2} for c in controls},indent=2),encoding='utf-8')
