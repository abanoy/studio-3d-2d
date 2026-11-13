"""Legitimate headless converter entry; independently attest before runpy worker."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).absolute().parent))
import background_route as BG


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", required=True,
                        help="This entry actually consumes headless mode; it creates no window")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    options = parser.parse_args(argv)
    request_path = options.request.absolute()
    case = request_path.parent
    BG.owned(case, BG.TASK)
    BG.S.require(request_path.name == "background-request.json", "Wrong bootstrap request path")
    request = BG.read_bound(request_path, options.request_sha256)
    BG.validate_request(request, case)
    python_attestation = BG.observation("python", request, options.request_sha256)
    BG.S.save(case / "python-desktop-attestation.json", python_attestation)
    actual_popen, actual_argv = subprocess.Popen, sys.argv
    calls = []
    exit_code, exception, import_origins = 2, None, {}
    def observed_popen(command, *args, **kwargs):
        BG.S.require(not calls, "More than one worker subprocess requested")
        BG.S.require(not args and not kwargs.get("shell", False) and kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW
                      and BG.normalized(kwargs.get("cwd", "")) == BG.normalized(case / "bundle") and isinstance(kwargs.get("env"), dict),
                      "Worker subprocess flags/cwd/environment differ")
        BG.source_observation(request["sources"])
        changed, environment, observer_sha = BG.instrument_blender(command, request, case, python_attestation,
                                                                  options.request_sha256, kwargs["env"])
        calls.append(True)
        modified = dict(kwargs); modified["env"] = environment
        process = actual_popen(changed, **modified)
        receipt = {"format": "has_background_blender_spawn_1", "nonce": request["nonce"],
                   "python_request_sha256": options.request_sha256,
                   "python_pid": python_attestation["self"]["pid"],
                   "python_creation_filetime": python_attestation["self"]["creation_filetime"],
                   "blender_pid": process.pid, "blender_creation_filetime": BG.Win.process_creation(process.pid),
                   "observer_request_sha256": observer_sha,
                   "conversion_request_sha256": BG.S.identity(case / "bundle/conversion-request.json")["sha256"],
                   "original_command": command, "observed_command": changed,
                   "observed_filetime": BG.Win.system_filetime()}
        BG.S.save(case / "blender-spawn.json", receipt)
        return process
    try:
        subprocess.Popen = observed_popen
        # --headless belongs to this entry and is never passed to the unchanged
        # prepare_source argparse interface. __file__ and its original argv stay exact.
        sys.argv = request["native_command"][3:]
        with BG.native_import_context("python", request["sources"]) as observed_imports:
            try:
                try:
                    runpy.run_path(str(BG.PREPARE), run_name="__main__")
                    exit_code = 0
                except SystemExit as result:
                    BG.S.require(result.code is None or type(result.code) is int, "Noninteger worker SystemExit")
                    exit_code = 0 if result.code is None else result.code
            finally:
                import_origins = observed_imports()
        BG.S.require(len(calls) == 1, "Native worker did not launch exactly one observed Blender command")
    except BaseException as error:
        exception = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        subprocess.Popen, sys.argv = actual_popen, actual_argv
        BG.S.save(case / "python-background-completion.json",
                  {"format": "has_background_completion_1", "role": "python", "nonce": request["nonce"],
                   "worker_exit": exit_code, "intercepted_blender_commands": len(calls), "exception": exception,
                   "native_import_origins": import_origins,
                   "observed_filetime": BG.Win.system_filetime(), "sources_after": BG.source_observation(request["sources"])})
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
