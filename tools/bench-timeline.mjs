import {resolve} from 'node:path';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const args = process.argv.slice(2);
const runsAt = args.indexOf('--runs');
const runs = runsAt >= 0 ? Number(args[runsAt + 1]) : 3;
const fileArg = args.find((arg, i) => arg !== '--runs' && (runsAt < 0 || i !== runsAt + 1));
const file = resolve(fileArg ?? 'dist/Line Rider.sb3');
const TIMEOUT_MS = 120_000;
const POLL_MS = 20;
const wait = ms => new Promise(r => setTimeout(r, ms));
const scalar = async (session, name) =>
    Number((await session.call('get_variable_list_data', {item_name: name})).variables[name]);
const ready = async session => await scalar(session, 'Timeline ready') === 1
    && await scalar(session, 'Timeline current pose') === 1
    && await scalar(session, 'Timeline loading') === 0;
const median = values => {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

async function untilReady(session, label) {
    const deadline = performance.now() + TIMEOUT_MS;
    while (performance.now() < deadline) {
        if (await ready(session)) return performance.now();
        await wait(POLL_MS);
    }
    throw new Error(`Timed out after ${TIMEOUT_MS} ms waiting for ${label}`);
}

// Pencil stroke copied from tools/verify-stroke-timeline.mjs; times the rebuild after release.
async function timeRecalculation(session) {
    const page = session.requirePage();
    const end = await scalar(session, 'Timeline end');
    await session.call('set_variable_values', {values: {Brush: 3}});
    await session.clickStage(-112, -142);
    const frame = Math.round(114 * end / 294);
    const deadline = performance.now() + TIMEOUT_MS;
    while (await scalar(session, 'Frame') !== frame) {
        if (performance.now() > deadline) throw new Error('Timed out selecting frame');
        await wait(POLL_MS);
    }
    const segmentsBefore = (await session.call('get_variable_list_data', {item_name: 'LX'})).lists.LX.length;
    const move = async (x, y) => {
        const p = await session.stagePoint(x, y);
        await page.mouse.move(p.x, p.y);
    };
    await move(-150, -18);
    await page.mouse.down();
    for (const [x, y] of [[-118, -31], [-85, -46], [-55, -65], [-24, -89]]) {
        await move(x, y);
        await wait(110);
    }
    await page.mouse.up();
    const started = performance.now();
    while (await ready(session)) {
        if (performance.now() - started > TIMEOUT_MS) throw new Error('Recalculation never started');
        await wait(POLL_MS);
    }
    const segmentsAfter = (await session.call('get_variable_list_data', {item_name: 'LX'})).lists.LX.length;
    if (segmentsAfter <= segmentsBefore) throw new Error('Pencil stroke added no segments');
    const finished = await untilReady(session, 'recalculation');
    return finished - started;
}

async function oneRun(withRecalc) {
    const session = new EditorSession();
    try {
        await session.openFile(file);
        const start = performance.now();
        await session.call('green_flag');
        const done = await untilReady(session, 'initial timeline');
        const result = {ms: done - start, timeline_end: await scalar(session, 'Timeline end')};
        if (withRecalc) result.recalc_ms = await timeRecalculation(session);
        return result;
    } finally {
        await session.close();
    }
}

try {
    const results = [];
    for (let i = 0; i < runs; i++) results.push(await oneRun(false));
    const recalc = await oneRun(true);
    const summary = {
        file,
        runs: results.map(r => Math.round(r.ms)),
        median_ms: Math.round(median(results.map(r => r.ms))),
        timeline_end: results[0].timeline_end,
        recalc_ms: Math.round(recalc.recalc_ms),
    };
    console.log(JSON.stringify(summary, null, 2));
} catch (error) {
    console.error(error);
    process.exitCode = 1;
}
