# Line Rider in Scratch

Open [dist/Line Rider.sb3](dist/Line%20Rider.sb3) in Scratch using **File > Load from your computer**, then click the green flag. The project opens in the track editor. Click **Run** to ride the sample course. The **Edit / Play** switch is one joined control in the upper right. Run/Pause, Retry and Step form a shared toolbar below it, connected to the Play half. The switch selects the mode: Play opens a paused preview, and Edit stops the run and restores your editing camera and zoom. Selecting the active mode again does not reset it. Track, Edit, View and Help are dropdown menus; the second row selects the active tool and material. Use Scratch's fullscreen stage for larger controls.

The opening track and **Track > Demo course** use a launch bowl followed by a sloping catch and runout. The rider leaves the seat at frame 115 when the rising sled loses track support, stays airborne without terrain contact, and begins landing back in the sled at frame 149. A compliant catch absorbs relative motion and lets the arms and legs settle before restoring the normal riding constraints. It keeps the current pose and velocity at first contact; it does not reset body points to the seated pose. Catching requires a prior departure above the seat, a downward crossing near the seat, an intact sled and an active run. Ground impact or a crash screen permanently disables catching until Retry. `tracks/current.json` retains the previous owner's canvas as a backup.

The interface starts in mobile mode, with touch instructions and no keyboard shortcuts. Pressing any key on the stage switches to desktop mode. Typing into the track-code answer box does not switch modes. Mobile erasing repairs one skipped segment only when its connected neighbors were removed less than 350 ms apart during the same drag. It checks the original endpoints and stable segment IDs, so unrelated lines and separate gestures do not bridge. Undo restores the entire erase gesture.

In Play, the expand icon beside the Edit / Play selector opens an uninterrupted view across the full Scratch stage. It hides the toolbars and status bar and expands the drawing bounds. The small corner icon returns without resetting the ride. A paused ride has a touch Play button; after a fall settles, touch Retry or Edit. This is the game's fullscreen stage view; Scratch's own fullscreen control can enlarge the player window.

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

Normal lines use the original point-friction model. Grip lines add damping along the track tangent. Ice disables point friction. Scenery is visible but does not collide. Acceleration adds the original lr-core 0.1 tangent boost on contact; Reverse boost applies it in the opposite direction. Acceleration lines are red and retain their material in saved codes. The renderer clips all terrain and rider strokes to the canvas, including very long offscreen lines.

## Playback

- **Run / Space** starts a run; click again to pause or resume.
- **Step / N**, also available under Edit, advances exactly one physics frame and stays paused. Step remains available for repeated clicks. The first step preserves the editor camera; the status bar shows the frame number and elapsed time. A paused ragdoll can also be stepped frame by frame. Step is disabled during playback and once the fall or run has finished.
- **Retry / R** restarts the run. In the editor it returns to the start view.
- **Edit > Return to editor / E** returns to editing and preserves the camera position from before the run.
- **X** detaches the rider for a crash test.
- Elapsed simulation time, speed, segment count and zoom appear in the status bar.

## Keeping your tracks

**Track > Save track code** creates an `LR1` code that can be kept in a text file or sent to someone else. Double-click the code row, then press Ctrl+A and Ctrl+C. Close the dialog when finished. **Track > Load track code** opens Scratch's answer box for pasting. Submit an empty answer to cancel. Invalid, incomplete, oversized or altered codes show an error and leave the track, flags, saved slot and undo history untouched. Loading a valid code creates one undo step and rebuilds the collision data. Export can be used during Play; it freezes and resumes the same ride. Import from Play uses the existing confirmation before switching to Edit.

Codes retain every segment, its material, the start flag, goal position and goal-enabled setting. Coordinates are rounded to hundredths of a world unit, at most 0.005 units per coordinate. Connected endpoints stay connected. The code omits redundant line starts and computed normals/bounds, uses signed endpoint deltas and variable-length base-32 numbers, and ends with a checksum. The preserved 128-line track uses 823 characters, about 89% less than its segment-array JSON. The original 140-line Demo course uses 898 characters. The limit remains 3,000 segments. Spaces, tabs, line breaks, hyphens and lowercase letters are accepted on load. [The format specification](docs/track-code-format.md) describes the exact layout.

**Track > Save slot** copies the current track and flags into one saved slot inside the project. **Track > Load saved slot** restores that slot; Undo can reverse a load. The slot survives the green flag and saving/reopening the `.sb3`.

The saved slot is not a filesystem download. Use a track code to keep individual tracks, or Scratch's **File > Save to your computer** to keep the entire editor and its saved slot. Neither method requires a cloud service or account. Closing Scratch without saving the project or copying a code can lose changes.

New and Demo preserve the saved slot. The green flag resets the editor and run state, while keeping the current track, flags and saved slot. It clears the undo/redo history.

## Build and verification

The native project is divided into **Game controller**, **Physics**, **Track editor**, **Menus**, **Track codes**, and **Renderer**, plus the existing **Prompt history** sprite. Each sprite has a comment explaining its responsibilities and a list of incoming requests. The largest sprite has about 2,250 blocks. [The sprite guide](docs/sprite-architecture.md) explains the shared state, message boundaries, and build process.

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

Mounted motion keeps the original 17-point lr-core model, Verlet integration, gravity of 0.175 and six constraint/contact passes. Four articulated elbow/knee nodes and a physical head bring the total to 22 points. They follow the original pose until detachment, preserving the original ride and natural unseating. After detachment, eight solver passes enforce mass-weighted limb bones, knee/elbow bend direction, neck limits and selected self-separation constraints. Circle-to-line contacts give the head and limbs thickness; small restitution and tangent friction let the body roll, slide and settle. Track segments remain lines. Retry restores the mounted state and clears contacts. Original Stick, RepelStick, breakable BindStick, orientation-based BindJoint, DirectedChain scarf constraints and direct SolidLine contacts are retained for the mounted solver. A 64-unit spatial grid supplies nearby line candidates in source order. Geometry edits invalidate it; playback rebuilds it once. Camera coordinates do not affect physics.

This remains a subset port. It does not include upstream immutable timeline/rewind, file-format compatibility, procedural scarf flutter, endpoint extension flags. Grip/Ice/Scenery are editor material extensions. Extreme speeds can tunnel through the original ten-unit line contact bound. The track limit is 3,000 segments; this limit is a guard against unbounded editing, not a performance guarantee. Undo snapshots and the saved slot increase project size. Drawing, menus and gameplay work with a pointer or touch; the desktop mode also supplies keyboard controls.

The previous demo is retained at `artifacts/demo-v1.sb3`.

Default-course check: `node tools/verify-course.mjs` verifies all-normal materials, natural loss of balance at frame 96, visible separation, crash stopping, Retry and Demo restoration. `tools/course.py` is the shared course data source.

Confirmation regression check: `node tools/verify-confirmation.mjs` exercises guarded Track/Edit actions, cancellation, keyboard confirmation, modal input blocking and paused/running simulation behavior.

Connected toolbar check: `node tools/verify-connected.mjs` tests the shared mode selector, relocated Run/Pause, Retry and Step targets, and the mode-change confirmation. `dist/ui-controls.json` records their current centers for test automation.

Smooth-course and connector check: `node tools/verify-smooth.mjs` verifies a continuous all-normal track with no blocking segments, the rendered parent/bus/three connector branches, natural rider separation and an intact sled.

Ragdoll check: `node tools/verify-ragdoll.mjs` compares the mounted motion with the numerical source, checks natural detachment, bone stability, finite motion, settling, pause/resume/step and retry. `tools/ragdoll.py` defines the post-detachment body and contact solver. The default fall settles naturally rather than reaching the duration cap.

Scratch compatibility: mouse booleans use explicit comparisons. Scalar variables placed directly in boolean sockets can become dangling block references after Scratch GUI saves the project. `node tools/verify-scratch-online.mjs` checks the published project in the official Scratch runtime, including export/import, fullscreen and playback.

Acceleration regression: `node tools/verify-acceleration.mjs` checks drawing, native LR1 round trips, forward/reverse boosts and 30-frame numerical agreement with the lr-core equations.

Launch-and-catch check: `node tools/check-reseat.mjs` runs the delivered course in the Scratch VM and requires a contact-free flight, no crash screen, remounting and a seated finish. It also verifies that neither an active crash nor a completed crash can remount.

Soft-landing check: `node tools/verify-landing.mjs` verifies a seated finish, a multi-frame settling phase and bounded body motion relative to the sled. Matching before/after captures and per-frame positions are saved in `artifacts/landing-*`. `node tools/check-reseat.mjs --terminal-only` checks that crashes before contact or during settling remain terminal until Retry.
