"""Run frozen source in fresh folders, never copying developer caches or imports.

Uses the last accepted full-review native Model7/8 scenes as data, then performs
new cold Open/edit/save/render checks. Also runs the real beginner course from
included original assets. No normal-install replacement or executable bundling.
"""
from pathlib import Path
import array
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    review = read(ROOT / "output/full-current-review.json")
    assert review["full_verifier_exit"] == 0 and review["functional_unchanged"]
    frozen = read(Path(review["folder"]) / "functional-inputs.json")
    current = {name:sha(ROOT / name) for name in frozen}
    prior_changes = {name:{"review_sha256":digest,"current_sha256":current[name]}
                     for name,digest in frozen.items() if current[name] != digest}
    # This checker is deliberately exercised under a Unicode path for the first
    # time. Its explicit ffprobe UTF-8 decoding is the only existing-file change.
    assert {Path(name).as_posix() for name in prior_changes} <= {"tests/verify_first_movie.py"}, prior_changes
    folder = ROOT / "output/portable-candidate" / str(time.time_ns())
    folder.mkdir(parents=True)
    # Git is only used for its explicit source inventory. Include these new tests.
    workspace = ROOT.parent
    listed = subprocess.check_output(
        ["git", "ls-files", "-z", "--", ROOT.name], cwd=workspace
    ).decode("utf-8").split("\0")
    source = {Path(name).relative_to(ROOT.name).as_posix(): (workspace / name).read_bytes()
              for name in listed if name}
    for name in ["tests/portable_candidate.gd", "tests/verify_portable_candidate.py"]:
        source[name] = (ROOT / name).read_bytes()
    assert not any(Path(name).parts[0] in {"output", ".godot", ".git"} for name in source)
    hashes = {name: hashlib.sha256(blob).hexdigest() for name, blob in source.items()}
    (folder / "source-inputs.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    receipts = []
    commands = []

    def clone(label):
        target = folder / (label + " Studio — тест")
        assert not target.exists()
        for name, blob in source.items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        assert not (target / "output").exists() and not (target / ".godot").exists()
        return target

    def command_at(candidate, script, extra):
        spec = importlib.util.spec_from_file_location("candidate_run", candidate / "run.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.command(script, extra=["--", *map(str, extra)])

    def execute(candidate, args, label, timeout=310):
        before = set((candidate / "output/private-desktop").glob("*.json"))
        started = time.time_ns()
        p = subprocess.run(args, cwd=candidate, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        log = p.stdout + p.stderr
        (folder / (label + ".log")).write_text(log, encoding="utf-8")
        row = {"label":label, "args":args, "exit":p.returncode, "started_ns":started}
        commands.append(row)
        (folder / "commands.json").write_text(json.dumps(commands, indent=2), encoding="utf-8")
        fresh = set((candidate / "output/private-desktop").glob("*.json")) - before
        for path in sorted(fresh):
            receipt = read(path)
            receipts.append({"path":str(path), "sha256":sha(path)})
            assert (receipt["exit"] == 0 and receipt["child_desktop_confirmed"]
                    and not receipt["foreground_child_observed"]
                    and receipt["job_closed"] and receipt["desktop_closed"]), receipt
        assert p.returncode == 0 and fresh, log
        assert not any(text in log for text in ["ERROR:", "FAIL ", "ObjectDB instances leaked"]), log
        assert all(sha(candidate / name) == digest for name,digest in hashes.items())
        return log

    course = clone("Beginner")
    execute(course, [sys.executable, "tests/verify_first_movie.py"], "beginner")
    course_result = read(course / "output/first-movie-verification.json")
    contact = read(ROOT / "output/contact-persistence-verification.json")
    motion = read(ROOT / "output/motion-animation-app-verification.json")
    cases = [
        ("model7", Path(contact["writer"]["packed"]),
         Path(contact["writer"]["folder"]) / "expected.json",
         Path(contact["writer"]["folder"]) / "reference.png", 12),
        ("model8", Path(motion["project"]),
         Path(motion["folder"]) / "result.json",
         Path(motion["folder"]) / "saved-frame.png", 10),
    ]
    reports = []
    input_hashes = {}
    for kind, project, expected, reference, frame in cases:
        inputs = folder / "isolated-inputs" / kind
        inputs.mkdir(parents=True)
        # Only these three declared files transfer, not any old assets/cache/history.
        for path, name in [(project,"Portable native.has"), (expected,"expected.json"),
                           (reference,"reference.png")]:
            (inputs / name).write_bytes(path.read_bytes())
            input_hashes[str(path)] = sha(path)
        config = {"kind":kind, "project":str(inputs / "Portable native.has"),
                  "expected":str(inputs / "expected.json"),
                  "reference":str(inputs / "reference.png"), "frame":frame}
        if kind == "model8":
            tone = Path(contact["writer"]["folder"]) / "tone.wav"
            (inputs / "Sound clip.wav").write_bytes(tone.read_bytes())
            input_hashes[str(tone)] = sha(tone)
            config["audio"] = str(inputs / "Sound clip.wav")
        config_path = inputs / "case.json"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        candidate = clone(kind)
        # Move this freshly created source folder before its first launch.
        relocated = folder / ("Moved " + candidate.name)
        assert candidate.resolve().is_relative_to(folder.resolve()) and relocated.resolve().is_relative_to(folder.resolve())
        candidate.rename(relocated)
        assert not candidate.exists() and not (relocated / "output").exists()
        log = execute(relocated, command_at(relocated,"tests/portable_candidate.gd",[config_path]), kind)
        assert "PORTABLE_CANDIDATE " in log
        report = read(relocated / "output/portable/result.json")
        assert report["failures"] == 0
        movie = report["movie"]
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", movie
        ], text=True, encoding="utf-8"))
        video = next(s for s in probe["streams"] if s["codec_type"] == "video")
        assert (video["codec_name"],video["width"],video["height"],video["r_frame_rate"],video["nb_read_frames"]) == ("h264",1920,1080,"24/1","48")
        assert abs(float(probe["format"]["duration"])-2) < .001
        assert any(s.get("codec_name") == "aac" for s in probe["streams"])
        pcm = subprocess.check_output(["ffmpeg","-v","error","-i",movie,"-vn","-f","s16le","-ac","1","-ar","48000","-"])
        samples = array.array("h"); samples.frombytes(pcm)
        if sys.byteorder != "little": samples.byteswap()
        onset = next(i for i,value in enumerate(samples) if abs(value)>1000)/48000
        assert abs(onset-1) < .002, onset
        reports.append({**report,"source_copy":str(relocated),"audio_onset_seconds":onset,"video":video})
    assert all(sha(path) == digest for path,digest in input_hashes.items())
    assert all(sha(ROOT / name) == digest for name,digest in current.items())
    assert len(receipts) == 4
    # A clean runnable candidate is kept separately from the instrumented copies.
    candidate = clone("Review candidate")
    result = {"folder":str(folder),"candidate":str(candidate),"source_files":len(source),
              "source_hashes":hashes,"commands":commands,"private_receipts":receipts,
              "beginner":course_result,"native_cases":reports,"original_inputs":input_hashes,
              "functional_unchanged":True,"changes_since_full_review":prior_changes,
              "normal_install_updated":False,"deployed":False}
    (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (ROOT / "output/portable-candidate-verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({key:value for key,value in result.items() if key != "source_hashes"},indent=2))


if __name__ == "__main__":
    main()
