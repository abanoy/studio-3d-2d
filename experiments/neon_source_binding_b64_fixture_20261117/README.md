# Authored bone-binding fixture newline correction

The proposed change adds carriage-return removal to the existing newline removal
on the authored GOLDEN_GLB decoding expression. Reversing that single expression
reproduces the original CRLF source byte-for-byte. All319 physical CRLF lines,
the literal payload, constants,79binding/17helper predicates and wrapper thresholds
are unchanged. No product source changes.

The main52 fixture and root-supplied immutable375 Git blob are exact27810-byte LF
sources (SHA b7d7ade3). Candidate375 working source is28129-byte CRLF source, equal
after CRLF-to-LF comparison. The embedded literal contains103 line breaks. The
old expression removes LF while leaving103 CR bytes in the CRLF literal.
The retained closed ordered engine log records the original b64_decode failure
at that expression and subsequent invalid fixture loads.

Ten independent CPU methods pass. LF/CRLF/CR/mixed literal variants produce the
same9360 authored bytes, SHA39637fa34e53c81708329ab963659e8100a285a92e25a22a92ab5e708c0154c1.
The malformed-chunk control remains9364 bytes with its existing95e0c878 hash.
Hardcoded independent identities, container header/chunk extents, changed-payload
negative and exact source inverse are checked. Decoded bytes stay in RAM.
Strict Python base64 checks corroborate the source mechanism; they do not replace
Godot parse/execution, which remains root-owned and unrun by this packet.
Bare-CR tests concern literal normalization, not a claim that Godot parses an
entire bare-CR source file.

A source-pattern scan found five Godot raw-decode sites across the tests. This is
the sole matching embedded multiline-constant/newline-removal construct; the four
other Godot sites consume serialized expected.audio metadata. The scan is bounded
to those source constructs and is not a general proof against every possible
line-ending issue or indirect dataflow. No other test is changed.

An independent source peer verified the exact inverse and raw line counts and
separately ran all10 CPU methods successfully. It found no source blocker.
No native artist file, image, media, model output, engine, CIM or Git operation
was used by this preparation/tests; root supplied the immutable Git blob.
The fixture, helper and wrapper originals and ordered failure log are retained.
No actual full-suite or native-fidelity success is claimed.
