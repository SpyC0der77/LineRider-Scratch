"""Mobile-first input and conservative repair of single-segment erase gaps."""


def install(api):
    globals().update(api)
    V('Mobile'); variables['Mobile'][1] = 1
    for name in ['Erase source IDs', 'Erase times']:
        lists[name] = [name, []]
    proc('begin erase gesture', [clear('Erase source IDs'), clear('Erase times'),
        iff(cmp('equals', V('Mobile'), 1), [
            setv('Erase base', length('Undo LX')-length('LX')), setv('Erase source', 1),
            loop(length('LX'), [add('Erase source IDs', V('Erase source')), add('Erase times', 0), change('Erase source',1)])])])
    # The most recent Undo snapshot is the untouched geometry at gesture start.
    # Stable source IDs survive deletions and prevent shifted indices bridging
    # unrelated strokes. A bridge must touch both erased neighbors geometrically.
    proc('erase endpoints touch', [setv('Erase touch', 0)] + [
        iff(cmp('lt',
            (L('Undo LX',V('Erase A')) + L('Undo DX',V('Erase A'))*end_a - L('Undo LX',V('Erase B')) - L('Undo DX',V('Erase B'))*end_b)
            *(L('Undo LX',V('Erase A')) + L('Undo DX',V('Erase A'))*end_a - L('Undo LX',V('Erase B')) - L('Undo DX',V('Erase B'))*end_b)
            +(L('Undo LY',V('Erase A')) + L('Undo DY',V('Erase A'))*end_a - L('Undo LY',V('Erase B')) - L('Undo DY',V('Erase B'))*end_b)
            *(L('Undo LY',V('Erase A')) + L('Undo DY',V('Erase A'))*end_a - L('Undo LY',V('Erase B')) - L('Undo DY',V('Erase B'))*end_b),
            .0004), [setv('Erase touch',1)]) for end_a in [0,1] for end_b in [0,1]])
    proc('remove erase source', [setv('Erase index',itemindex('Erase source IDs',V('Erase candidate'))),
        iff(cmp('gt',V('Erase index'),0), [delete(f,V('Erase index')) for f in FIELDS]+[
            delete('Erase source IDs',V('Erase index')), replace('Erase times',V('Erase candidate'),Expr('sensing_timer')+.001),setv('Grid ready',0)])])
    proc('bridge erased neighbor', [
        iff(AND(AND(cmp('gt',V('Erase other'),0),cmp('lt',V('Erase other'),length('Erase times')+1)),
                AND(cmp('gt',L('Erase times',V('Erase other')),0),cmp('lt',Expr('sensing_timer')+.001-L('Erase times',V('Erase other')),.35))),[
            setv('Erase A',V('Erase base')+V('Erase candidate')),setv('Erase B',V('Erase base')+V('Erase hit source')),call('erase endpoints touch'),
            iff(cmp('equals',V('Erase touch'),1),[
                setv('Erase B',V('Erase base')+V('Erase other')),call('erase endpoints touch'),
                iff(cmp('equals',V('Erase touch'),1),[call('remove erase source')])])])])
    proc('delete eraser hit', [iff(cmp('equals',V('Mobile'),1),[
        setv('Erase hit source',L('Erase source IDs',V('erase id'))),setv('Erase candidate',V('Erase hit source')),call('remove erase source')
    ] + sum(([
        setv('Erase candidate',V('Erase hit source')+direction),setv('Erase other',V('Erase hit source')+direction*2),call('bridge erased neighbor')
    ] for direction in [-1,1]),[]), [delete(f,V('erase id')) for f in FIELDS]+[setv('Grid ready',0)])])
