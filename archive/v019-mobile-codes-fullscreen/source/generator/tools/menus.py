"""Native Scratch dropdowns: one menu owns input until dismissed."""
def define_controls(api):
 globals().update(api)
 global menus,controls
 editing_off=cmp('equals',V('Editing'),0)
 editing_on=cmp('equals',V('Editing'),1)
 proc('select edit mode',[iff(editing_off,[call('edit track')])])
 proc('select play mode',[iff(editing_on,[call('prepare paused preview')])])
 proc('toggle finish goal',[iff(editing_on,[call('begin change'),setv('Goal enabled',1-V('Goal enabled'))])])
 proc('zoom in',[setv('Zoom',V('Zoom')*1.25),iff(cmp('gt',V('Zoom'),5),[setv('Zoom',5)])])
 proc('zoom out',[setv('Zoom',V('Zoom')/1.25),iff(cmp('lt',V('Zoom'),.15),[setv('Zoom',.15)])])
 proc('toggle grid',[setv('Grid',1-V('Grid'))])
 proc('detach rider',[iff(editing_off,[setv('Mounted',0)])])
 proc('toggle help',[setv('Help',1-V('Help'))])
 def row(label,shortcut='',action=None,disabled=None,checked=None,alt=None,edit_action=None):return dict(edit_action=edit_action,label=label,shortcut=shortcut,action=action or [],can_disable=disabled is not None,checkable=checked is not None,disabled=disabled or cmp('equals',0,1),checked=checked or cmp('equals',0,1),alt=alt)
 menus=[
  dict(id=1,x=8,top=36,w=208,rows=[row('New track',edit_action=1),row('Demo course',edit_action=2),None,row('Save slot','S',edit_action=3),row('Load saved slot','L',disabled=cmp('equals',V('Saved exists'),0),edit_action=4),None,row('Remove goal',alt='Restore goal',edit_action=5),None,row('Save track code',action=[call('save track code')]),row('Load track code',edit_action=9)]),
  dict(id=2,x=70,top=36,w=202,rows=[row('Undo','Z',disabled=cmp('equals',length('Undo Count'),0),edit_action=6),row('Redo','Y',disabled=cmp('equals',length('Redo Count'),0),edit_action=7),None,row('Step one frame','N',[call('step once')],OR(cmp('equals',V('Playing'),1),OR(cmp('equals',V('State'),4),AND(cmp('equals',V('State'),3),cmp('equals',V('Crash complete'),1))))),row('Detach rider','X',[call('detach rider')],editing_on),row('Return to editor','E',disabled=editing_on,edit_action=8)]),
  dict(id=3,x=126,top=36,w=208,rows=[row('Zoom in','+',[call('zoom in')]),row('Zoom out','-',[call('zoom out')]),row('Fit track','F',[call('fit track')]),row('Start view','H',[call('home view')],editing_off),None,row('Grid and snapping','G',[call('toggle grid')],checked=cmp('equals',V('Grid'),1))]),
  dict(id=4,x=184,top=36,w=190,rows=[row('Controls and storage',action=[call('toggle help')])]),
  dict(id=5,x=8,top=76,w=196,rows=[row(label,str(i+1),[setv('Tool',i)],editing_off,cmp('equals',V('Tool'),i)) for i,label in enumerate(['Pencil','Straight line','Eraser','Pan','Start flag','Goal flag'])]),
  dict(id=6,x=142,top=76,w=204,rows=[row(label,action=[setv('Brush',i)],disabled=editing_off,checked=cmp('equals',V('Brush'),i)) for i,label in enumerate(['Normal','Grip','Ice','Scenery'])])]
 for menu in menus:
  y=menu['top']+6;index=0
  for r in menu['rows']:
   if r is None:y+=8;continue
   index+=1;r.update(y=y,index=index);y+=26
  menu['h']=y-menu['top']+6;menu['count']=index
 controls=[
  dict(name='track',label='Track',x=8,y=7,w=56,h=26,menu=1),dict(name='edit',label='Edit',x=70,y=7,w=50,h=26,menu=2),dict(name='view',label='View',x=126,y=7,w=52,h=26,menu=3),dict(name='help',label='Help',x=184,y=7,w=50,h=26,menu=4),
  dict(name='play',label='Run',x=284,y=43,w=188/3,h=26,action=[call('play or pause')]),dict(name='retry',label='Retry',x=284+188/3,y=43,w=188/3,h=26,action=[call('retry')]),dict(name='mode',label='Step',x=284+376/3,y=43,w=188/3,h=26,action=[call('step once')],disabled=OR(cmp('equals',V('Playing'),1),OR(cmp('equals',V('State'),4),AND(cmp('equals',V('State'),3),cmp('equals',V('Crash complete'),1))))),
  dict(name='edit-mode',label='Edit',x=284,y=7,w=94,h=26,action=[call('select edit mode')]),dict(name='play-mode',label='Play',x=378,y=7,w=94,h=26,action=[call('select play mode')]),
  dict(name='full-play',label='Fullscreen',x=244,y=5,w=32,h=32,action=[call('toggle full play')],disabled=editing_on),
  dict(name='tool',label='Pencil',x=8,y=43,w=124,h=26,menu=5,disabled=editing_off),dict(name='material',label='Normal',x=142,y=43,w=114,h=26,menu=6,disabled=editing_off)]
 def hit(x,y,w,h):return AND(AND(cmp('gt',V('Mouse X'),x-240),cmp('lt',V('Mouse X'),x+w-240)),AND(cmp('lt',V('Mouse Y'),180-y),cmp('gt',V('Mouse Y'),180-y-h)))
 globals()['hit']=hit
 edit_actions={1:'new track',2:'demo track',3:'save track',4:'load track',5:'toggle finish goal',6:'undo',7:'redo',9:'load track code'}
 proc('perform requested edit action',[iff(cmp('equals',V('Requested edit action'),i),[call(action)]) for i,action in edit_actions.items()])
 proc('request edit action',[setv('Edit action available',1),iff(AND(cmp('equals',V('Requested edit action'),4),cmp('equals',V('Saved exists'),0)),[setv('Edit action available',0)]),iff(AND(cmp('equals',V('Requested edit action'),6),cmp('equals',length('Undo Count'),0)),[setv('Edit action available',0)]),iff(AND(cmp('equals',V('Requested edit action'),7),cmp('equals',length('Redo Count'),0)),[setv('Edit action available',0)]),iff(V('Edit action available'),[iff(editing_off,[setv('Pending edit action',V('Requested edit action')),setv('Confirm open',1),setv('Menu',0),setv('Drawing',0)],[call('perform requested edit action')])])])
 for i,action in edit_actions.items():proc('request '+action,[setv('Requested edit action',i),call('request edit action')])
 proc('request return to editor',[setv('Requested edit action',8),call('request edit action')])
 proc('cancel edit confirmation',[setv('Confirm open',0),setv('Pending edit action',0)])
 proc('accept edit confirmation',[setv('Requested edit action',V('Pending edit action')),setv('Confirm open',0),setv('Pending edit action',0),call('edit track'),call('perform requested edit action')])
 proc('confirmation pointer',[iff(hit(218,204,92,30),[call('cancel edit confirmation')]),iff(hit(322,204,112,30),[call('accept edit confirmation')])])
 proc('confirmation keyboard',[iff(cmp('equals',V('Input key'),'q'),[call('cancel edit confirmation')]),iff(cmp('equals',V('Input key'),'enter'),[call('accept edit confirmation')])])
 proc('code pointer',[iff(cmp('equals',V('Code open'),1),[iff(hit(354,281,96,29),[call('close track code')])]),iff(cmp('equals',V('Code open'),3),[iff(hit(234,281,96,29),[call('close track code')]),iff(hit(342,281,108,29),[call('load track code')])])])
 proc('code keyboard',[iff(OR(cmp('equals',V('Input key'),'q'),cmp('equals',V('Input key'),'enter')),[iff(cmp('equals',V('Code open'),1),[call('close track code')],[iff(cmp('equals',V('Code open'),3),[iff(cmp('equals',V('Input key'),'q'),[call('close track code')],[call('load track code')])])])])])
 row_execute=[];row_disabled=[]
 for menu in menus:
  for r in menu['rows']:
   if r is None:continue
   current=AND(cmp('equals',V('Menu'),menu['id']),cmp('equals',V('Menu focus'),r['index']))
   row_execute += [iff(AND(current,NOT(r['disabled'])),[setv('Menu',0),setv('Drawing',0)]+([setv('Requested edit action',r['edit_action']),call('request edit action')] if r.get('edit_action') else r['action']))]
   row_disabled += [iff(current,[setv('Menu disabled',r['disabled'])])]
 proc('execute menu selection',row_execute)
 proc('menu selection disabled',[setv('Menu disabled',1)]+row_disabled)
 # All pointer clicks on an open menu are consumed, including clicks outside it.
 proc('menu pointer',[setv('Menu panel hit',0)]+[iff(cmp('equals',V('Menu'),m['id']),[iff(hit(m['x'],m['top'],m['w'],m['h']),[setv('Menu panel hit',1)]+[iff(hit(m['x']+4,r['y'],m['w']-8,26),[setv('Menu focus',r['index']),call('execute menu selection')]) for r in m['rows'] if r is not None])]) for m in menus]+[iff(cmp('equals',V('Menu panel hit'),0),[setv('Menu',0)])])
 header_actions=[]
 for c in controls:
  if c.get('menu'):
   action=[iff(cmp('equals',V('Menu before'),c['menu']),[setv('Menu',0)],[setv('Menu',c['menu']),setv('Menu focus',1),setv('Drawing',0),setv('Menu key up',0),setv('Menu key down',0),setv('Menu key enter',0),setv('Menu key escape',0)])]
  else:action=[setv('Menu',0)]+c['action']
  header_actions += [iff(hit(c['x'],c['y'],c['w'],c['h']),[setv('UI hit',1),iff(NOT(c.get('disabled',cmp('equals',0,1))),action)])]
 proc('handle toolbar',[setv('UI hit',0),setv('Menu before',V('Menu')),setv('Menu panel hit',0),iff(cmp('gt',V('Menu'),0),[setv('UI hit',1),call('menu pointer')]),iff(cmp('equals',V('Menu panel hit'),0),header_actions)])
 proc('menu hover',[iff(OR(NOT(cmp('equals',V('Mouse X'),V('Menu mouse X'))),NOT(cmp('equals',V('Mouse Y'),V('Menu mouse Y')))),sum(([iff(cmp('equals',V('Menu'),m['id']),[iff(hit(m['x']+4,r['y'],m['w']-8,26),[setv('Menu focus',r['index'])]) for r in m['rows'] if r is not None])] for m in menus),[])),setv('Menu mouse X',V('Mouse X')),setv('Menu mouse Y',V('Mouse Y'))])
 def next_row(direction):
  return sum(([iff(cmp('equals',V('Menu'),m['id']),[setv('Menu direction',direction),change('Menu focus',direction),iff(cmp('gt',V('Menu focus'),m['count']),[setv('Menu focus',1)]),iff(cmp('lt',V('Menu focus'),1),[setv('Menu focus',m['count'])]),call('menu selection disabled'),loop(m['count'],[iff(V('Menu disabled'),[change('Menu focus',direction),iff(cmp('gt',V('Menu focus'),m['count']),[setv('Menu focus',1)]),iff(cmp('lt',V('Menu focus'),1),[setv('Menu focus',m['count'])]),call('menu selection disabled')])])])] for m in menus),[])
 proc('menu keyboard',[iff(cmp('equals',V('Input key'),'down arrow'),next_row(1)),iff(cmp('equals',V('Input key'),'up arrow'),next_row(-1)),iff(cmp('equals',V('Input key'),'enter'),[call('execute menu selection')]),iff(cmp('equals',V('Input key'),'q'),[setv('Menu',0)])])
 return menus,controls

def render_controls(api):
 globals().update(api)
 out=[]
 for c in controls:
  if c['name'] in ['edit-mode','play-mode','play','retry','mode','full-play']:continue
  name=c['name'];out += [setv('button label',c['label']),setv('button state','normal')]
  if name=='edit-mode':out += [iff(cmp('equals',V('Editing'),1),[setv('button state','selected')])]
  if name=='play-mode':out += [iff(cmp('equals',V('Editing'),0),[setv('button state','selected')])]
  if name=='play':out += [iff(cmp('equals',V('Playing'),1),[setv('button label','Pause')])]
  if name=='track':out += [iff(cmp('equals',V('Dirty'),1),[setv('button label','Track*')])]
  if name=='tool':out += [iff(cmp('equals',V('Tool'),i),[setv('button label',label)]) for i,label in enumerate(['Pencil','Straight line','Eraser','Pan','Start flag','Goal flag'])]
  if name=='material':out += [iff(cmp('equals',V('Brush'),i),[setv('button label',label)]) for i,label in enumerate(['Normal','Grip','Ice','Scenery'])]
  out += [iff(hit(c['x'],c['y'],c['w'],c['h']),[setv('button state','hover')])]
  if name=='edit-mode':out += [iff(cmp('equals',V('Editing'),1),[setv('button state','selected')])]
  if name=='play-mode':out += [iff(cmp('equals',V('Editing'),0),[setv('button state','selected')])]
  if c.get('menu'):out += [iff(cmp('equals',V('Menu'),c['menu']),[setv('button state','selected')])]
  if name=='play':out += [iff(cmp('equals',V('Playing'),1),[setv('button state','selected')])]
  if c.get('disabled') is not None:out += [iff(c['disabled'],[setv('button state','disabled')])]
  out += stamp(cat('control ',name,' ',V('button label'),' ',V('button state')),c['x']+c['w']/2-240,180-c['y']-c['h']/2)
 # Mode, connector bus and transport share one SVG so their strokes meet exactly.
 out += [setv('Mode selected','edit'),setv('Assembly hover',0),setv('Transport running',0),setv('Transport disabled',0),iff(cmp('equals',V('Editing'),0),[setv('Mode selected','play')]),iff(hit(284,7,94,26),[setv('Assembly hover',1)]),iff(hit(378,7,94,26),[setv('Assembly hover',2)]),iff(cmp('equals',V('Playing'),1),[setv('Transport running',1)]),iff(OR(cmp('equals',V('Playing'),1),OR(cmp('equals',V('State'),4),AND(cmp('equals',V('State'),3),cmp('equals',V('Crash complete'),1)))),[setv('Transport disabled',1)])]
 for i in range(3):out += [iff(hit(284+i*188/3,43,188/3,26),[setv('Assembly hover',i+3)])]
 out += stamp(cat('play assembly ',V('Mode selected'),' ',V('Transport running'),' ',V('Transport disabled'),' ',V('Assembly hover')),138,142)
 out += [iff(cmp('equals',V('Editing'),0),stamp('control full-play Fullscreen normal',20,159))]

 return out

def render_popups(api):
 globals().update(api)
 out=[]
 for m in menus:
  draw=stamp('panel '+str(m['id']),m['x']+m['w']/2-240,180-m['top']-m['h']/2)
  for r in m['rows']:
   if r is None:continue
   draw += [setv('row label',r['label']),setv('row state','normal'),setv('row checked',0),iff(r['checked'],[setv('row checked',1)]),iff(cmp('equals',V('Menu focus'),r['index']),[setv('row state','hover')]),iff(r['disabled'],[setv('row state','disabled')])]
   if r.get('alt'):draw += [iff(cmp('equals',V('Goal enabled'),0),[setv('row label',r['alt'])])]
   draw += stamp(cat('row ',m['id'],' ',r['index'],' ',V('row label'),' ',V('row state'),' ',V('row checked'),' ',V('Mobile')),m['x']+m['w']/2-240,180-r['y']-13)
  out += [iff(cmp('equals',V('Menu'),m['id']),draw)]
 out += [iff(cmp('equals',V('Confirm open'),1),[setv('Confirmation hover',0),iff(hit(218,204,92,30),[setv('Confirmation hover',1)]),iff(hit(322,204,112,30),[setv('Confirmation hover',2)])]+stamp(cat('edit confirmation ',V('Confirmation hover'))))]
 return out

def build_assets(api):
 globals().update(api)
 for c in controls:
  if c['name'] in ['edit-mode','play-mode','play','retry','mode','full-play']:continue
  name=c['name'];w,h=c['w'],c['h'];labels=[c['label']]
  if name=='play':labels+=['Pause']
  if name=='track':labels+=['Track*']
  if name=='tool':labels+=['Straight line','Eraser','Pan','Start flag','Goal flag']
  if name=='material':labels+=['Grip','Ice','Scenery']
  flat=name in ['track','edit','view','help']
  for label in labels:
   for state in ['normal','hover']+(['selected'] if c.get('menu') else [])+(['disabled'] if c.get('disabled') is not None else []):
    fill={'normal':'#f1eee8' if flat else '#faf8f5','hover':'#e5e0d7','selected':'#ded9cf' if c.get('menu') else '#30332f','disabled':'#f1eee8'}[state]
    ink='#faf8f5' if state=='selected' and not c.get('menu') else '#918b82' if state=='disabled' else '#30332f'
    border='none' if flat else '#d6d1c8'
    cx=10 if c.get('menu') else w/2;anchor='start' if c.get('menu') else 'middle'
    content=f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="3" fill="{fill}" stroke="{border}"/><text x="{cx}" y="{h/2+3.7}" text-anchor="{anchor}" font-family="sans-serif" font-size="11" fill="{ink}">{html.escape(label)}</text>'
    if c.get('menu'):content+=f'<path d="M{w-15} 11l3 3 3-3" fill="none" stroke="{ink}" stroke-width="1.2"/>'
    costumes.append(costume('control '+name+' '+label+' '+state,svg(w,h,content),w/2,h/2))
 for m in menus:
  w,h=m['w'],m['h'];content=f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="3" fill="#faf8f5" stroke="#b6b1a9"/>'
  y=6
  for r in m['rows']:
   if r is None:content+=f'<path d="M8 {y+4}H{w-8}" stroke="#ded9cf"/>';y+=8
   else:y+=26
  costumes.append(costume('panel '+str(m['id']),svg(w,h,content),w/2,h/2))
  for r in m['rows']:
   if r is None:continue
   for label in [r['label']]+([r['alt']] if r.get('alt') else []):
    for state in ['normal','hover']+(['disabled'] if r['can_disable'] else []):
     for checked in ([0,1] if r['checkable'] else [0]):
      ink='#918b82' if state=='disabled' else '#30332f';content=f'<rect x="4" y="0" width="{w-8}" height="26" rx="2" fill="'+('#e5e0d7' if state=='hover' else '#faf8f5')+'"/>'
      if checked:content+=f'<path d="M10 13l3 3 5-6" fill="none" stroke="{ink}" stroke-width="1.4"/>'
      content+=f'<text x="25" y="17" font-family="sans-serif" font-size="11.5" fill="{ink}">{html.escape(label)}</text>'
      for mobile in [0,1]:
       shortcut=f'<text x="{w-13}" y="17" text-anchor="end" font-family="sans-serif" font-size="10" fill="{ink}">{html.escape(r["shortcut"])}</text>' if r['shortcut'] and not mobile else ''
       costumes.append(costume(f'row {m["id"]} {r["index"]} {label} {state} {checked} {mobile}',svg(w,26,content+shortcut),w/2,13))
 # A full-size assembly avoids trimming/cropping a separate line-only costume.
 for selected in ['edit','play']:
  for running in [0,1]:
   for disabled in [0,1]:
    if selected=='edit' and (running or disabled):continue
    if running and not disabled:continue
    for hover in range(6):
     content='<defs><clipPath id="mode-clip"><rect x=".5" y=".5" width="187" height="25" rx="3"/></clipPath><clipPath id="transport-clip"><rect x=".5" y=".5" width="187" height="25" rx="3"/></clipPath></defs><g clip-path="url(#mode-clip)"><path fill="#faf8f5" d="M0 0h188v26H0z"/>'
     hovered='edit' if hover==1 else 'play' if hover==2 else 'none'
     if hovered!='none' and hovered!=selected:content+=f'<rect x="{0 if hovered=="edit" else 94}" y="0" width="94" height="26" fill="#e5e0d7"/>'
     content+=f'<rect x="{0 if selected=="edit" else 94}" y="0" width="94" height="26" fill="#30332f"/></g><rect x=".5" y=".5" width="187" height="25" rx="3" fill="none" stroke="#8d8a81"/><path d="M94 .5v25" stroke="#8d8a81"/>'
     for i,label in enumerate(['Edit','Play']):
      ink='#faf8f5' if label.lower()==selected else '#30332f'
      content+=f'<text x="{47+94*i}" y="17" text-anchor="middle" font-family="sans-serif" font-size="12" fill="{ink}">{label}</text>'
     ink='#30332f' if selected=='play' else '#b6b1a9'
     content+=f'<path d="M141 25.5V31M{188/6} 31H{188*5/6}M{188/6} 31V36.5M94 31V36.5M{188*5/6} 31V36.5" fill="none" stroke="{ink}" stroke-width="1.5"/>'
     content+='<g transform="translate(0 36)"><g clip-path="url(#transport-clip)"><path fill="#faf8f5" d="M0 0h188v26H0z"/>'
     for i,label in enumerate(['Pause' if running else 'Run','Retry','Step']):
      inactive=i==2 and disabled
      fill='#f1eee8' if inactive else '#30332f' if i==0 and running else '#e5e0d7' if hover==i+3 else '#faf8f5'
      content+=f'<rect x="{i*188/3}" y="0" width="{188/3}" height="26" fill="{fill}"/>'
     content+='</g><rect x=".5" y=".5" width="187" height="25" rx="3" fill="none" stroke="#b6b1a9"/>'
     for divider in [188/3,376/3]:content+=f'<path d="M{divider} .5v25" stroke="#d6d1c8"/>'
     for i,label in enumerate(['Pause' if running else 'Run','Retry','Step']):
      ink='#918b82' if i==2 and disabled else '#faf8f5' if i==0 and running else '#30332f'
      content+=f'<text x="{(i+.5)*188/3}" y="17" text-anchor="middle" font-family="sans-serif" font-size="11" fill="{ink}">{label}</text>'
     content+='</g>'
     costumes.append(costume(f'play assembly {selected} {running} {disabled} {hover}',svg(188,62,content),94,31))

 # The backdrop and centered confirmation are drawn last and consume all input.
 for hover in range(3):
  cancel_fill='#e5e0d7' if hover==1 else '#faf8f5'
  accept_fill='#484b45' if hover==2 else '#30332f'
  content='<path fill="#30332f" fill-opacity=".28" d="M0 0h480v360H0z"/><rect x="24.5" y="122.5" width="431" height="131" rx="4" fill="#faf8f5" stroke="#b6b1a9"/>'
  for y,label in [(152,'This action will change the mode to "Edit".'),(176,'Are you sure you want to do this?')]:
   content+=f'<text x="44" y="{y}" font-family="sans-serif" font-size="13" fill="#30332f">{html.escape(label)}</text>'
  content+=f'<rect x="218.5" y="204.5" width="91" height="29" rx="3" fill="{cancel_fill}" stroke="#b6b1a9"/><text x="264" y="224" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#30332f">Cancel</text><rect x="322" y="204" width="112" height="30" rx="3" fill="{accept_fill}"/><text x="378" y="224" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#faf8f5">Switch to Edit</text>'
  costumes.append(costume('edit confirmation '+str(hover),svg(480,360,content),240,180))
