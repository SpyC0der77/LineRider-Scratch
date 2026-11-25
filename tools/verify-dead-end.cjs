// Checks dead-end detection in a headless VM: bowls must end as result 6, the setting must
// resume correctly, and every resumed timeline must equal a forced full recalculation.
// Usage: node tools/verify-dead-end.cjs
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createRequire} = require('node:module');

const NM = 'C:/Users/Carter/code/Scratch/goboscript/tools/scratch-test/node_modules';
const req = createRequire(path.join(NM, 'package.json'));
const VM = req('scratch-vm');
const {ScratchStorage} = req('scratch-storage');
req('minilog').disable();
const warn = console.warn;
console.warn = (...a) => { if (!String(a[0]).startsWith('Translation for')) warn(...a); };

const FILE = path.join(__dirname, '..', 'dist', 'Line Rider.sb3');
const TRACK = ['LX', 'LY', 'DX', 'DY', 'NX', 'NY', 'InvSq', 'Material', 'MinX', 'MaxX', 'MinY', 'MaxY'];
const CACHE = ['Timeline X', 'Timeline Y', 'Timeline PX', 'Timeline PY', 'Timeline Ride result', 'Timeline Mounted',
    'Timeline Boost', 'Timeline Cell X0', 'Timeline Cell X1', 'Timeline Cell Y0', 'Timeline Cell Y1'];
const POINT_LISTS = new Set(CACHE.slice(0, 4));
const SETTING = 'Setting stop dead ends';
const DEAD_RESULT = 6;
const FRAMES = 450;
const SLACK = 2;
const TIMEOUT_MS = 900000;

const stage = vm => vm.runtime.getTargetForStage();
const getVar = (vm, name) => stage(vm).lookupVariableByNameAndType(name, '').value;
const setVar = (vm, name, v) => { stage(vm).lookupVariableByNameAndType(name, '').value = v; };
const getList = (vm, name) => stage(vm).lookupVariableByNameAndType(name, 'list').value;
const num = (vm, name) => Number(getVar(vm, name));
const isReady = vm => num(vm, 'Timeline ready') === 1 && num(vm, 'Timeline current pose') === 1;

// Steps until the restart is consumed and the timeline is ready. Returns elapsed milliseconds.
function settle(vm, label) {
    const start = Date.now();
    do {
        if (Date.now() - start > TIMEOUT_MS) throw new Error('Timed out: ' + label);
        vm.runtime._step();
    } while (!(num(vm, 'Timeline restart') === 0 && isReady(vm) && num(vm, 'Grid ready') === 1));
    return Date.now() - start;
}

async function loadVM() {
    const vm = new VM();
    vm.attachStorage(new ScratchStorage());
    await vm.loadProject(fs.readFileSync(FILE));
    vm.runtime.currentStepTime = 1000 / 30;
    vm.greenFlag();
    settle(vm, 'initial timeline');
    return vm;
}

// Mirrors the segment hook: swap so dx >= 0, then fill every aligned track list.
function lineFields(x1, y1, x2, y2, material) {
    if (x2 < x1) [x1, y1, x2, y2] = [x2, y2, x1, y1];
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy);
    return {
        LX: x1, LY: y1, DX: dx, DY: dy, NX: -dy / len, NY: dx / len, InvSq: 1 / (len * len), Material: material,
        MinX: x1 - 10, MaxX: x1 + dx + 10,
        MinY: y1 + dy * .5 - Math.abs(dy) * .5 - 10, MaxY: y1 + dy * .5 + Math.abs(dy) * .5 + 10,
    };
}

// Appends one line the way the editor does: marks its padded box dirty, then grows the lists.
function addLineMarked(vm, x1, y1, x2, y2, material) {
    const line = lineFields(x1, y1, x2, y2, material);
    for (const k of TRACK) getList(vm, k).push(line[k]);
    const idx = getList(vm, 'LX').length;
    const bounds = [['X0', 'MinX', Math.min], ['X1', 'MaxX', Math.max], ['Y0', 'MinY', Math.min], ['Y1', 'MaxY', Math.max]];
    if (num(vm, 'Timeline dirty') === 0) {
        for (const [b, f] of bounds) setVar(vm, 'Timeline dirty ' + b, getList(vm, f)[idx - 1]);
        setVar(vm, 'Timeline dirty', 1);
    } else {
        for (const [b, f, pick] of bounds) setVar(vm, 'Timeline dirty ' + b, pick(num(vm, 'Timeline dirty ' + b), getList(vm, f)[idx - 1]));
    }
    setVar(vm, 'Timeline expected lines', num(vm, 'Timeline expected lines') + 1);
    setVar(vm, 'Grid ready', 0);
}

// Replaces the whole track and forces a full recalculation on the next step.
function setTrack(vm, segments, goal) {
    for (const k of TRACK) getList(vm, k).length = 0;
    for (const [x1, y1, x2, y2, material] of segments) {
        const line = lineFields(x1, y1, x2, y2, material);
        for (const k of TRACK) getList(vm, k).push(line[k]);
    }
    setVar(vm, 'Goal enabled', goal ? 1 : 0);
    setVar(vm, 'Grid ready', 0);
    setVar(vm, 'Timeline dirty all', 1);
    setVar(vm, 'Timeline restart', 1);
}

// Bowl under the spawn in 12-unit segments. Y grows downward in this editor, so the
// bottom is 60 units below the spawn and the walls rise above it.
// y = spawnY + 60 - (x - spawnX - 60)^2 / 400.
function bowl(vm, material = () => 0) {
    const sx = num(vm, 'Spawn X'), sy = num(vm, 'Spawn Y');
    const pts = [];
    for (let x = sx - 200; x <= sx + 320; x += 12) pts.push([x, sy + 60 - (x - sx - 60) ** 2 / 400]);
    const segs = [];
    for (let i = 0; i + 1 < pts.length; i++) {
        const [x1, y1] = pts[i], [x2, y2] = pts[i + 1];
        segs.push([x1, y1, x2, y2, material((x1 + x2) / 2)]);
    }
    return {segs, sx, sy};
}

function snapshot(vm) {
    const out = {end: num(vm, 'Timeline end'), resume: num(vm, 'Timeline resume')};
    for (const k of CACHE) out[k] = getList(vm, k).slice();
    return out;
}

// Returns null when equal, otherwise a description of the first difference.
function firstDiff(inc, full, P) {
    if (inc.end !== full.end) return `Timeline end ${inc.end} vs ${full.end}`;
    for (const k of CACHE) {
        const a = inc[k], b = full[k];
        const n = Math.max(a.length, b.length);
        for (let i = 0; i < n; i++) {
            if (String(a[i]) !== String(b[i])) {
                const frame = POINT_LISTS.has(k) ? Math.floor(i / P) : i;
                return `${k} index ${i} (frame ${frame}): incremental=${a[i]} full=${b[i]} lengths ${a.length}/${b.length}`;
            }
        }
    }
    return null;
}

// Independent evaluation of the rule over the cached hips and boost flags. Returns the
// first frame that would end as a dead end, or -1.
function expectedDeadEnd(vm, end) {
    const P = getList(vm, 'Initial X').length;
    const X = getList(vm, 'Timeline X'), Y = getList(vm, 'Timeline Y');
    const boost = getList(vm, 'Timeline Boost'), result = getList(vm, 'Timeline Ride result');
    const hip = f => [Number(X[f * P + 4]), Number(Y[f * P + 4])];
    let [hx, hy] = hip(0);
    let box = {x0: hx, x1: hx, y0: hy, y1: hy}, stuck = 0;
    for (let f = 1; f <= end; f++) {
        [hx, hy] = hip(f);
        const out = hx < box.x0 - SLACK || hx > box.x1 + SLACK || hy < box.y0 - SLACK || hy > box.y1 + SLACK;
        if (out) stuck = f;
        box = {x0: Math.min(box.x0, hx), x1: Math.max(box.x1, hx), y0: Math.min(box.y0, hy), y1: Math.max(box.y1, hy)};
        if (Number(boost[f]) === 1) stuck = f;
        // Cached frames before the end are results 1; the end frame may already be 6.
        const r = Number(result[f]);
        if ((r === 1 || r === DEAD_RESULT) && f - stuck >= FRAMES) return f;
    }
    return -1;
}

// Compares the current timeline with a forced full recalculation. Afterwards the
// timeline holds the full result, which is what the next step of the test uses.
function checkAgainstFull(vm, label) {
    const P = getList(vm, 'Initial X').length;
    const inc = snapshot(vm);
    setVar(vm, 'Timeline dirty all', 1);
    setVar(vm, 'Timeline restart', 1);
    const ms = settle(vm, 'full ' + label);
    const full = snapshot(vm);
    const diff = firstDiff(inc, full, P);
    assert.equal(diff, null, `${label}: incremental differs from full recalculation: ${diff}`);
    return {inc, ms};
}

// Per-frame lists are 1-based in Scratch: frame f is item f + 1, JS index f.
function endResult(vm) {
    const end = num(vm, 'Timeline end');
    return Number(getList(vm, 'Timeline Ride result')[end]);
}

function lastBoost(vm, end) {
    const b = getList(vm, 'Timeline Boost');
    for (let f = end; f >= 0; f--) if (Number(b[f]) === 1) return f;
    return -1;
}

// Cached crash/finish flags: the rider must stay mounted for every frame up to the end.
function mountedThrough(vm, end) {
    const m = getList(vm, 'Timeline Mounted');
    for (let f = 0; f <= end; f++) if (Number(m[f]) !== 1) return f;
    return -1;
}

function deepestHip(vm, frames) {
    const P = getList(vm, 'Initial X').length;
    const Y = getList(vm, 'Timeline Y');
    let deep = -Infinity;
    for (let f = 0; f <= frames; f++) deep = Math.max(deep, Number(Y[f * P + 4]));
    return deep;
}

function report(label, vm, ms) {
    const end = num(vm, 'Timeline end');
    const r = endResult(vm);
    console.log(`${label}: end=${end} result=${r} time=${ms} ms (${(ms / Math.max(1, end)).toFixed(2)} ms/frame)`);
    return {end, r, ms};
}

(async () => {
    const results = {};

    // 1. Normal bowl: dead end after the rider settles.
    const vmA = await loadVM();
    const sA = bowl(vmA);
    setTrack(vmA, sA.segs, false);
    const msA = settle(vmA, 'normal bowl');
    const a = report('normal bowl (setting on)', vmA, msA);
    const expectedA = expectedDeadEnd(vmA, a.end);
    assert.equal(a.r, DEAD_RESULT, 'normal bowl should end as dead end');
    assert.equal(a.end, expectedA, 'normal bowl end should match the independent evaluation');
    assert.ok(a.end <= 900, `normal bowl should end within 900 frames, got ${a.end}`);
    assert.equal(mountedThrough(vmA, a.end), -1, 'rider should stay mounted through the bowl');
    const lands = deepestHip(vmA, 100);
    assert.ok(lands > sA.sy + 30, `rider should drop into the bowl (deepest hip ${lands} vs spawn ${sA.sy})`);
    console.log(`  deepest hip in first 100 frames: ${lands.toFixed(1)} (spawn ${sA.sy}); last acceleration frame: ${lastBoost(vmA, a.end)}`);
    results.normal = {...a, expected: expectedA};
    const fullA = checkAgainstFull(vmA, 'normal bowl');
    console.log(`  full recalculation equal; full time ${fullA.ms} ms`);

    // 2. Storage-limit comparison: same bowl with detection off.
    setVar(vmA, SETTING, 0);
    setVar(vmA, 'Timeline restart', 1);
    const msOff = settle(vmA, 'bowl with detection off');
    const offResume = num(vmA, 'Timeline resume');
    const off = report('normal bowl (setting off, storage limit)', vmA, msOff);
    assert.equal(off.r, 5, 'with detection off the bowl should reach the storage limit');
    results.storage = off;
    console.log(`  resume after turning setting off: ${offResume} (dead-end frame was ${a.end})`);
    assert.equal(offResume, a.end, 'turning the setting off should resume from the dead-end frame');
    checkAgainstFull(vmA, 'bowl with detection off');
    console.log(`  full recalculation equal with setting off`);

    // 3. Setting back on: ends at the same frame as the first run.
    setVar(vmA, SETTING, 1);
    setVar(vmA, 'Timeline restart', 1);
    const msOn = settle(vmA, 'bowl with detection back on');
    const on = report('normal bowl (setting back on)', vmA, msOn);
    assert.equal(on.r, DEAD_RESULT);
    assert.equal(on.end, a.end, 'turning detection back on should end at the same frame');
    checkAgainstFull(vmA, 'bowl with detection back on');
    console.log('  full recalculation equal with setting back on');

    // 4. Edits at a late frame: one inside the bowl (its grid cells are queried from frame 1,
    // so it resumes early), and one outside the bowl (resumes late). Both must match a full run.
    const late = Math.floor(on.end * 0.8);
    const P = getList(vmA, 'Initial X').length;
    const hx = Number(getList(vmA, 'Timeline X')[late * P + 4]);
    const hy = Number(getList(vmA, 'Timeline Y')[late * P + 4]);
    addLineMarked(vmA, hx - 14, hy - 12, hx + 14, hy - 12, 0);
    const msEdit = settle(vmA, 'late edit inside bowl');
    const edit = report(`late edit inside bowl near frame ${late} (setting on)`, vmA, msEdit);
    console.log(`  resume after late edit inside bowl: ${num(vmA, 'Timeline resume')}`);
    checkAgainstFull(vmA, 'late edit inside bowl');
    console.log('  full recalculation equal after late edit inside bowl');
    results.lateEdit = {...edit, late, resume: num(vmA, 'Timeline resume')};
    vmA.stopAll();

    const vmL = await loadVM();
    const sL = bowl(vmL);
    setTrack(vmL, sL.segs, false);
    settle(vmL, 'bowl for outside edit');
    const endL = num(vmL, 'Timeline end');
    const farX = sL.sx + 400;
    addLineMarked(vmL, farX, sL.sy + 40, farX + 40, sL.sy + 40, 0);
    const msFar = settle(vmL, 'outside edit');
    const far = report('edit outside the bowl (setting on)', vmL, msFar);
    console.log(`  resume after outside edit: ${num(vmL, 'Timeline resume')} (dead end was at ${endL})`);
    assert.equal(far.r, DEAD_RESULT, 'outside edit should keep the bowl a dead end');
    checkAgainstFull(vmL, 'outside edit');
    console.log('  full recalculation equal after outside edit');
    results.outsideEdit = {...far, resume: num(vmL, 'Timeline resume')};
    vmL.stopAll();

    // 5. Ice bowl: low friction still ends as a dead end.
    const vmB = await loadVM();
    const sB = bowl(vmB, () => 2);
    setTrack(vmB, sB.segs, false);
    const msB = settle(vmB, 'ice bowl');
    const b = report('ice bowl', vmB, msB);
    assert.equal(b.r, DEAD_RESULT, 'ice bowl should end as dead end');
    assert.equal(b.end, expectedDeadEnd(vmB, b.end), 'ice bowl end should match the independent evaluation');
    checkAgainstFull(vmB, 'ice bowl');
    results.ice = b;
    vmB.stopAll();

    // 6. Bowl with an acceleration strip at its bottom: the boost keeps energy coming.
    const vmC = await loadVM();
    const sxC = num(vmC, 'Spawn X');
    const sC = bowl(vmC, mid => (mid > sxC + 40 && mid < sxC + 80 ? 4 : 0));
    setTrack(vmC, sC.segs, false);
    const msC = settle(vmC, 'acceleration bowl');
    const c = report('bowl with acceleration strip (setting on)', vmC, msC);
    const boost = lastBoost(vmC, c.end);
    console.log(`  last acceleration contact at frame ${boost}; ride result ${c.r}; frames after last boost ${c.end - boost}`);
    assert.equal(expectedDeadEnd(vmC, c.end), c.r === DEAD_RESULT ? c.end : -1, 'acceleration bowl must end exactly where the rule says');
    checkAgainstFull(vmC, 'acceleration bowl');
    results.accel = {...c, lastBoost: boost};
    vmC.stopAll();

    console.log('\nsummary', JSON.stringify(results, null, 1));
    console.log('PASS dead-end checks');
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
