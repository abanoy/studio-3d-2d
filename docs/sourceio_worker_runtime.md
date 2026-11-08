# Compatible SourceIO worker runtime

The local image `has-sourceio-worker:local` supplies Blender 5.2.2 LTS,
GLIBC 2.43, Python 3.14 and NumPy 2.4.6. It imports the full Blender bindings
from the unchanged pinned SourceIO package, whose native codec cannot load on
the cloud host's GLIBC 2.41. The host was not upgraded.

The original runtime probe below does not mount owner models. Later standalone
integration tests used this image with the actual production adapter to convert
Ran, Reimu V2 and Chen, then pose/save/reopen/render them in HAS. See the separate
[standalone receipt](benchmarks/standalone_source_samples_2026-11-07.json).
Supplied model files do not require a game installation; validated installed
content is an optional source of dependencies.

The tested cloud adapter is `tools/sourceio_blender_container.py`. Pass its
absolute executable path to `tools/prepare_source.py --blender`, together with the
pinned `--sourceio` folder and your own source/output paths. It mounts only the
selected resource folders and worker code read-only, gives the output its own
writable mount and runs the verified image offline. Windows continues to use its
normal installed Blender executable. This adapter is an optional Linux cloud
runtime, not a replacement for the native format-fidelity acceptance tests.

Build from the existing checkout using the managed local Docker daemon:

```sh
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
  -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
  docker --host=unix:///var/run/docker.sock build \
  -f tools/docker/sourceio_worker.Dockerfile \
  -t has-sourceio-worker:local tools/docker
```

Preserve Docker's configured reachable proxy defaults. Passing the outer shell's
`proxy` hostname as a build argument failed inside the build. Never use host
networking or disable TLS verification. The Debian base digest is pinned;
resolved package versions and the tested image ID are in the receipt. The apt
repository is rolling, so rebuilding later can resolve different packages.

The image includes `python3-cattr` and `python3-requests`, which Blender's
extension manager imports even in offline mode. It contains no SourceIO source,
owner artwork, game installation, credentials or project assets.

The tested image is
`sha256:920ce476fe22608deb971d51c152ee67cc4072c0e2781ce5c1c164ece0d0966e`.
The probe uses the unchanged SourceIO directory as a read-only mount and exports
an original triangle with a skin, animated morph and material:

```sh
mkdir -p /workspace/has-handoff-audit/sourceio-worker-new

env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
  -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
  docker --host=unix:///var/run/docker.sock run --rm \
  --network none --read-only --user 1000:1000 \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 4g --cpus 2 --tmpfs /tmp:size=268435456 \
  -e BLENDER_USER_CONFIG=/tmp/blender-config \
  -e BLENDER_USER_EXTENSIONS=/tmp/blender-extensions \
  -e XDG_CONFIG_HOME=/tmp/xdg-config \
  -e XDG_CACHE_HOME=/tmp/xdg-cache \
  -e XDG_DATA_HOME=/tmp/xdg-data \
  --mount type=bind,src=/workspace/studio-3d-2d/tests/sourceio_worker_probe.py,dst=/probe.py,readonly \
  --mount type=bind,src=/workspace/.studio-tools/sourceio-source/SourceIO-fe24260b97ac03b899d9b5d4f0fd7b34772f3647,dst=/sourceio,readonly \
  --mount type=bind,src=/workspace/has-handoff-audit/sourceio-worker-new,dst=/evidence \
  sha256:920ce476fe22608deb971d51c152ee67cc4072c0e2781ce5c1c164ece0d0966e \
  blender -noaudio --background --factory-startup --disable-autoexec \
  --offline-mode --python-exit-code 1 --python /probe.py -- \
  --sourceio /sourceio --output /evidence
```

The final probe exited successfully without Python tracebacks. Debian's optional
Draco and MeshOptimizer compression libraries are absent and produce notices;
uncompressed GLB export succeeded. Eight independent accessor checks confirmed
the original geometry, bone identity, normalized weights, morph displacement,
24 animation samples and material. All 574 extracted SourceIO files matched the
checksum-bound archive. No supplied SFM model was converted by this probe.

See [the runtime receipt](benchmarks/sourceio_worker_runtime_2026-11-07.json).
