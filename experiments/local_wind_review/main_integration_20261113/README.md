# Main integration and canvas-first cleanup

The production implementation is in src/ and its normal verifier is
tests/verify_wind_review.py. Retrieve the latest committed source for new work;
do not reapply historical scripts blindly.

The first main matrix passed842checks, then an existing SceneView test freed
the canvas before the application. Wind cleanup attempted a pose redraw against
that disposed canvas. The integration wrapper rejected the engine error despite
all102SceneView assertions printing as passing. A valid-canvas guard fixes that
demonstrated route; three new lifetime checks preserve it in the Wind matrix.
The corrected main matrix passes845checks and94units, followed by eight existing
workflow wrappers. Native assets, frame images and source snapshots stay local.

The comparison source and compact old/fixed result preserve the exact teardown
counterexample. Both sides run the same five assertions; only the old side logs
the invalid pose_lines access. No predicate, error check or native tolerance was
removed. historical_apply_port.py requires its historical2a54base and is retained
as provenance, not a future installation workflow. run_integration_regressions.py
derives wrapper deadlines from the actual canonical source and records unchanged
functional hashes/stamps/HEAD. Neither scoped execution is a full aggregate.

The source-only earlier packets remain under production_port_candidate_20261112
and main_driver_proposal_20261113. Main now includes the canvas correction,
three added checks and updated source pins/counts. Pending helper-before-Apply
and permanent exclusion controls are still separate work.
