#!/bin/bash
# HYBRID_PYTHON stand-in: ignores the Windows-only script path ($1), reports PID liveness via /proc.
shift; out=""; for p in "$@"; do [ -d /proc/$p ] && s=alive || s=exited; out="$out${out:+,}\"$p\":\"$s\""; done
echo "{\"format\":\"studio_process_liveness_1\",\"owners\":{$out},\"created_100ns\":{}}"
