"""Build a hidden documentation sprite from the reviewed, redacted transcript."""
import json
import math


def make_sprite(root, target, costume, svg):
    history = json.loads((root/'docs'/'prompt-history.json').read_text(encoding='utf-8'))
    prompts = history['prompts']
    assert [p['number'] for p in prompts] == list(range(1,len(prompts)+1))
    icon = costume('Prompt history',svg(48,48,
        '<path d="M11 5h19l7 7v31H11z" fill="#faf8f5" stroke="#59574f" stroke-width="2"/>'
        '<path d="M30 5v8h7M17 20h14M17 26h14M17 32h10" fill="none" stroke="#59574f" stroke-width="2"/>'),24,24)
    blocks = {
        'prompt-history-start': {'opcode':'event_whenflagclicked','next':'prompt-history-hide','parent':None,'inputs':{},'fields':{},'shadow':False,'topLevel':True,'x':20,'y':20},
        'prompt-history-hide': {'opcode':'looks_hide','next':None,'parent':'prompt-history-start','inputs':{},'fields':{},'shadow':False,'topLevel':False},
    }
    sprite = target('Prompt history',blocks=blocks,costumes=[icon],visible=False,x=0,y=0,size=100,direction=90,draggable=False,rotationStyle='all around')
    sprite['layerOrder']=2
    sprite['comments'] = {'prompt-history-index': {
        'blockId':None,'x':300,'y':20,'width':520,'height':125,'minimized':False,
        'text':f"Prompt history\n\n{len(prompts)} user-written prompts in chronological order, including the request for this sprite. Personal details and credentials are replaced with redaction markers. System/environment context and private attachment references are excluded."
    }}
    for index,prompt in enumerate(prompts):
        text=f"Prompt {prompt['number']:02d}\n\n{prompt['text']}"
        lines=sum(max(1,math.ceil(len(line)/75)) for line in text.splitlines())
        sprite['comments'][f"prompt-{prompt['number']:02d}"]={
            'blockId':None,'x':20+(index%2)*580,'y':180+(index//2)*360,
            'width':520,'height':min(330,max(110,35+18*lines)),'minimized':False,'text':text}
    return sprite
