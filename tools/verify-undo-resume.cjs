// Checks that Undo and Redo resume the timeline and match a full recalculation.
// Usage: node tools/verify-undo-resume.cjs [seed=1] [cases=20]
const fs = require('node:fs');
const path = require('node:path');
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
const CACHE = ['Timeline X', 'Timeline Y', 'Timeline PX', 'Timeline PY',
    'Timeline Ride result', 'Timeline Mounted'];
const POINT_LISTS = new Set(CACHE.slice(0, 6));
const MATERIALS = [0, 0, 0, 1, 2, 4, 5, 3];
const TIMEOUT_MS = 120000;

const args = process.argv.slice(2);
const seed = Number(args[0]) || 1;
const cases = Number(args[1]) || 20;

function mulberry32(a) {
    return () => {
        a |= 0; a = a + 0x6D2B79F5 | 0;
        let t = Math.imul(a ^ a >>> 15, 1 | a);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
}
const rnd = mulberry32(seed);
const between = (lo, hi) => lo + (hi - lo) * rnd();
const pick = xs => xs[Math.floor(rnd() * xs.length)];

const stage = vm => vm.runtime.getTargetForStage();
const getVar = (vm, name) => stage(vm).lookupVariableByNameAndType(name, '').value;
const setVar = (vm, name, v) => { stage(vm).lookupVariableByNameAndType(name, '').value = v; };
const getList = (vm, name) => stage(vm).lookupVariableByNameAndType(name, 'list').value;
const num = (vm, name) => Number(getVar(vm, name));
const isReady = vm => num(vm, 'Timeline ready') === 1 && num(vm, 'Timeline current pose') === 1;

// Steps until the timeline has no pending restart, is ready and the grid is built.
function settle(vm, label) {
    const start = Date.now();
    do {
        if (Date.now() - start > TIMEOUT_MS) throw new Error('Timed out: ' + label);
        vm.runtime._step();
    } while (!(num(vm, 'Timeline restart') === 0 && isReady(vm) && num(vm, 'Grid ready') === 1));
}

// Runs an exported Track editor request (begin change, undo, redo) to completion.
function request(vm, name) {
    const threads = vm.runtime.startHats('event_whenbroadcastreceived', {BROADCAST_OPTION: name});
    if (!threads || !threads.length) throw new Error('no hat for ' + name);
    const start = Date.now();
    while (threads.some(t => vm.runtime.threads.includes(t))) {
        if (Date.now() - start > TIMEOUT_MS) throw new Error('Timed out: ' + name);
        vm.runtime._step();
    }
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

// Mirrors 'mark_line'. The edit itself mirrors the segment hook and delete hook.
function markLine(vm, index1, delta) {
    const at = k => Number(getList(vm, k)[index1 - 1]);
    const bounds = [['X0', 'MinX', Math.min], ['X1', 'MaxX', Math.max], ['Y0', 'MinY', Math.min], ['Y1', 'MaxY', Math.max]];
    if (num(vm, 'Timeline dirty') === 0) {
        for (const [b, f] of bounds) setVar(vm, 'Timeline dirty ' + b, at(f));
        setVar(vm, 'Timeline dirty', 1);
    } else {
        for (const [b, f, pickFn] of bounds) setVar(vm, 'Timeline dirty ' + b, pickFn(num(vm, 'Timeline dirty ' + b), at(f)));
    }
    setVar(vm, 'Timeline expected lines', num(vm, 'Timeline expected lines') + delta);
}

function addSegment(vm, x1, y1, x2, y2, material) {
    if (x2 < x1) [x1, y1, x2, y2] = [x2, y2, x1, y1];
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy);
    const line = {
        LX: x1, LY: y1, DX: dx, DY: dy, NX: -dy / len, NY: dx / len, InvSq: 1 / (len * len), Material: material,
        MinX: x1 - 10, MaxX: x1 + dx + 10,
        MinY: y1 + dy * .5 - Math.abs(dy) * .5 - 10, MaxY: y1 + dy * .5 + Math.abs(dy) * .5 + 10,
    };
    for (const k of TRACK) getList(vm, k).push(line[k]);
    markLine(vm, getList(vm, 'LX').length, 1);
    setVar(vm, 'Grid ready', 0);
}

function deleteLine(vm, i0) {
    markLine(vm, i0 + 1, -1);
    for (const k of TRACK) getList(vm, k).splice(i0, 1);
    setVar(vm, 'Grid ready', 0);
}

// Returns the edit's description and the frame it was placed near (null when none).
function applyEdit(vm, kind, end) {
    const P = getList(vm, 'Initial X').length;
    const hip = f => ({x: Number(getList(vm, 'Timeline X')[f * P + 4]), y: Number(getList(vm, 'Timeline Y')[f * P + 4])});
    if (kind === 'near') {
        const frame = Math.floor(end / 2) + Math.floor(rnd() * (end - Math.floor(end / 2)));
        const h = hip(frame);
        const n = 1 + Math.floor(rnd() * 4);
        for (let k = 0; k < n; k++) {
            const x1 = h.x + between(-30, 30), y1 = h.y - between(0, 40);
            const len = between(5, 60), a = between(0, 2 * Math.PI);
            addSegment(vm, x1, y1, x1 + len * Math.cos(a), y1 + len * Math.sin(a), pick(MATERIALS));
        }
        return {desc: `near ${n} seg`, kind, frame};
    }
    const n = 1 + Math.floor(rnd() * 3);
    for (let k = 0; k < n; k++) deleteLine(vm, Math.floor(rnd() * getList(vm, 'LX').length));
    return {desc: `delete ${n}`, kind, frame: null};
}

function trackCopy(vm) {
    return TRACK.map(k => getList(vm, k).map(Number));
}

function snapshot(vm) {
    const out = {end: num(vm, 'Timeline end')};
    for (const k of CACHE) out[k] = getList(vm, k).slice();
    return out;
}

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

// Recomputes the whole ride from scratch and returns the snapshot.
function fullRecalculation(vm) {
    setVar(vm, 'Timeline dirty all', 1);
    setVar(vm, 'Timeline restart', 1);
    settle(vm, 'full recalculation');
    return snapshot(vm);
}

const sameTrack = (a, b) => JSON.stringify(a) === JSON.stringify(b);

(async () => {
    console.log(`seed=${seed} cases=${cases}`);
    let passed = 0, failed = 0;
    const undoResumes = [], redoResumes = [];
    for (let c = 1; c <= cases; c++) {
        const vm = await loadVM();
        if (num(vm, 'Editing') !== 1) throw new Error('expected Editing=1 after green flag');
        const end = num(vm, 'Timeline end');
        const P = getList(vm, 'Initial X').length;
        const before = trackCopy(vm);

        // Save an Undo snapshot of the untouched track, then make the edit.
        request(vm, 'Track editor / begin change');
        const edit = applyEdit(vm, pick(['near', 'near', 'delete']), end);
        settle(vm, 'edit');
        const afterEdit = trackCopy(vm);

        // Undo must restore the pre-edit track and resume the ride.
        request(vm, 'Track editor / undo');
        settle(vm, 'undo');
        const undoResume = num(vm, 'Timeline resume');
        const undoTrackOk = sameTrack(trackCopy(vm), before);
        const undoInc = snapshot(vm);
        const undoFull = fullRecalculation(vm);
        const undoDiff = firstDiff(undoInc, undoFull, P);

        // Redo must restore the edited track. The cache is now a full, valid ride.
        request(vm, 'Track editor / redo');
        settle(vm, 'redo');
        const redoResume = num(vm, 'Timeline resume');
        const redoTrackOk = sameTrack(trackCopy(vm), afterEdit);
        const redoInc = snapshot(vm);
        const redoFull = fullRecalculation(vm);
        const redoDiff = firstDiff(redoInc, redoFull, P);
        vm.stopAll();

        const label = `${edit.desc}${edit.frame !== null ? ` @f${edit.frame}` : ''}`;
        const problems = [];
        if (!undoTrackOk) problems.push('undo track differs from pre-edit track');
        if (!redoTrackOk) problems.push('redo track differs from edited track');
        if (undoDiff) problems.push('undo: ' + undoDiff);
        if (redoDiff) problems.push('redo: ' + redoDiff);
        if (edit.kind === 'near' && undoResume <= 0) problems.push(`undo resume ${undoResume} not > 0 for late edit`);
        if (edit.kind === 'near' && redoResume <= 0) problems.push(`redo resume ${redoResume} not > 0 for late edit`);
        undoResumes.push({kind: edit.kind, frame: edit.frame, resume: undoResume, end});
        redoResumes.push({kind: edit.kind, frame: edit.frame, resume: redoResume, end});
        if (problems.length) {
            failed++;
            console.log(`FAIL case ${c}: edit [${label}] undo resume=${undoResume} redo resume=${redoResume}\n  ${problems.join('\n  ')}`);
        } else {
            passed++;
            console.log(`pass case ${c}: edit [${label}] undo resume=${undoResume} redo resume=${redoResume} end=${end}`);
        }
    }

    const summarize = (name, rows) => {
        const near = rows.filter(r => r.kind === 'near');
        const del = rows.filter(r => r.kind === 'delete');
        const fmt = xs => xs.length ? `min=${Math.min(...xs)} median=${[...xs].sort((a, b) => a - b)[xs.length >> 1]} max=${Math.max(...xs)}` : 'none';
        console.log(`  ${name} near (late edits, frame in second half): n=${near.length} resume ${fmt(near.map(r => r.resume))}`);
        console.log(`  ${name} near frame->resume: ` + near.map(r => `f${r.frame}->${r.resume}`).join('  '));
        console.log(`  ${name} delete: n=${del.length} resume ${fmt(del.map(r => r.resume))}`);
    };
    console.log('\nResume frames (frames before resume are reused):');
    summarize('undo', undoResumes);
    summarize('redo', redoResumes);
    console.log(`\nsummary: ${passed} passed, ${failed} failed of ${cases}`);
    process.exitCode = failed ? 1 : 0;
})().catch(e => { console.error(e); process.exit(1); });
