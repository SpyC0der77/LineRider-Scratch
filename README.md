# Line Rider in Scratch

Open [dist/Line Rider.sb3](dist/Line%20Rider.sb3) in Scratch using **File > Load from your computer**, then click the green flag. The project opens in Edit and calculates the demo ride. Drag the timeline at the bottom to inspect any frame, or click **Run** to play from the selected frame. The **Edit / Play** switch keeps the playhead in place. Track, Edit, View and Help are dropdown menus. The second row selects the active tool and material. Use Scratch's fullscreen stage for larger controls.

The opening track and **Track > Demo course** use the same 413-segment rolling descent. The rider stays bound to the sled until the binding breaks. The timeline ends at that crash or when the mounted rider crosses the goal.

The interface starts in mobile mode, with touch instructions and no keyboard shortcuts. Pressing any key on the stage switches to desktop mode. Typing into the track-code answer box does not switch modes. Mobile erasing repairs one skipped segment only when its connected neighbors were removed less than 350 ms apart during the same drag. It checks the original endpoints and stable segment IDs, so unrelated lines and separate gestures do not bridge. Undo restores the entire erase gesture.

In Play, the expand icon beside the Edit / Play selector opens an uninterrupted view across the full Scratch stage. It hides the toolbars and timeline and expands the drawing bounds. The small corner icon returns to the current frame. A paused ride has a touch Play button. At the end, touch Retry or Edit. Scratch's own fullscreen control enlarges the player window.

## Editor

| Control | Action |
| --- | --- |
| Tool > Pencil / 1 | Drag to draw a connected stroke. Long pointer moves are subdivided into short line segments. |
| Tool > Straight line / 2 | Drag to preview a straight line; release to commit. |
| Tool > Eraser / 3 | Drag over segments to remove them. The circle shows the erase radius. |
| Tool > Pan / 4 | Drag the canvas to move the camera. Arrow keys also pan. |
| Tool > Start flag / 5 | Click to place the rider's starting point. Put it just above the track. |
| Tool > Goal flag / 6 | Click to place the finish flag near the riding surface. |
| Material dropdown | Select Normal, Grip, Ice, Scenery, Acceleration or Reverse boost directly for new segments. The current choice is checked. |
| Edit > Undo / Z, Redo / Y | Undo or redo one complete stroke or track operation. Each stack holds twelve snapshots. |
| View > Zoom in / Zoom out | Zoom around the center of the canvas. |
| View > Fit track / F | Fit the complete track and flags in view. |
| View > Start view / H | Return to the starting view. |
| View > Grid and snapping / G | Toggle a measuring grid and five-unit snapping. |
| Track > New track | Clear the canvas and place default start and goal flags. Undo restores the previous track. |
| Track > Save track code | Generate a compact code for the current track. Double-click its row, then Ctrl+A and Ctrl+C to copy. |
| Track > Load track code | Paste a code into Scratch's answer box. Empty input cancels. A valid load is undoable. |
| Track > Demo course | Restore the long rolling course. Also undoable. |
| Help > Controls and storage | Show controls and storage instructions. Click to close. |

Click a menu item to choose it. Disabled actions are muted. Click outside a menu, click its header again, or press Q to dismiss it; the dismissal click does not draw. With a menu open, Up/Down selects an enabled item and Enter activates it. Opening a menu suspends playback until it closes. Keyboard shortcuts work when menus are closed. Track and Edit menu actions that require editing remain available in Play mode. They first ask: This action will change the mode to "Edit". Are you sure you want to do this? Switch to Edit confirms and performs the requested action; Cancel leaves the mode, track and preview intact. Playback is frozen while the dialog is open and resumes on Cancel if it was running. Enter confirms and Q cancels. The same guard applies to S, L, Z, Y and E. Unavailable actions, such as loading an empty saved slot or undoing with no history, remain disabled. Step and Detach do not require switching to Edit. The explicit Edit mode switch still changes mode directly.

**Track > Remove goal** hides the finish flag and disables the finish condition. The item becomes **Restore goal**. This change supports undo/redo and the saved track slot. Placing a new goal flag re-enables finishing.

Stroke ends snap to nearby existing endpoints. Lines are one-sided and automatically oriented left to right, so their riding surface faces upward. The tool preserves upward-facing normals when drawing from right to left. Vertical walls have a direction-dependent collision side.

Normal lines apply contact friction. Grip lines add damping along the track tangent. Ice disables point friction. Scenery is visible but does not collide. Acceleration adds the original lr-core 0.1 tangent boost on contact; Reverse boost applies it in the opposite direction. Acceleration lines are red and retain their material in saved codes. The renderer clips all terrain and rider strokes to the canvas, including very long offscreen lines.

## Playback

- **Timeline** pauses playback and moves to the frame under the pointer. It works in Edit and Play. The last frame is the first crash or the mounted crossing of the goal.
- The timeline recalculates when you release a stroke or finish moving a flag. The spinner appears during recalculation. If the edited ride ends sooner, the playhead shows that end. Undo can bring the original frame back into range.
- **Run / Space** plays from the selected frame, or starts over from the end. Click again to pause.
- **Step / N** advances one frame and stays paused. Step is disabled during playback and at the end.
- **Retry / R** returns to frame zero. In Edit it also restores the start view. In Play it starts playback.
- **Edit > Return to editor / E** stops playback at the current frame so you can edit with the rider in view.
- **X** detaches the rider for a crash test. Retry restores the original run.
- A ride with no earlier finish or crash can reach Scratch's storage limit at frame 9,089. The status bar labels that endpoint **Preview limit**.

## Keeping your tracks

**Track > Save track code** creates an `LR1` code that can be kept in a text file or sent to someone else. Double-click the code row, then press Ctrl+A and Ctrl+C. Close the dialog when finished. **Track > Load track code** opens Scratch's answer box for pasting. Submit an empty answer to cancel. Invalid, incomplete, oversized or altered codes show an error and leave the track, flags, saved slot and undo history untouched. Loading a valid code creates one undo step and rebuilds the collision data. Export can be used during Play; it freezes and resumes the same ride. Import from Play uses the existing confirmation before switching to Edit.

Codes retain every segment, its material, the start flag, goal position and goal-enabled setting. Coordinates are rounded to hundredths of a world unit, at most 0.005 units per coordinate. Connected endpoints stay connected. The code omits redundant line starts and computed normals/bounds, uses signed endpoint deltas and variable-length base-32 numbers, and ends with a checksum. The preserved 128-line track uses 823 characters, about 89% less than its segment-array JSON. The limit remains 3,000 segments. Spaces, tabs, line breaks, hyphens and lowercase letters are accepted on load. [The format specification](docs/track-code-format.md) describes the exact layout.

**Track > Save slot** copies the current track and flags into one saved slot inside the project. **Track > Load saved slot** restores that slot; Undo can reverse a load. The slot survives the green flag and saving/reopening the `.sb3`.

The saved slot is not a filesystem download. Use a track code to keep individual tracks, or Scratch's **File > Save to your computer** to keep the entire editor and its saved slot. Neither method requires a cloud service or account. Closing Scratch without saving the project or copying a code can lose changes.

New and Demo preserve the saved slot. The green flag resets the editor and run state, while keeping the current track, flags and saved slot. It clears the undo/redo history.

## Build and verification

The native project is divided into **Game controller**, **Physics**, **Track editor**, **Menus**, **Track codes**, and **Renderer**, plus the existing **Prompt history** sprite. Each sprite has a comment explaining its responsibilities and a list of incoming requests. The build report records the block count for each sprite. [The sprite guide](docs/sprite-architecture.md) explains the shared state, message boundaries, and build process.

Run `python tools/build.py` to generate the main `dist/Line Rider.sb3`, native project JSON, and build report. The generator uses Python's standard library and the checked-in lr-core rider data. `tools/mounted_rider.py` defines the solver, `tools/timeline.py` precomputes and reads the frame cache, and `tools/split_sprites.py` gives each subsystem its own Scratch sprite. Earlier versions are available in Git history.

Use `python tools/build.py --testing` for a local project with capture and step controls. `tools/editor-session.mjs` loads that fixture when available. Set `LINE_RIDER_RELEASE_TEST=1` to test the main build directly. The session points to the local Scratch project optimizer's Chromium adapter.

- `node tools/verify-timeline.mjs` checks the full ride through frame 348, scrubbing, flag edits, Undo and crashes.
- `node tools/verify-stroke-timeline.mjs` checks live drawing, calculation after release, and the loading spinner.
- `node tools/verify-track-code.mjs` exercises native track code export and import. Build the local test fixture first.

The optional upload helper reads the account name from `SCRATCH_USERNAME` or an ignored `artifacts/scratch-upload.json` containing the existing Scratch project ID. It reads the password from a private file supplied at runtime.

## Physics source and limits

Adapted from David Lu / conundrumer's [lr-core 0.8.2](https://github.com/conundrumer/lr-core), commit `ce48ebed967d24ff4582995b31342440901f913d`. Attribution and the MIT license are embedded in the Scratch project and included in `LICENSE.lr-core.txt`.

The mounted solver uses Verlet integration with gravity 0.175 and six passes of distance constraints and line contacts. A 64-unit spatial grid supplies nearby segments in track order. The rider's binding determines when the ride crashes. The renderer uses the cached positions to draw the sled, rider and scarf.

Extreme speeds can tunnel past thin terrain. Tracks can contain up to 3,000 segments. Undo snapshots and the saved slot count toward the project file size.
