# Exact zero-cone boundary correction

The first322-check packet covered the positive Junko-like angle, but its accepted
parameter domain also included zero. Independent root inspection found104 failures
in1000 unchanged tilted-goal, zero-mass/zero-cone cases. An inverse-cosine rounding
error could report a positive angle while the provisional tip already equalled
the target. Normalizing their zero difference then raised ValueError.

This is a mathematical candidate defect, not an observed HAS/native-client bug.
The original source SHA256 is
`636a81bd7932e790c7a3d512d88ea71e09362e473c4f8bc3f84e4022fbbbce9f`.
The complete pre-correction packet, its initial322 results, closed-form proof,
source/index and code are frozen in `attempt1-original/`. The root's failure is
retained byte-for-byte in `root-zero-cone-failure.json`.

For exactly `angle_limit == 0`, the corrected candidate selects the normalized
goal-forward direction directly, before inverse cosine or normalization of any
provisional tip difference. It retains the fixed-length and radial-velocity
operations. No angular epsilon, parameter narrowing or tolerance relaxation is
used. Positive-cone behavior is unchanged. Undefined positive-cone directions
remain explicit candidate refusals; no general native stability claim is added.

`verify_zero_cone.py` loads the SHA-locked original as well as the correction.
It reproduces the original104/1000 failures and obtains0/1000 with the correction.
The displacement gate remains1e-10; maximum corrected rest displacement is
7.944109290391274e-15. Another500 forced/moving/rotated zero-cone cases match the
analytic permitted ray within3.972054645195637e-15. A provisional tip exactly at
the base is also handled without an undefined direction.

Fresh `*-zero-cone-fix.json` results repeat the322-check positive-angle scenarios,
17,280 strong-input steps,4,363 angular projections and3.132987439350646e-15 unit
covariance maximum. Independent rational first-tick and second-tick damping/world
gravity oracles also pass unchanged. Historical results and the independent root
failure remain distinct. This is still an unintegrated double-precision candidate,
not SDK-executed/native/artist acceptance. The strict mathematical Goal basis
domain is not an automatically qualified float32 engine adapter.
