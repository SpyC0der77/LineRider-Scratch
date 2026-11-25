// Checks that the incremental timeline resume matches a full recalculation.
// Usage: node tools/verify-timeline-resume.cjs [seed=1] [cases=40]
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
const CACHE = ['Timeline X', 'Timeline Y', 'Timeline PX', 'Timeline PY', 'Timeline VX', 'Timeline VY',
    'Timeline Ride result', 'Timeline Mounted'];
const POINT_LISTS = new Set(CACHE.slice(0, 6));
const KINDS = ['near', 'delete', 'far', 'goal', 'detach', 'lowest'];
const MATERIALS = [0, 0, 0, 1, 2, 4, 5, 3];
const TIMEOUT_MS = 120000;

const args = process.argv.slice(2);
const seed = Number(args[0]) || 1;
const cases = Number(args[1]) || 40;

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

// Steps at least once, then until the restart is consumed and the timeline is ready.
function settle(vm, label) {
    const start = Date.now();
    do {
        if (Date.now() - start > TIMEOUT_MS) throw new Error('Timed out: ' + label);
        vm.runtime._step();
    } while (!(num(vm, 'Timeline restart') === 0 && isReady(vm) && num(vm, 'Grid ready') === 1));
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

// Mirrors 'mark_line': index is 1-based; deltas track 'Timeline expected lines'.
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

// Mirrors the segment hook: swap so dx >= 0, append at the end, then mark the new index.
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

// Marks before removal, as the delete hook does.
function deleteLine(vm, i0) {
    markLine(vm, i0 + 1, -1);
    for (const k of TRACK) getList(vm, k).splice(i0, 1);
    setVar(vm, 'Grid ready', 0);
}

// Applies one edit and returns its description and the cached frame it targets (null if none).
function applyEdit(vm, kind, end) {
    const P = getList(vm, 'Initial X').length;
    const hip = f => ({x: Number(getList(vm, 'Timeline X')[f * P + 4]), y: Number(getList(vm, 'Timeline Y')[f * P + 4])});
    const frame = 1 + Math.floor(rnd() * end);
    switch (kind) {
        case 'near': {
            const h = hip(frame);
            const n = 1 + Math.floor(rnd() * 5);
            for (let k = 0; k < n; k++) {
                const x1 = h.x + between(-30, 30), y1 = h.y - between(0, 40);
                const len = between(5, 60), a = between(0, 2 * Math.PI);
                addSegment(vm, x1, y1, x1 + len * Math.cos(a), y1 + len * Math.sin(a), pick(MATERIALS));
            }
            return {desc: `near ${n} seg`, frame};
        }
        case 'delete': {
            const n = 1 + Math.floor(rnd() * 3);
            for (let k = 0; k < n; k++) deleteLine(vm, Math.floor(rnd() * getList(vm, 'LX').length));
            return {desc: `delete ${n}`, frame: null};
        }
        case 'far': {
            const xs = [], ys = [];
            for (let i = 0; i < getList(vm, 'Timeline X').length; i += P) {
                xs.push(Number(getList(vm, 'Timeline X')[i]));
                ys.push(Number(getList(vm, 'Timeline Y')[i]));
            }
            const maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
            const n = 1 + Math.floor(rnd() * 3);
            for (let k = 0; k < n; k++) {
                const x1 = maxX + between(1000, 2000), y1 = between(minY, maxY);
                addSegment(vm, x1, y1, x1 + between(20, 60), y1 + between(-20, 20), pick(MATERIALS));
            }
            return {desc: `far ${n} seg`, frame: null};
        }
        case 'goal': {
            const h = hip(frame);
            setVar(vm, 'Goal X', h.x + between(-200, 200));
            setVar(vm, 'Goal Y', h.y + between(-100, 100));
            setVar(vm, 'Timeline restart', 1);
            return {desc: 'goal move', frame: null};
        }
        case 'detach': {
            setVar(vm, 'Timeline detach frame', frame);
            setVar(vm, 'Timeline restart', 1);
            return {desc: 'detach', frame};
        }
        case 'lowest': {
            // The build sets Lowest track to max(MaxY), so this line lies above the current value.
            const y = num(vm, 'Lowest track') + 50, x = hip(frame).x + between(-100, 100);
            addSegment(vm, x, y, x + between(20, 80), y, pick(MATERIALS));
            return {desc: 'lowest line', frame: null};
        }
    }
    throw new Error('unknown kind ' + kind);
}

function snapshot(vm) {
    const out = {end: num(vm, 'Timeline end')};
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

(async () => {
    console.log(`seed=${seed} cases=${cases}`);
    const byKind = {};
    let passed = 0, failed = 0;
    for (let c = 1; c <= cases; c++) {
        const vm = await loadVM();
        const end = num(vm, 'Timeline end');
        const P = getList(vm, 'Initial X').length;
        if (end !== 348) console.log(`warn: case ${c} initial Timeline end is ${end}, expected 348`);
        const picked = [];
        const count = 1 + Math.floor(rnd() * 2);
        while (picked.length < count) {
            const k = pick(KINDS);
            if (!picked.includes(k)) picked.push(k);
        }
        const edits = picked.map(k => applyEdit(vm, k, end));
        settle(vm, 'incremental');
        const resume = num(vm, 'Timeline resume');
        const inc = snapshot(vm);
        setVar(vm, 'Timeline dirty all', 1);
        setVar(vm, 'Timeline restart', 1);
        settle(vm, 'full recalculation');
        const full = snapshot(vm);
        vm.stopAll();

        const diff = firstDiff(inc, full, P);
        const label = edits.map(e => e.desc + (e.frame !== null ? ` @f${e.frame}` : '')).join(', ');
        if (diff) {
            failed++;
            console.log(`FAIL case ${c}: edit [${label}] resume=${resume} end=${inc.end}\n  first difference: ${diff}`);
        } else {
            passed++;
            console.log(`pass case ${c}: edit [${label}] resume=${resume} end=${inc.end}`);
        }
        picked.forEach((kind, i) => {
            (byKind[kind] = byKind[kind] || []).push({resume, frame: edits[i].frame, end: inc.end});
        });
    }

    console.log('\nResume frame by edit type (frames before resume are reused; resume = end+1 means none recomputed):');
    for (const kind of KINDS) {
        const rows = byKind[kind] || [];
        if (!rows.length) { console.log(`  ${kind}: no cases`); continue; }
        const resumes = rows.map(r => r.resume).sort((a, b) => a - b);
        console.log(`  ${kind}: n=${rows.length} resume min=${resumes[0]} median=${resumes[resumes.length >> 1]} max=${resumes[resumes.length - 1]}`);
        if (kind === 'near' || kind === 'detach') {
            console.log('    ' + rows.map(r => `f${r.frame}->${r.resume}${r.resume <= r.frame ? '' : ' (after f)'}`).join('  '));
        }
    }
    console.log(`\nsummary: ${passed} passed, ${failed} failed of ${cases}`);
    process.exitCode = failed ? 1 : 0;
})().catch(e => { console.error(e); process.exit(1); });
