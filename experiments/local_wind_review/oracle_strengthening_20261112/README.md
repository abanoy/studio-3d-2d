# GPU oracle strengthening before first graphical run

This folder retains the exact three old harness files and their byte hashes in
`before.json`. `review.patch` is informational; current full source is in the
prototype's `Studio/tests` tree, with exact hashes in `strengthening.json`.

The read-only review found three test gaps: an empty product-owned hidden list
could pass vacuously; excluded pose expectations reused the product baseline
method; and the after-close motion check accepted either original simulation
moving when the plan required both. The stronger checks independently inventory
the nonempty owned mesh set, verify the known nonzero procedural recorded skirt
pose through the ordinary authored sampler and compare excluded channels exactly,
and require both original simulations to remain running and move independently.
The original assertions and numeric bounds remain. The post-close motion control
adds velocity only to the existing bodies; it never restarts or unfreezes them.

All nine runtime files retain their exact hash, byte size and modification time.
Four approved Godot headless `--check-only` parses pass at
`../gpu-preparation/1794542894612507700/verification.json`. The full prototype and
native input identities stayed unchanged during parsing; root functional files
were unchanged. No GPU smoke body, actual rendered motion, PNG export, Record,
navigation or teardown test ran. These are stronger proposed oracles, not a
runtime fix or a graphical pass.
