# Pure normal adapter v2 — test-only fixture correction

The implementation remains byte-exact23576/5d19134b. Root's first20-method run had19passes and1fixtureerror: the measured fake compared the adapter's private dictionary of immutable tuples with the caller's dictionary of mutable lists. The corrected test explicitly verifies a distinct private dict, canonical tuple values, and unchanged original list values. No MappingProxy or new implementation contract is required. All20methods/asserted semantic contracts remain.

Old implementation/test bytes are preserved under bases/ and the complete failed five-file CPU packet under failed_cpu_v1/. No original asset, Blender/SourceIO/native process, GPU, stage or app file is read or modified. The real sealed pure corrector parses only synthetic VVD3/GLB69joint inputs created by the tests. This unadopted candidate still needs actual input/domain/frame/resource qualification and product integration.

Root command: Python313 -B -m unittest -v test_normal_export_adapter, working directory this folder, PYTHONDONTWRITEBYTECODE=1. Four-source readset: this module/test plus experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py17632/37be746c... and vvd_normals.py4184/f3a959cc.... No author tests were run.
