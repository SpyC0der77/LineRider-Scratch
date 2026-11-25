// Headless scratch-vm benchmark of the ride-timeline computation (no renderer).
// Usage: node tools/bench-vm.cjs [file.sb3] [--runs N]
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {createRequire} = require('node:module');

const NM = 'C:/Users/Carter/code/Scratch/goboscript/tools/scratch-test/node_modules';
const req = createRequire(path.join(NM, 'package.json'));
const VM = req('scratch-vm');
const {ScratchStorage} = req('scratch-storage');
req('minilog').disable();
// scratch-vm logs a 'Translation ... missing' warning per block; drop only those lines.
const warn = console.warn;
console.warn = (...a) => { if (!String(a[0]).startsWith('Translation for')) warn(...a); };

const args = process.argv.slice(2);
const runsAt = args.indexOf('--runs');
const runs = runsAt >= 0 ? Number(args[runsAt + 1]) : 5;
const fileArg = args.find((a, i) => a !== '--runs' && (runsAt < 0 || i !== runsAt + 1));
const file = path.resolve(fileArg || path.join(__dirname, '..', 'dist', 'Line Rider.sb3'));
const TIMEOUT_MS = 120000;

const stage = vm => vm.runtime.getTargetForStage();
const getVar = (vm, name) => stage(vm).lookupVariableByNameAndType(name, '').value;
const setVar = (vm, name, v) => { stage(vm).lookupVariableByNameAndType(name, '').value = v; };
const getList = (vm, name) => stage(vm).lookupVariableByNameAndType(name, 'list').value;
const isReady = vm => Number(getVar(vm, 'Timeline ready')) === 1 && Number(getVar(vm, 'Timeline current pose')) === 1;
const sha256 = list => crypto.createHash('sha256').update(JSON.stringify(list)).digest('hex');

// Steps the runtime until the predicate holds; tick time is measured around each _step call only.
function stepUntil(vm, done, label) {
    const start = performance.now();
    let ticks = 0, tickMs = 0, maxTickMs = 0;
    while (!done()) {
        if (performance.now() - start > TIMEOUT_MS) throw new Error(`Timed out after ${TIMEOUT_MS} ms: ${label}`);
        const t0 = performance.now();
        vm.runtime._step();
        const dt = performance.now() - t0;
        tickMs += dt;
        maxTickMs = Math.max(maxTickMs, dt);
        ticks++;
    }
    return {ticks, tickMs, maxTickMs, wallMs: performance.now() - start};
}

async function oneRun(withRecalc) {
    const vm = new VM();
    vm.attachStorage(new ScratchStorage());
    await vm.loadProject(fs.readFileSync(file));
    vm.runtime.currentStepTime = 1000 / 30;
    const t0 = performance.now();
    vm.greenFlag();
    const first = stepUntil(vm, () => isReady(vm), 'initial timeline');
    const end = Number(getVar(vm, 'Timeline end'));
    const out = {
        total_ms: performance.now() - t0,
        ticks: first.ticks,
        tick_ms: first.tickMs,
        max_tick_ms: first.maxTickMs,
        ms_per_frame: first.tickMs / end,
        timeline_end: end,
        hash_X: sha256(getList(vm, 'Timeline X')),
        hash_Y: sha256(getList(vm, 'Timeline Y')),
    };
    if (withRecalc) {
        // Time a full rebuild from the finished state (not limited by the budget logic's first pass).
        setVar(vm, 'Timeline dirty all', 1); setVar(vm, 'Timeline restart', 1);
        // Wait for the restart to be consumed and the timeline to finish rebuilding.
        let busy = false;
        const r = stepUntil(vm, () => {
            if (!isReady(vm)) busy = true;
            return busy && Number(getVar(vm, 'Timeline restart')) === 0 && isReady(vm);
        }, 'recalc');
        const recalcEnd = Number(getVar(vm, 'Timeline end'));
        out.recalc = {ticks: r.ticks, tick_ms: r.tickMs, total_ms: r.wallMs, ms_per_frame: r.tickMs / recalcEnd, timeline_end: recalcEnd};
    }
    vm.stopAll();
    return out;
}

const median = xs => { const s = [...xs].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const round = o => JSON.parse(JSON.stringify(o, (k, v) => typeof v === 'number' ? Number(v.toFixed(3)) : v));

(async () => {
    const results = [];
    for (let i = 0; i < runs; i++) results.push(await oneRun(true));
    const recalcRuns = results.map(r => r.recalc).filter(Boolean);
    const first = results[0];
    const runRows = results.map(({total_ms, ticks, tick_ms, max_tick_ms, ms_per_frame}) => ({total_ms, ticks, tick_ms, max_tick_ms, ms_per_frame}));
    const out = {
        file,
        runs: runRows,
        median_ms_per_frame: median(runRows.map(r => r.ms_per_frame)),
        recalc: {
            runs: recalcRuns.length,
            median_ms_per_frame: recalcRuns.length ? median(recalcRuns.map(r => r.ms_per_frame)) : null,
            first: first.recalc,
        },
        timeline_end: first.timeline_end,
        hash_X: first.hash_X,
        hash_Y: first.hash_Y,
        hashes_stable_across_runs: results.every(r => r.hash_X === first.hash_X && r.hash_Y === first.hash_Y),
    };
    console.log(JSON.stringify(round(out), null, 2));
})().catch(e => { console.error(e); process.exit(1); });
