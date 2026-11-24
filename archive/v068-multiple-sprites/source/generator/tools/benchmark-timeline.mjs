import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import {cpus} from 'node:os';
import {resolve} from 'node:path';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const session = new EditorSession();
const files = {
    before: resolve('archive/v064-multiple-sprites/Line Rider.sb3'),
    after: resolve('dist/Line Rider.sb3'),
};
const repetitions = 5;
let page;
let cdp;

async function watch(items, condition, value) {
    return page.evaluate(async ({items, condition, value}) => {
        const deadline = performance.now() + 45_000;
        while (performance.now() < deadline) {
            const values = {};
            for (const name of items) {
                const {variables} = await window.__scratchOptimizer.call('get_variable_list_data', {item_name: name});
                values[name] = Number(variables[name]);
            }
            if (condition === 'gte' ? values[items[0]] >= value : items.every(name => values[name] === value)) {
                return {time: performance.now(), values};
            }
            await new Promise(requestAnimationFrame);
        }
        throw new Error('Timed out waiting for ' + items.join(', '));
    }, {items, condition, value});
}

const now = () => page.evaluate(() => performance.now());
const ready = () => watch(['Timeline ready', 'Timeline current pose'], 'all', 1);
const frame = n => watch(['Frame'], 'gte', n);
const exactFrame = n => watch(['Frame'], 'all', n);

async function click(x, y) {
    const point = await session.stagePoint(x, y);
    const time = await now();
    await page.mouse.click(point.x, point.y, {delay: 60});
    return time;
}

async function browserTaskTime() {
    const {metrics} = await cdp.send('Performance.getMetrics');
    return metrics.find(entry => entry.name === 'TaskDuration').value * 1000;
}

async function run(version) {
    await session.loadCurrentFile(files[version]);
    const current = version === 'after';
    const start = await now();
    await session.call('green_flag');
    // A nonzero Canvas bottom marks the first native renderer pass.
    const paint = await watch(['Canvas bottom'], 'all', current ? -130 : -153);
    const firstFrame = frame(1);
    const runClick = await click(75, 124);
    const first = await firstFrame;
    const elapsedStart = await frame(20);
    const taskStart = await browserTaskTime();
    const elapsedEnd = await frame(200);
    const taskEnd = await browserTaskTime();
    const played = elapsedEnd.values.Frame - elapsedStart.values.Frame;
    const finish = await watch(['State'], 'all', 4);
    const end = (await frame(200)).values.Frame;
    const sample = {
        editorMs: paint.time - start,
        coldRunMs: first.time - runClick,
        playbackFps: played * 1000 / (elapsedEnd.time - elapsedStart.time),
        mainThreadMsPerFrame: (taskEnd - taskStart) / played,
        firstRunFinishMs: finish.time - runClick,
        terminalFrame: end,
    };
    if (current) {
        const scrubMs = [];
        for (const wanted of [40, 160, 90, 180, 30]) {
            const x = Math.round(-226 + 294 * wanted / end);
            const observedFrame = Math.round((x + 226) * end / 294);
            // Arm the probe before mouse-down to measure the update during the click.
            const delivered = exactFrame(observedFrame);
            const pressed = await click(x, -142);
            scrubMs.push((await delivered).time - pressed);
        }
        sample.scrubMs = scrubMs;
        await click(75, 124);
        await frame(40);
        const pausedFrom = await now();
        const seeked = exactFrame(0);
        await click(-226, -142);
        await seeked;
        await watch(['Playing'], 'all', 0);
        assert.ok(await now() - pausedFrom < 2000, 'Scrubbing should promptly pause playback');
        const warmStart = frame(1);
        const warmClick = await click(75, 124);
        sample.warmRunMs = (await warmStart).time - warmClick;

        await click(91, 160);
        await watch(['Editing'], 'all', 1);
        await session.pressKeys([
            {key: 'h', hold_duration_ms: 60, time_after_last_key_press_ms: 60},
            {key: '5', hold_duration_ms: 60, time_after_last_key_press_ms: 60},
        ]);
        const editClick = await click(-140, 46);
        await watch(['Timeline ready'], 'all', 0);
        sample.startEditMs = (await ready()).time - editClick;
    }
    return sample;
}

try {
    await session.openFile(files.before);
    page = session.requirePage();
    cdp = await page.createCDPSession();
    await cdp.send('Performance.enable');
    const samples = {before: [], after: []};
    for (let i = 0; i < repetitions; i++) {
        for (const version of i % 2 === 0 ? ['before', 'after'] : ['after', 'before']) {
            const sample = await run(version);
            samples[version].push(sample);
            console.log(version, i + 1, JSON.stringify(sample));
        }
    }
    const builds = {};
    for (const [version, path] of Object.entries(files)) {
        const bytes = await readFile(path);
        builds[version] = {path, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex')};
    }
    await writeFile('artifacts/timeline-benchmark.json', JSON.stringify({
        repetitions, cpu: cpus()[0].model, userAgent: await page.evaluate(() => navigator.userAgent), builds, samples,
    }, null, 2) + '\n');
} finally {
    await session.close();
}
