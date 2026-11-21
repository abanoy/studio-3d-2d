# Root execution after successful Full closure only

First run the separate synthetic policy checks if desired:

```powershell
& '<approved Python 3.13>' -I -B output/source-miku-contact-c315-1103-successor-prep-20261121/test_source1103_contracts.py
```

These60 controls are authored and unrun. They do not read owner inputs or qualify
a Full. Root must inspect the completed Full and independently provide the exact
SHA256 pins below; no future completion/report hash is invented in this packet.

```powershell
& '<approved Python 3.13>' -I -B output/source-miku-contact-c315-1103-successor-prep-20261121/run_miku_contact_qualification.py `
  --self-sha256 '<exact driver SHA256 from SOURCE_PINS.json>' `
  --expected-head c31576d0c1d84030d51ec886f2f3976a60a70c7b `
  --private-manifest '<unchanged local sealed private Miku manifest>' `
  --full-folder 'C:/a/Programming/cloudflare/has-import-off-full-20261121-c31576d/output/windows-reference-body-<actual-run>' `
  --full-completion-sha256 '<actual successful completion SHA256>' `
  --full-source-sha256 '<actual identical before/after source SHA256>' `
  --full-report-sha256 '<actual fresh verification SHA256>' `
  --full-outer-folder 'C:/a/Programming/cloudflare/has-import-off-full-20261121-c31576d/output/root-full-launch-<actual-run>' `
  --full-outer-launch-sha256 '<actual isolated launch SHA256>' `
  --full-outer-completion-sha256 '<actual successful reaped outer completion SHA256>' `
  --ticks 480 --root-exclusive-lane-confirmed
```

Run only after Root has the exclusive native lane and successful actual Full182
proof for this exact source. An already running Full, the old failed435 Full, a
scoped pass or a synthetic admission fixture is insufficient. Every gate occurs
before the first job. The existing six tool pins, unchanged private manifest and
exact admitted source identities must still match. Do not overwrite any old
stage or lock to force a retry. Failed closure or preservation retains a FAIL.

The ArrayMesh13 stage is the first actual engine conformance measurement after
the171 pure checks and before contact attempts. Failure stops there and remains
preserved; it must not be described as full-mesh, GPU shader or contact proof.
