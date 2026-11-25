// Headless scratch-vm profile of the ride-timeline computation, by custom procedure and opcode.
// Usage: node tools/profile-vm.cjs [file.sb3]
// Profiling overhead inflates absolute times; compare shares, not milliseconds.
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

const file = path.resolve(process.argv[2] || path.join(__dirname, '..', 'dist', 'Line Rider.sb3'));
const TIMEOUT_MS = 120000;

const stage = vm => vm.runtime.getTargetForStage();
const getVar = (vm, name) => stage(vm).lookupVariableByNameAndType(name, '').value;
const isReady = vm => Number(getVar(vm, 'Timeline ready')) === 1 && Number(getVar(vm, 'Timeline current pose')) === 1;

// Procedure attribution: a procedure is "active" on a thread while its definition block is on that thread's stack.
// Time is charged only while the thread is being stepped (between stepThread entry and exit), so yields and
// other threads do not leak into a procedure's totals.
function installProcedureProfiler(vm) {
    const defName = new Map();
    for (const target of vm.runtime.targets) {
        for (const block of Object.values(target.blocks._blocks)) {
            if (block.opcode !== 'procedures_definition') continue;
            const proto = target.blocks.getBlock(block.inputs.custom_block.block);
            defName.set(block.id, proto.mutation.proccode);
        }
    }
    const incl = new Map(), self = new Map(), calls = new Map();
    const bump = (m, k, v) => m.set(k, (m.get(k) || 0) + v);
    let cur = null, lastT = performance.now();

    const flush = () => {
        const now = performance.now();
        if (cur) {
            const dt = now - lastT;
            const stack = cur.procNames;
            if (stack.length) {
                const seen = new Set();
                for (const n of stack) if (!seen.has(n)) { seen.add(n); bump(incl, n, dt); }
                bump(self, stack[stack.length - 1], dt);
            } else {
                bump(self, '(top-level script)', dt);
            }
        }
        lastT = now;
    };
    const resync = thread => {
        thread.procNames = thread.stack.filter(id => defName.has(id)).map(id => defName.get(id));
    };

    const threadProto = Object.getPrototypeOf(vm.runtime.threads[0]);
    const seqProto = Object.getPrototypeOf(vm.runtime.sequencer);
    const origPush = threadProto.pushStack;
    const origPop = threadProto.popStack;
    const origStep = seqProto.stepThread;

    threadProto.pushStack = function (blockId) {
        origPush.call(this, blockId);
        const name = defName.get(blockId);
        if (name !== undefined) {
            if (this === cur) flush();
            (this.procNames || (this.procNames = [])).push(name);
            bump(calls, name, 1);
        }
    };
    threadProto.popStack = function () {
        const top = this.stack[this.stack.length - 1];
        if (defName.has(top) && this.procNames && this.procNames.length) {
            if (this === cur) flush();
            this.procNames.pop();
        }
        return origPop.call(this);
    };
    seqProto.stepThread = function (thread) {
        flush();
        cur = null;
        resync(thread);
        cur = thread;
        try {
            return origStep.call(this, thread);
        } finally {
            flush();
            cur = null;
        }
    };
    return {incl, self, calls, restore: () => {
        threadProto.pushStack = origPush;
        threadProto.popStack = origPop;
        seqProto.stepThread = origStep;
    }};
}

(async () => {
    const vm = new VM();
    vm.attachStorage(new ScratchStorage());
    await vm.loadProject(fs.readFileSync(file));
    vm.runtime.currentStepTime = 1000 / 30;
    vm.greenFlag();
    // Threads now exist; attach profilers before the first step so the timeline computation is fully covered.
    const procs = installProcedureProfiler(vm);
    // scratch-vm's built-in Profiler is only enabled when window.performance exists (not in Node) and it
    // records block execution counts only, not opcode time. The VM calls these methods on runtime.profiler
    // and per-op counters live on the cached ops; a stub gives the counts without a DOM shim.
    const opFrames = new Map();
    const profiler = {
        idByName: () => 0,
        start () {}, stop () {}, increment () {}, reportFrames () {},
        frame (id, arg) {
            if (!opFrames.has(arg)) opFrames.set(arg, {arg, count: 0});
            return opFrames.get(arg);
        },
    };
    vm.runtime.profiler = profiler;

    const start = performance.now();
    let tickMs = 0, ticks = 0;
    while (!isReady(vm)) {
        if (performance.now() - start > TIMEOUT_MS) throw new Error('Timed out waiting for timeline');
        const t0 = performance.now();
        vm.runtime._step();
        tickMs += performance.now() - t0;
        ticks++;
    }
    const timelineEnd = Number(getVar(vm, 'Timeline end'));
    procs.restore();
    vm.runtime.profiler = null;
    const opCounts = new Map([...opFrames.values()].map(f => [f.arg, f.count]));

    const fmt = (n, d = 2) => Number(n).toFixed(d);
    const pad = (s, w, right = false) => (right ? String(s).padStart(w) : String(s).padEnd(w));
    const totalCompute = tickMs;
    console.log(`File: ${file}`);
    console.log(`Timeline end: ${timelineEnd} frames   Ticks: ${ticks}   Profiled compute: ${fmt(totalCompute, 1)} ms   Per frame: ${fmt(totalCompute / timelineEnd, 3)} ms`);
    console.log('');

    const names = new Set([...procs.incl.keys(), ...procs.self.keys(), ...procs.calls.keys()]);
    const procRows = [...names]
        .map(k => ({name: k, calls: procs.calls.get(k) || 0, incl: procs.incl.get(k) || 0, self: procs.self.get(k) || 0}))
        .sort((a, b) => b.incl - a.incl);
    console.log('Per procedure (sorted by inclusive ms; self = time with this procedure innermost):');
    console.log(pad('proccode', 44) + pad('calls', 9, true) + pad('incl ms', 12, true) + pad('ms/call', 12, true) + pad('self ms', 12, true) + pad('incl %', 9, true));
    for (const r of procRows) {
        console.log(pad(r.name, 44) + pad(r.calls, 9, true) + pad(fmt(r.incl), 12, true) +
            pad(r.calls ? fmt(r.incl / r.calls, 4) : '-', 12, true) + pad(fmt(r.self), 12, true) +
            pad(fmt(100 * r.incl / totalCompute, 1), 9, true));
    }
    console.log('');

    const ops = [...opCounts.entries()].map(([op, count]) => ({op, count}))
        .sort((a, b) => b.count - a.count).slice(0, 20);
    console.log('Top 20 opcodes by execution count:');
    console.log(pad('opcode', 44) + pad('count', 12, true));
    for (const o of ops) console.log(pad(o.op, 44) + pad(o.count, 12, true));
    console.log('(opcode time is not recorded by scratch-vm; per-opcode counts only)');
    vm.stopAll();
    process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
