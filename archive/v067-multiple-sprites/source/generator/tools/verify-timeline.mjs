import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
import {EditorSession} from './editor-session.mjs';

process.env.SCRATCH_OPTIMIZER_HEADLESS = '1';
process.env.LINE_RIDER_RELEASE_TEST = '1';

const session = new EditorSession();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const state = () => session.call('get_variable_list_data');
const click = (x, y) => session.clickStage(x - 240, 180 - y);
const key = name => session.pressKeys([
    {key: name, hold_duration_ms: 80, time_after_last_key_press_ms: 80},
]);
const seek = (frame, end) => session.clickStage(Math.round(-226 + 294 * frame / end), -142);
const ready = ({variables: v}) => +v['Timeline ready'] === 1 && +v['Timeline current pose'] === 1;

async function until(label, predicate) {
    const deadline = Date.now() + 25_000;
    while (Date.now() < deadline) {
        const result = await state();
        if (predicate(result)) return result;
        await wait(100);
    }
    throw new Error('Timed out waiting for ' + label);
}

function pointOnStage(vars, x, y) {
    return [(x - vars['Camera X']) * vars.Zoom, -20 - (y - vars['Camera Y']) * vars.Zoom];
}

try {
    await session.openFile(process.cwd() + '/dist/Line Rider.sb3');
    await session.call('green_flag');
    const demo = await until('full demo timeline', ready);
    const end = +demo.variables['Timeline end'];
    const reference = JSON.parse(execFileSync('python', ['-c',
        'import sys,json; sys.path.insert(0,"tools"); from course import default_track; import contact_reference as ref; print(json.dumps(ref.run(default_track())))',
    ], {encoding: 'utf8'}));
    assert.equal(end, reference.length);
    assert.equal(+demo.variables.Frame, 0);
    assert.equal(+demo.variables.Editing, 1);
    assert.deepEqual(demo.lists['Timeline Ride result'].items.map(Number), [...Array(end).fill(1), 4]);
    for (const axis of ['X', 'Y']) {
        const expected = [...demo.lists[axis].items, ...reference.flatMap(row => row[axis.toLowerCase()])];
        const actual = demo.lists['Timeline ' + axis].items;
        assert.equal(actual.length, expected.length);
        for (let i = 0; i < actual.length; i++) {
            assert.ok(Math.abs(actual[i] - expected[i]) < 1e-7, axis + ' at ' + i);
        }
    }
    const capture = await session.capture();
    await writeFile('artifacts/timeline-after.png', Buffer.from(capture.image_base64, 'base64'));
    console.log('PASS every demo frame matches the physics reference, through the finish at frame', end);

    await session.dragStage([[-226, -142], [-50, -142], [-112, -142]], 100);
    const selected = Math.round(114 * end / 294);
    const paused = await until('mouse scrub', ({variables: v}) => +v.Frame === selected);
    assert.equal(+paused.variables.Editing, 1);
    assert.equal(+paused.variables.Playing, 0);
    assert.equal(paused.lists.LX.length, demo.lists.LX.length);
    const points = demo.lists.X.length;
    const demoPose = frame => demo.lists['Timeline X'].items.slice(frame * points, (frame + 1) * points);
    assert.deepEqual(paused.lists.X.items, demoPose(selected));

    await click(425, 20);
    await until('Play mode at the selected frame', ({variables: v}) => +v.Editing === 0 && +v.Frame === selected);
    await key('n');
    await until('one paused step', ({variables: v}) => +v.Frame === selected + 1 && +v.Playing === 0);
    await click(331, 20);
    await until('Edit mode at the same frame', ({variables: v}) => +v.Frame === selected + 1 && +v.Editing === 1);
    console.log('PASS dragging, stepping, and switching modes retain the playhead');

    await key('f');
    await key('6');
    const fitted = (await state()).variables;
    await session.clickStage(...pointOnStage(fitted, 80, 52));
    const short = await until('earlier goal', snapshot => ready(snapshot) && +snapshot.variables['Goal X'] < 100);
    const shortEnd = +short.variables['Timeline end'];
    assert.ok(shortEnd < selected);
    assert.equal(+short.variables.Frame, shortEnd);
    assert.equal(+short.variables.State, 4);

    await key('z');
    const restored = await until('Undo restores the longer ride', snapshot => ready(snapshot) &&
        +snapshot.variables['Timeline end'] === end && +snapshot.variables.Frame === selected + 1);
    assert.deepEqual(restored.lists.X.items, demoPose(selected + 1));
    console.log('PASS goal edits clamp to an earlier finish and Undo restores the selected time');

    await key('h');
    await key('5');
    const home = (await state()).variables;
    await session.clickStage(...pointOnStage(home, 12, 25.6));
    const moved = await until('moved spawn', snapshot => ready(snapshot) && +snapshot.variables['Spawn X'] > 8);
    assert.equal(+moved.variables.Frame, selected + 1);
    assert.notEqual(+moved.lists.X.items[4], reference[selected].x[4]);
    assert.ok(Math.abs(moved.lists['Timeline X'].items[0] - moved.variables['Spawn X']) < 1e-7);
    await key('z');
    await until('original spawn', snapshot => ready(snapshot) && +snapshot.variables['Spawn X'] === 0);
    console.log('PASS moving the start recalculates the rider at the same frame');

    await key('h');
    await key('2');
    const drawingView = (await state()).variables;
    await session.dragStage([
        pointOnStage(drawingView, 40, 46),
        pointOnStage(drawingView, 115, 56),
    ], 160);
    const edited = await until('terrain edit', snapshot => ready(snapshot) && snapshot.lists.LX.length > demo.lists.LX.length);
    assert.equal(+edited.variables.Frame, selected + 1);
    assert.notDeepEqual(edited.lists.X.items, demoPose(selected + 1));
    await key('z');
    await until('original terrain', snapshot => ready(snapshot) && snapshot.lists.LX.length === demo.lists.LX.length);
    console.log('PASS drawing a new line changes the selected pose without moving the playhead');

    await key('h');
    await key('6');
    await session.clickStage(...pointOnStage((await state()).variables, -26, 20));
    const behind = await until('goal behind the spawn', snapshot => ready(snapshot) && +snapshot.variables['Goal X'] < -20);
    const crashEnd = +behind.variables['Timeline end'];
    assert.ok(crashEnd > end);
    assert.equal(+behind.lists['Timeline Ride result'].items.at(-1), 3);
    await seek(crashEnd, crashEnd);
    await until('first crash frame', ({variables: v}) => +v.Frame === crashEnd && +v.State === 3);
    await seek(0, crashEnd);
    await until('backward scrub clears the displayed crash', ({variables: v}) => +v.Frame === 0 && +v.State === 0);
    await key('z');
    await until('original goal', snapshot => ready(snapshot) && +snapshot.variables['Timeline end'] === end);
    console.log('PASS the crash bounds the timeline when the goal is never crossed');

    const page = session.requirePage();
    await (await page.createCDPSession()).send('Emulation.setTouchEmulationEnabled', {
        enabled: true, maxTouchPoints: 1,
    });
    await session.touchDragStage([[20, -142], [53, -142], [63, -142]], 120);
    const touch = await until('touch scrub', ({variables: v}) => +v.Frame > end - 8 && +v.Frame < end);
    assert.equal(+touch.variables.Playing, 0);
    await click(315, 56);
    await until('playback resumes and stops at the finish', ({variables: v}) =>
        +v.Editing === 0 && +v.Frame === end && +v.State === 4 && +v.Playing === 0);

    await seek(60, end);
    const beforeDetach = await until('seek back in Play', ({variables: v}) => +v.Frame === 60 && +v.State === 2);
    await key('x');
    await until('manual detach', snapshot => ready(snapshot) && +snapshot.variables.State === 3 &&
        +snapshot.variables['Timeline end'] === +beforeDetach.variables.Frame + 1);
    await click(377, 56);
    await until('Retry restores the natural timeline', snapshot => ready(snapshot) &&
        +snapshot.variables['Timeline end'] === end && +snapshot.variables.Playing === 1);
    console.log('PASS touch scrub, cached playback, detach, and Retry');
} finally {
    await session.close();
}
