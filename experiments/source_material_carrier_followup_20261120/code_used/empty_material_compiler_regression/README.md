# Existing compiler regressions on the empty-material profile

Root-only execution preparation. All six Python files are byte-exact copies from the frozen empty-material profile and prior compiler-context preparation. The existing 13 test methods and all assertions are unchanged. No tests, module, native input or application is executed by this copying step.

Root should bind these six sources plus every pinned primary source read by the unchanged tests, execute only test_export_hook_compiler_context.py with bytecode writes disabled, then prove hashes, sizes and nsmtimes unchanged. This does not add a new test or admission policy. The compiler fixture reads/compiles pinned source; it does not import Blender or SourceIO.
