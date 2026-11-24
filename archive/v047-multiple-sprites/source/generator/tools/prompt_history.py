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
        'blockId':None,'x':20,'y':135,'width':520,'height':145,'minimized':False,
        'text':f"Prompt history\n\n{len(prompts)} user prompts in order. Public usernames are kept; passwords, private contact details and local paths are redacted. Automatic context is omitted."
    }}
    y=320
    for prompt in prompts:
        text=f"Prompt {prompt['number']:02d}\n\n{prompt['text']}"
        lines=sum(max(1,math.ceil(len(line)/55)) for line in text.splitlines())
        height=min(430,max(120,70+18*lines))
        sprite['comments'][f"prompt-{prompt['number']:02d}"]={
            'blockId':None,'x':20,'y':y,
            'width':520,'height':height,'minimized':False,'text':text}
        y+=height+45
    return sprite
