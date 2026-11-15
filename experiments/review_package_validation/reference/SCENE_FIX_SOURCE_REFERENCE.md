# CPU checker source reference

`verify_cpu.py` preserves the 22 oracles from the two original inline CPU probes
in one reproducible script. It creates a fresh evidence directory on every run
and does not overwrite the original failed or successful replay evidence.

Run from the repository:

```powershell
python output/owner-review-validation/scene-fix-cpu-1794541869074561300/verify_cpu.py
```

Prerequisites are the retained c678 review Studio/source-snapshot proof and the
first failed six-project replay at
`output/owner-review-validation/replay-1794541459557567800`. The last check confirms
retention of those six old results; it is a local historical-evidence check, not
a portable product requirement. The guide/checker paths derive from this checkout.

Engine actions are explicit: version probes; `--headless --check-only` to parse
the Node harness; and a headless resource-loader script that loads the generated
external scene as a `PackedScene` **without instantiating it**. The resource load
does not use `--check-only`; its small script executes only the load/type check
and quits. Neither action instantiates Studio or launches graphical replay.

The original inline calls passed all 22 checks. This consolidated reference was
AST-parsed after saving and was **not rerun**. The six actual graphical replays
subsequently passed separately at
`output/owner-review-validation/replay-1794542007734603300`; their proof must not
be conflated with this CPU-only audit.

Saved reference: 7,716 bytes, SHA256
`a4d981825917d6db335a63fa269a2efe05f24b38a63980a771bcf4089a6381d0`.
No application source, built snapshot or final review files were changed while
saving this output-only reference.

Root then ran the consolidated source from its published reference location:
`python -B experiments/review_package_validation/reference/verify_scene_fix_cpu.py`.
All22checks pass,1360snapshot source files unchanged; Node parse and resource
load exit0, no GPU. Evidence:
`output/owner-review-validation/scene-fix-cpu-replay-1794542482918510700`.
The original above remains the earlier saving-time statement.
