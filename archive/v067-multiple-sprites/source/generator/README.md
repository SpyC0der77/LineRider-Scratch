# Line Rider in Scratch

Open [dist/Line Rider.sb3](dist/Line%20Rider.sb3) in Scratch using **File > Load from your computer**, then click the green flag. The project opens in Edit and calculates the demo ride. Drag the timeline at the bottom to inspect any frame, or click **Run** to play from the selected frame. The **Edit / Play** switch keeps the playhead in place. Track, Edit, View and Help are dropdown menus. The second row selects the active tool and material. Use Scratch's fullscreen stage for larger controls.

The opening track and **Track > Demo course** use a physical launch lip, short drop and sloping catch. The rider is always an articulated physical body. A finite seat, deck and rear post collide with the body, and elastic rope grips yield with stretch. The rider clears the sled, physically returns and finishes seated. `Mounted` reports seat proximity and posture for the finish condition. `tracks/current.json` retains the previous owner's canvas as a backup.

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
- Track and flag edits update the selected frame as soon as it has been recalculated. If the edited ride ends sooner, the playhead shows that end. Undo can bring the original frame back into range.
- **Run / Space** plays from the selected frame, or starts over from the end. Click again to pause.
- **Step / N** advances one frame and stays paused. Step is disabled during playback and at the end.
- **Retry / R** returns to frame zero. In Edit it also restores the start view. In Play it starts playback.
- **Edit > Return to editor / E** stops playback at the current frame so you can edit with the rider in view.
- **X** detaches the rider for a crash test. Retry restores the original run.
- A ride with no earlier finish or crash can reach Scratch's storage limit at frame 8,694. The status bar labels that endpoint **Preview limit**.

## Keeping your tracks

**Track > Save track code** creates an `LR1` code that can be kept in a text file or sent to someone else. Double-click the code row, then press Ctrl+A and Ctrl+C. Close the dialog when finished. **Track > Load track code** opens Scratch's answer box for pasting. Submit an empty answer to cancel. Invalid, incomplete, oversized or altered codes show an error and leave the track, flags, saved slot and undo history untouched. Loading a valid code creates one undo step and rebuilds the collision data. Export can be used during Play; it freezes and resumes the same ride. Import from Play uses the existing confirmation before switching to Edit.

Codes retain every segment, its material, the start flag, goal position and goal-enabled setting. Coordinates are rounded to hundredths of a world unit, at most 0.005 units per coordinate. Connected endpoints stay connected. The code omits redundant line starts and computed normals/bounds, uses signed endpoint deltas and variable-length base-32 numbers, and ends with a checksum. The preserved 128-line track uses 823 characters, about 89% less than its segment-array JSON. The original 140-line Demo course uses 898 characters. The limit remains 3,000 segments. Spaces, tabs, line breaks, hyphens and lowercase letters are accepted on load. [The format specification](docs/track-code-format.md) describes the exact layout.

**Track > Save slot** copies the current track and flags into one saved slot inside the project. **Track > Load saved slot** restores that slot; Undo can reverse a load. The slot survives the green flag and saving/reopening the `.sb3`.

The saved slot is not a filesystem download. Use a track code to keep individual tracks, or Scratch's **File > Save to your computer** to keep the entire editor and its saved slot. Neither method requires a cloud service or account. Closing Scratch without saving the project or copying a code can lose changes.

New and Demo preserve the saved slot. The green flag resets the editor and run state, while keeping the current track, flags and saved slot. It clears the undo/redo history.

## Build and verification

The native project is divided into **Game controller**, **Physics**, **Track editor**, **Menus**, **Track codes**, and **Renderer**, plus the existing **Prompt history** sprite. Each sprite has a comment explaining its responsibilities and a list of incoming requests. The build report records the block count for each sprite. [The sprite guide](docs/sprite-architecture.md) explains the shared state, message boundaries, and build process.

Local Scratch account metadata, historical publishing-helper copies, Python bytecode and local credential/configuration files are excluded by the root `.gitignore`. Archived game builds and their generators remain included. The lr-core reference is included as ordinary source files, with no submodule setup required. Its original Git administration data is retained locally under an ignored `.git-local-metadata` directory.

The optional upload helper reads the account name from `SCRATCH_USERNAME` or the `owner` field in the ignored `artifacts/scratch-upload.json`. That local record must also contain the existing project `id`. The password is read from a private file supplied at runtime. Account details are not part of the public source.

Run `python tools/build.py` to rebuild the project. It uses Python's standard library and the checked-in `reference/lr-core` source. `tools/core.py` contains the point solver and its Scratch block builder; `tools/build.py` assembles the editor, game states, spatial grid, clipping and SVG control assets. `tools/split_sprites.py` places each procedure in its owning sprite and creates native messages for calls between sprites. All delivered behavior runs in native Scratch blocks with the built-in Pen extension. No JavaScript extension or development server is needed.

Every build is also copied into its own folder in [archive](archive/README.md), with its exact native Scratch code, all assets, a checksum, a repacking script and the complete Python generator. The archive also preserves every older `.sb3` found in this workspace. The original demo and blank baseline have verified original generators; intermediate historical versions retain their exact native Scratch code because their original Python generators were overwritten. Each version records what could be recovered. Run `python tools/archive_versions.py --recover` to discover additional old artifacts without replacing existing snapshots.

`node tools/verify-track-code.mjs` exercises native code export/copy selection, round trips, all materials, disconnected and vertical lines, flags, goal removal, invalid input, undo/redo, Play-mode behavior and the 3,000-line limit. The generator is in `tools/track_code.py`; it emits stock Scratch blocks and performs no per-frame encoding work.

The build removes unreachable procedures and unused scalar state, writes compact variable reporters, and arranges scripts into labeled subsystem columns. The delivered project has no capture/test controls. `dist/testing/Line Rider.sb3` is a separate fixture with capture gates for screenshots and tests; `tools/editor-session.mjs` selects that fixture for automated verification. Set `LINE_RIDER_RELEASE_TEST=1` to exercise the delivered file directly. `dist/build-report.json` records cleanup counts. `node tools/verify-mobile-play.mjs` checks mobile detection, real touch erasing, the 350 ms cutoff, disconnected lines, gesture undo/redo and uninterrupted Play.

`python tools/reference_check.py` generates a numerical reference for the first 60 physics frames. `node tools/verify-editor.mjs`, which invokes `tools/verify-menus.mjs`, runs the native Scratch project in the local project-optimizer's isolated Chromium session. Its purpose-built pointer adapter lives in `tools/editor-session.mjs`. The optimizer import path in those files is specific to this machine.

The current verification covers dropdown selection and dismissal, disabled menu items, native keyboard navigation, direct tool/material choices, goal removal/restoration and undo/redo, drawing after dismissal, save/load including the removed-goal state, zoom, grid selection, help, playback and numerical equivalence over 60 frames. Earlier editor checks also exercised erase, flag placement, saved slot export/reload, panning, crash/retry, and completion of the previous sample course. `tools/menus.py` defines the shared menu model, input routing and native Scratch menu costumes. Results and before/after screenshots are in `artifacts/`. VM step samples are measurements of Scratch's runtime loop, not display frame-rate guarantees.

## Physics source and limits

Adapted from David Lu / conundrumer's [lr-core 0.8.2](https://github.com/conundrumer/lr-core), commit `ce48ebed967d24ff4582995b31342440901f913d`. The upstream package declares MIT licensing. Attribution and license text are embedded in the Scratch project and included in `LICENSE.lr-core.txt`.

The body and sled use the same Verlet integration and eight constraint/contact passes throughout the run, with gravity 0.175. The rigid sled retains six distance constraints. Torso, neck, elbows and knees use mass-weighted bones and anatomical limits. Passive muscle springs preserve the forward-reaching arms and the original leg proportions throughout the run. Support pressure and seat proximity load a compliant leg-balance spring that brings the feet forward after landing, with mass-weighted reaction on the hip and sled. Circle/capsule contacts exchange equal and opposite impulses with the finite seat, deck and rear post, including swept contact when a body part crosses a moving surface. Contact friction, elastic yielding grips and a balance spring loaded by actual support forces produce the rider's motion. The rope has its own physical loose end and a maximum length; it is drawn from those simulated points. When support is lost, those contact forces vanish naturally. The renderer reads physical particle positions directly, including the knees and elbows. No body pose or velocity is reset on departure or return. A 64-unit spatial grid supplies nearby terrain in source order; camera coordinates do not affect physics.

This remains a subset port. It does not include upstream immutable timeline/rewind, file-format compatibility, procedural scarf flutter, endpoint extension flags. Grip/Ice/Scenery are editor material extensions. Extreme speeds can still tunnel past thin terrain when they cross beyond the current spatial-query cell. The track limit is 3,000 segments; this limit is a guard against unbounded editing, not a performance guarantee. Undo snapshots and the saved slot increase project size. Drawing, menus and gameplay work with a pointer or touch; the desktop mode also supplies keyboard controls.

The previous demo is retained at `artifacts/demo-v1.sb3`.

Default-course check: `python tools/verify-contact-physics.py` verifies the physical launch lip, lower catch runway and short reverse-boost strip. It checks seated limb posture, sustained clearance of the body colliders, physical return and completion. `tools/course.py` supplies both the default track and Demo, including the matching start and goal flags.

Confirmation regression check: `node tools/verify-confirmation.mjs` exercises guarded Track/Edit actions, cancellation, keyboard confirmation, modal input blocking and paused/running simulation behavior.

Connected toolbar check: `node tools/verify-connected.mjs` tests the shared mode selector, relocated Run/Pause, Retry and Step targets, and the mode-change confirmation. `dist/ui-controls.json` records their current centers for test automation.

The older `verify-course`, `verify-smooth`, `verify-ragdoll`, numerical-equivalence and pose-transition scripts describe archived course and physics versions. `tools/ragdoll.py` now defines only the initial articulated anatomy; `tools/contact_rider.py` emits the continuous solver.

Scratch compatibility: mouse booleans use explicit comparisons. Scalar variables placed directly in boolean sockets can become dangling block references after Scratch GUI saves the project. `node tools/verify-scratch-online.mjs` checks the published project in the official Scratch runtime, including export/import, fullscreen and playback.

Acceleration regression: `node tools/verify-acceleration.mjs` checks drawing, native LR1 round trips, forward/reverse boosts and 30-frame numerical agreement with the lr-core equations.




Timeline verification: `node tools/verify-timeline.mjs` compares every cached demo frame in the delivered Scratch project with the numerical solver. It also checks mouse and touch scrubbing, edits to the start and goal, Undo, playback and crashes.
