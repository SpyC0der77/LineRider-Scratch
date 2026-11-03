# Version archive

Every recovered `.sb3` is preserved unchanged, with its exact executable Scratch source, assets, SHA-256 checksum and a rebuild script. Historical test/save variants are included as separate snapshots. Earlier complete Python generators were not retained; those gaps are stated in each version. Current and future builds include the full Python generator.

| Version | Original build | Preserved code |
| --- | --- | --- |
| [v000-original-demo](v000-original-demo/README.md) | artifacts\demo-v1.sb3 | Native + Python |
| [v001-blank-baseline](v001-blank-baseline/README.md) | artifacts\before.sb3 | Native + Python |
| [v002-editor-buttons](v002-editor-buttons/README.md) | artifacts\editor-buttons.sb3 | Exact native Scratch code |
| [v003-saved-slot-fixture](v003-saved-slot-fixture/README.md) | artifacts\persistence.sb3 | Exact native Scratch code |
| [v004-dropdown-editor](v004-dropdown-editor/README.md) | artifacts\before-step.sb3 | Exact native Scratch code |
| [v005-single-frame-step](v005-single-frame-step/README.md) | artifacts\before-mode-switch.sb3 | Exact native Scratch code |
| [v006-mode-switch](v006-mode-switch/README.md) | artifacts\before-course.sb3 | Exact native Scratch code |
| [v007-normal-course](v007-normal-course/README.md) | artifacts\before-edit-confirmation.sb3 | Exact native Scratch code |
| [v008-edit-confirmation](v008-edit-confirmation/README.md) | artifacts\before-connected-controls.sb3 | Exact native Scratch code |
| [v009-connected-controls](v009-connected-controls/README.md) | artifacts\before-smooth-course.sb3 | Exact native Scratch code |
| [v010-smooth-course](v010-smooth-course/README.md) | artifacts\before-ragdoll.sb3 | Exact native Scratch code |
| [v011-ragdoll](v011-ragdoll/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v012-track-codes](v012-track-codes/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v013-track-codes](v013-track-codes/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v014-track-codes](v014-track-codes/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v015-shared-before-update](v015-shared-before-update/README.md) | artifacts\shared-before-update.sb3 | Exact native Scratch code |
| [v016-mobile-codes-fullscreen](v016-mobile-codes-fullscreen/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v017-mobile-codes-fullscreen](v017-mobile-codes-fullscreen/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v018-mobile-codes-fullscreen](v018-mobile-codes-fullscreen/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v019-mobile-codes-fullscreen](v019-mobile-codes-fullscreen/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v020-shared-before-button-colors](v020-shared-before-button-colors/README.md) | artifacts\shared-before-button-colors.sb3 | Exact native Scratch code |
| [v021-button-color-fix](v021-button-color-fix/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v022-prompt-history](v022-prompt-history/README.md) | dist\Line Rider.sb3 | Native + Python |
| [v023-prompt-history](v023-prompt-history/README.md) | dist\Line Rider.sb3 | Native + Python |

`python tools/build.py` archives each distinct new build automatically. Existing snapshots are never overwritten.
