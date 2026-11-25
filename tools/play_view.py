"""An uninterrupted native Scratch stage view, with touch-friendly controls."""


def install(api):
    globals().update(api)
    V('Full play');variables['Full play'][1]=0
    proc('toggle full play', [iff(cmp('equals',V('Editing'),0),[
        setv('Full play',1-V('Full play')),setv('Menu',0),setv('Help',0),setv('Drawing',0)])])


def define_input(api):
    globals().update(api)
    proc('full play pointer',[
        iff(hit(440,8,32,32),[call('toggle full play')]),
        iff(AND(cmp('equals',V('Playing'),0),AND(cmp('lt',V('State'),3),hit(204,148,72,64))),[call('play or pause')]),
        iff(cmp('gt',V('State'),2),[
            iff(hit(152,273,82,32),[call('retry')]),iff(hit(246,273,82,32),[call('select edit mode')])])])


def render(api):
    globals().update(api)
    return stamp('exit full play',216,156)+[
        iff(AND(cmp('equals',V('Playing'),0),cmp('lt',V('State'),3)),stamp('full play resume',0,0)),
        iff(cmp('gt',V('State'),2),
            stamp('full play result',0,-119)+text(cat('Frame ',V('Frame'),'   ',mathop('round',V('Frame')/30*100)/100,'s'),-64,-144))]


def build_assets(api):
    globals().update(api)
    for name,inset in [('full-play',False),('exit full play',True)]:
        content='<rect x=".5" y=".5" width="31" height="31" rx="3" fill="#faf8f5" stroke="#b6b1a9"/>'
        path='M8 13h5V8M19 8v5h5M8 19h5v5M19 24v-5h5' if inset else 'M8 13V8h5M19 8h5v5M8 19v5h5M19 24h5v-5'
        content+=f'<path d="{path}" fill="none" stroke="#30332f" stroke-width="1.5"/>'
        if inset:
            costumes.append(costume(name,svg(32,32,content),16,16))
        else:
            # The Play timeline bar is 24 px high, so this icon is scaled to fit it.
            small='<rect x=".5" y=".5" width="23" height="23" rx="3" fill="#faf8f5" stroke="#b6b1a9"/>'+f'<path d="{path}" fill="none" stroke="#30332f" stroke-width="2" transform="scale(.75)"/>'
            costumes.append(costume('control full-play Fullscreen normal',svg(24,24,small),12,12))
    costumes.append(costume('full play resume',svg(72,64,'<rect x=".5" y=".5" width="71" height="63" rx="4" fill="#faf8f5" stroke="#b6b1a9"/><path d="M28 18l23 14-23 14z" fill="#30332f"/>'),36,32))
    content='<rect x=".5" y=".5" width="191" height="69" rx="4" fill="#faf8f5" stroke="#b6b1a9"/>'
    for x,label in [(8,'Retry'),(102,'Edit')]:
        content+=f'<rect x="{x}" y="9" width="82" height="32" rx="3" fill="#faf8f5" stroke="#b6b1a9"/><text x="{x+41}" y="30" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#30332f">{label}</text>'
    costumes.append(costume('full play result',svg(192,70,content),96,35))
