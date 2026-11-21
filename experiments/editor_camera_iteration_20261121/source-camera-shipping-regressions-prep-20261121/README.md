# Ordinary camera interaction regression wrappers

SOURCE ONLY, unparsed/unrun. These tests run the current checkout through existing run.command and Windows privateDesktop conventions. They do not require an old Full proof, historical Git snapshot, immutable experimental source catalogue, SourceIO, owner models, or the experimental qualification hosts. Root standalone camera oracle+matrix29+486 passed before this wrapper was authored; that result does not qualify the new wrapper or its canonical registration.

After adopting the exact camera/wire targets, run:

    python -B tests/verify_camera_interactions.py --scope pure
    python -B tests/verify_camera_interactions.py --scope variant --theme classic --scale 100 --workspace simple
    python -B tests/verify_camera_interactions.py --scope all

Pure scope has29wire+26key+12lens planning checks=67. Each variant has34timeline+22lens checks=56. All scope has67+8×56=515. Graphical variants cover Classic/Neon,100/150percent,Simple/Advanced. On Linux graphical standalone usage additionally requires an explicitly provisioned --isolated-display; there is no shared-display fallback. The current canonical Full registration follows its established Windows usage; no existing Linux smoke entry is changed.

The wrapper checks exact result markers/counts/PASS lines, engine and leak errors, controlled-focus-loss scope, timeline screenshot dimensions, immutable source hashes/size/nanosecond identity, and Windows actual private-window/job/desktop closure. It passes per-case APPDATA/LOCALAPPDATA/TEMP/TMP directories on Windows and leaves parent environment and app preferences alone. Graphical jobs use privateDesktop timeouts175/165seconds and4GiB cap with a35-second outer margin. Failed or interrupted calls stop without starting another case. Headless pure tests follow existing run.command semantics and use no display. All output is under a new directory inside output/.

PATCHES.json contains one exact anchor against main59a112a tests/verify.py57338/32a65792. It registers9ordinary result groups after numeric camera: pure once and8variants. The complete patched file is retained for review; removing the one inserted block reconstructs the baseline byte exactly. No old Full action/assertion/group is modified or weakened.

TARGETS.json binds a complete14-target camera+shipping candidate against current1086: camera3modified+7new, two new wire test helpers, wrappernew and verifyregistrationmodified, with the corrected lens fixture replacing its earlier test payload. This yields4replacements/10new and proposed functional1096, before separate UI additions. The shared app.gd payload here contains camera changes only; use the separately proven literal UI+camera composition when applying alongside UI. Never overwrite the UI Settings anchor with the standalone camera whole app.

Original camera26manifest6fa070, wirev2fixturemanifest46af4216, failed camera runs and measured diagnostic remain preserved. The wirev2 experimental-host frozen README had a corrupted example hash; its correct driver pin is25458/282973d27423c95c6926599e3a44a50cdc749da5c5679ceb9ade0e56260e55f0, verified separately in that host CHECK_PLAN/manifest. This wrapper does not depend on that driver.

Required next qualification: source/API peer, actual ordinary wrapper pure/variants, combined UI+camera integration, and Root canonical Full. No parser/engine/GPU/Git/current application write was performed by this author. No completion or owner acceptance percentage changes are implied.
