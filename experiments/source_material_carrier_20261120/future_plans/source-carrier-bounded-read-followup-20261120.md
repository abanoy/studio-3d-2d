# Bounded coordinator reads: concrete followup

The frozen V5 driver admits a regular file with before.st_size <= limit, then requests stream.read(limit + 1), with default limit256MiB, even for small sources. Its opened/final/lstat identity, length and SHA guards are separate. Root observed the V3 coordinator PID31708 with user9,531,250 and kernel1,028,750,000 units of100ns,3,412read operations and16,321,831read bytes during admission. This is one observation, not a benchmark or a proven cause of delay; the actual V3 child took7.775seconds.

Inference: oversized read requests may explain Windows coordinator overhead. Plan independently reviewed a narrow successor using before.st_size + 1 as the request, preserving all existing before/opened/after identity, limit, hash and exact-length checks. One extra byte still detects growth; final stamp/length checks retain shrink/rewrite/replace refusals. Zero-byte input requests one byte.

Do not edit frozen V5 or benchmark while Root27540 is active. After it is reaped, a source-only bounded comparison and grow/rewrite/zero-byte/oversize negatives can qualify this change if another coordinator run is needed. No performance improvement has been measured or adopted.
