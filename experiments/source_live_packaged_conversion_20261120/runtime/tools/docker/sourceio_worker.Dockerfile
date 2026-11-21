# Compatible local worker runtime; owner art and SourceIO remain read-only mounts.
FROM debian:unstable-slim@sha256:0616b6687a2b155010c25f9019d2e87461bed2b19b2733ca079b4700a2513949
RUN apt-get update && apt-get install -y --no-install-recommends blender python3 python3-numpy libstdc++6 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends python3-cattr python3-requests && rm -rf /var/lib/apt/lists/*
ENV NO_BPY=1 PYTHONDONTWRITEBYTECODE=1
