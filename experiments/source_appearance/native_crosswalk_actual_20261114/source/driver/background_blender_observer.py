"""Observation-only Blender entry, then run unchanged frozen native bridge."""
from __future__ import annotations
import os
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).absolute().parent))
import background_route as BG


def main():
    raw_path = os.environ.get("HAS_BACKGROUND_OBSERVER_REQUEST", "")
    raw_sha = os.environ.get("HAS_BACKGROUND_OBSERVER_SHA256", "")
    BG.S.require(raw_path and raw_sha, "Blender observation request is missing")
    request_path = Path(raw_path).absolute()
    case = BG.owned(request_path.parent, BG.TASK)
    BG.S.require(request_path.name == "blender-observer-request.json", "Wrong Blender observation request path")
    request = BG.read_bound(request_path, raw_sha)
    BG.S.require(request.get("format") == "has_background_blender_request_1" and BG.normalized(request["case"]) == BG.normalized(case),
                  "Wrong Blender observation request/case")
    conversion = case / "bundle/conversion-request.json"
    user_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    BG.S.require(len(user_args) == 1 and BG.normalized(user_args[0]) == BG.normalized(conversion)
                  and BG.normalized(request["conversion_request"]) == BG.normalized(conversion)
                  and BG.S.identity(conversion)["sha256"] == request["conversion_request_sha256"], "Blender bridge request/argv changed")
    attestation = BG.observation("blender", request, raw_sha)
    snapshot = attestation["self"]
    BG.S.require(snapshot["desktop"] == request["expected_desktop"]
                  and snapshot["parent_pid"] == request["python_pid"]
                  and snapshot["parent_creation_filetime"] == request["python_creation_filetime"],
                  "Blender did not inherit the attested Python desktop/parent identity")
    BG.S.save(case / "blender-desktop-attestation.json", attestation)
    status, error, import_origins = "exception", None, {}
    try:
        # The unchanged bridge sees its original __file__, the same -- request,
        # original SourceIO, and the same factory/offline/background options.
        with BG.native_import_context("blender", request["sources"]) as observed_imports:
            try:
                runpy.run_path(str(BG.BRIDGE), run_name="__main__")
                status = "ok"
            finally:
                import_origins = observed_imports()
    except BaseException as exception:
        error = {"type": type(exception).__name__, "message": str(exception)}
        raise
    finally:
        BG.S.save(case / "blender-background-completion.json",
                  {"format": "has_background_completion_1", "role": "blender", "nonce": request["nonce"],
                   "status": status, "exception": error, "observed_filetime": BG.Win.system_filetime(),
                   "native_import_origins": import_origins,
                   "conversion_request_sha256": request["conversion_request_sha256"],
                   "sources_after": BG.source_observation(request["sources"])})


if __name__ == "__main__":
    main()
