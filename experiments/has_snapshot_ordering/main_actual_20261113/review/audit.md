# HAS snapshot ordering review

Read-only review found no clear source/API blocker in the two recorded candidate hashes. No main/Git files were edited and no runtime, Godot, graphics or packer was launched by this reviewer.

The capture remains on the main thread and detaches live images/metadata before process creation. The new prepare/launch split holds one captured project, consumes it once, and starts its filesystem Thread only after a positive packer PID. The old start API still performs both operations. finish and exit release pending capture references; started workers retain the existing join/cancel path.

If Thread.start fails after child creation, the candidate records its error and cancellation while retaining pid/exporting/progress state. Python pack waits for snapshot readiness and checks cancellation before touching the target. The ordinary poll then closes progress, clears pid/exporting and emits one false completion without clearing dirty or adopting a successful save identity. Root's real-packer test must verify those endpoints and absence of a surviving child; the producer's 32 checks use inert persistence and do not substitute for app/Storage/packer evidence.

This is ordering hardening, not a proven explanation of the original Windows launch failure. Recovery writer/preview filesystem threads can still overlap launch, and the original GetLastError is unknown. The unchanged focused pass and unreproduced churn probe remain separate results. The patch retains the existing PID-based process lifecycle; it does not add a native retained-handle ownership guarantee.

Exact source hashes and scoped observations are in audit.json. The frozen producer publication packet was not modified.
