# Original baseline contact-solver phase profile

This is a diagnostic observation, not an optimization or production adoption. The original0bea5b26 baseline is unchanged. A separate9951f12e copy adds coarse phase clocks/bookkeeping only; reversing12 exact text patches recovers the original byte-for-byte. No geometry, numeric arithmetic/order, row/driver selection, iteration/correction budget or acceptance target changes. There are no clocks per vertex or collision pair; the accepted-driver update boundary is measured once per correction.

Native15 passes with720 SAME-input calls, exact complete pose/FK dictionaries and varbytes, nine non-timing metrics and unchanged raw input on every tick. Only the original solver drives the next tick; call order alternates. The original12 native settling/preservation assertions remain. The new timing program is not a cache candidate, so cache38 qualification is not applicable.

Within the INSTRUMENTED baseline's six accounted phases, full-row scans use77.101% (56.352ms/call), corrected slot/row updates10.140% (7.411ms), inputFK/skin points6.911% (5.051ms), driver search/rotation3.245% (2.372ms), capsule builds2.564% (1.874ms), validation/origins0.037% (0.027ms). Denominator is the sum of those six phase totals, not whole simulation time. Pair counts were not instrumented.

The separately timed unmodified baseline in THIS paired run averages72.399ms; the instrumented copy73.220ms. Observation overhead and scheduler/load apply. These absolute times are not directly comparable to prior45ms runs, nor do they establish real-time performance or viewportFPS. The whole comparison tick includes both solvers and fullFK comparisons. This identifies repeated full-row scans as the first measured cost center without claiming a faster algorithm.

Quality is unchanged:123 final remaining contact pairs,130 maximum, worst recorded gap−0.04447885m and710 iteration-limit hits; Off vertex error0. Full hair, collision-free behavior and appearance remain open. The original private independently guided five-section fixture/layout and existing pinned source/runtime are required to reproduce; their GLBs, native weights/poses/specs and artwork are not included.

Exact executed original/instrumented/test/runner logic is archived as .txt for source recovery. These files contain generic math/code, not measured private geometry arrays. Actual safe15 receipt, phase breakdown, exact reverse proof and headless lifecycle/source/input/runtime/environment preservation hashes are retained. Job+desktop close, retained launcher is reaped/handleclosed, and no foreground or desktop switch occurs. Headless closure does not claim a visible window.

No engine was launched by this curation, no production source/tests/tools/Git or blocked cleanup path was changed, and no new native run is authorized by this archive. Hair owns the separate sparse-typed prototype/CPU slot; all previous dense/sparse adverse observations stay distinct.
