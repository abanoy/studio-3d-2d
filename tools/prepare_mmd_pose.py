"""Own a hidden local converter and publish its result after it terminates."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import hashlib


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

request_path=Path(sys.argv[1])
request=json.loads(request_path.read_bytes())
result_path=Path(request["result"])
try:
    if Path(request["cancel"]).exists():raise RuntimeError("Pose import cancelled.")
    motion=request.get("kind")=="motion"
    native_key="motion" if motion else "pose"
    original={key:sha256(request[key]) for key in ("source",native_key)}
    command=[request["blender"],"--background","--factory-startup","--disable-autoexec",
             "--offline-mode","--python-exit-code","1","--python",
             str(Path(__file__).with_name("blender_mmd_motion.py" if motion else "blender_mmd_pose.py")),"--",str(request_path)]
    with result_path.with_suffix(".log").open("w",encoding="utf-8") as log:
        process=subprocess.Popen(command,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0)
        started=time.monotonic()
        try:
            while process.poll() is None:
                if Path(request["cancel"]).exists():raise RuntimeError("Pose import cancelled.")
                if time.monotonic()-started>60:raise RuntimeError("Pose conversion exceeded its time limit.")
                time.sleep(.05)
            if process.returncode:
                lines=result_path.with_suffix(".log").read_text(encoding="utf-8",errors="replace").splitlines()
                detail=next((line.partition(":")[2].strip() for line in reversed(lines) if line.startswith(("ValueError:","RuntimeError:"))),"Details: "+str(result_path.with_suffix(".log")))
                raise RuntimeError(("Motion" if motion else "Pose")+" preparation failed. "+detail[:500])
            if Path(request["cancel"]).exists():raise RuntimeError("Pose import cancelled.")
            if any(sha256(request[key])!=value for key,value in original.items()):
                raise RuntimeError("The source model or pose changed during preparation. Import again.")
            converted=json.loads(Path(request["output"]).read_bytes())
            if converted.get("model_sha256")!=original["source"] or converted.get("source_sha256" if motion else "pose_sha256")!=original[native_key]:
                raise RuntimeError("The converted pose does not match the selected input files.")
            result={"ok":True,"converted":converted}
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
except (OSError,ValueError,RuntimeError) as error:
    result={"ok":False,"error":str(error)}
temporary=result_path.with_suffix(".tmp")
temporary.write_text(json.dumps(result),encoding="utf-8")
temporary.replace(result_path)
