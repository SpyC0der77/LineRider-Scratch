# Extra rider QA

Tested the delivered `dist/Line Rider.sb3` without changing game code, physics constants, or course data.

SHA-256: `14a6639e6b81830a4c92edef3627041394cb43982d1342fb9106f57e77fd4ac1`

## Anomalies found

1. **The hands release the rope during the approach.** Both grip forces become zero at frame 18, well before the jump. At frame 60 the hands are 9.11 and 9.70 world units from the loose rope end, outside the 3-unit grip range. They remain posed forward while the rope hangs below them. A brief grip returns at frames 136-137, then releases again. See `hands-before-launch.png` and the normal-speed recording.
2. **Leg recovery still has a visible pop and temporary bone compression.** At frame 171 a foot moves 3.50 units relative to the hip in the sled frame, about 17.5 pixels at the recorded zoom. The left lower-leg segment contracts from its 3.427-unit rest length to 2.700 units, a 21.2% error. The torso also compresses by 19.5% during landing at frame 136. Both feet reach their intended forward range and stay there from frame 190 onward. See slow-motion playback at the frame counter near 171.
3. **The demo has little margin for start changes.** The unchanged run is deterministic, but 9 of 10 numerical perturbation trials failed to complete. These changed spawn X/Y by +/-0.01 or +/-0.1 units, or initial horizontal speed by +/-0.001. This is a robustness issue with the tuned stunt, not evidence of random behavior. The perturbation trials ran in the numerical version of the same generated constraints; native equivalence was verified through all 232 frames of the unchanged demo.

## Checks that passed

- Three uninterrupted runs of the delivered Scratch project finished at frame 232, with identical final particle positions. Recorded normal playback advanced at 29.93 simulation frames per second.
- Two additional numerical repeats reproduced every recorded position exactly.
- A fresh native frame-by-frame run matched all reference particle positions within 1e-7 through all 232 frames.
- Pausing near the jump froze all current and previous particle positions. Eighteen alternating mouse/keyboard steps, one further step after changing the camera/zoom, and resume all preserved the same trajectory.
- Entering fullscreen while airborne, stepping ten frames, exiting and resuming preserved the trajectory.
- Triggering a real X crash at frame 120 remained terminal through the rest of the fall, stopped at frame 301, ignored N afterward, and stayed stopped during an idle wait. Explicit Retry then completed the demo normally.
- The finish screen stayed stopped during an idle wait. No browser page errors were recorded.
- All 7 native test cases passed. All particle coordinates stayed finite in the motion audit.

## Recordings

- [Normal speed, complete delivered run](normal-playback.mp4), recorded directly from the native Scratch canvas at wall-clock speed.
- [Quarter speed, launch through recovery](slow-motion.mp4), fresh native simulation frames 105-210, shown at 7.5 simulation frames per second with no interpolated poses.
- [Pause, step and resume](pause-step-resume.mp4).
- [Crash and terminal-screen check](terminal-crash.mp4).
- GIF copies: [normal](normal-playback.gif), [quarter speed](slow-motion.gif).

## Reproduce

```powershell
python tools/audit-rider-motion.py
node tools/verify-rider-extra.mjs
```

Raw measurements are in `motion-audit.json`, `baseline-particles.json`, `native-motion.json` and `native-tests.json`. The original WebM recordings are retained alongside the MP4 copies. No development server was started.
