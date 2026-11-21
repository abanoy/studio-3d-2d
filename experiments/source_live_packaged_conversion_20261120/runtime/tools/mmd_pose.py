"""Read MMD pose data without executing model code or modifying the source."""
import hashlib
import math
import re
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
MAX_CONTROLS = 4096


def read_pose(path):
    path = Path(path)
    with path.open("rb") as stream:
        blob = stream.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES:
        raise ValueError("Pose file exceeds 4 MiB")
    try:
        text = blob.decode("utf-8-sig") if blob.startswith(b"\xef\xbb\xbf") else blob.decode("cp932")
    except UnicodeError as error:
        raise ValueError("Pose names could not be decoded") from error
    lines = [line.split("//", 1)[0].strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    if len(lines) < 3 or lines[0] != "Vocaloid Pose Data file":
        raise ValueError("Expected an MMD pose file")
    if not lines[1].endswith(";") or not re.fullmatch(r"\d+;", lines[2]):
        raise ValueError("Invalid pose header")
    count = int(lines[2][:-1])
    if count > MAX_CONTROLS:
        raise ValueError("Pose has too many bones")
    bones, morphs, ids, names = [], [], set(), set()
    cursor = 3
    while cursor < len(lines):
        header = re.fullmatch(r"(Bone|Morph)(\d+)\{(.+)", lines[cursor])
        if not header:
            raise ValueError("Invalid pose control")
        kind, index, name = header.groups()
        name = name.strip()
        identity = (kind, int(index))
        if not name or len(name) > 512 or identity in ids or (kind, name) in names:
            raise ValueError("Repeated or invalid pose control")
        ids.add(identity)
        names.add((kind, name))
        width = 4 if kind == "Bone" else 3
        if cursor + width > len(lines) or lines[cursor + width - 1] != "}":
            raise ValueError("Incomplete pose control")
        if kind == "Bone":
            position = numbers(lines[cursor + 1], 3)
            rotation = numbers(lines[cursor + 2], 4)
            if not any(rotation):
                rotation = [0., 0., 0., 1.]
            bones.append(dict(name=name, position=position, rotation_xyzw=rotation))
        else:
            morphs.append(dict(name=name, weight=numbers(lines[cursor + 1], 1)[0]))
        if len(bones) + len(morphs) > MAX_CONTROLS:
            raise ValueError("Pose has too many controls")
        cursor += width
    if len(bones) != count:
        raise ValueError("Pose bone count differs from its header")
    return dict(format="studio_mmd_pose_input_1", source_sha256=hashlib.sha256(blob).hexdigest(),
                source_model=lines[1][:-1], bones=bones, morphs=morphs)


def numbers(line, count):
    if not line.endswith(";"):
        raise ValueError("Pose value must end with a semicolon")
    try:
        values = [float(item.strip()) for item in line[:-1].split(",")]
    except ValueError as error:
        raise ValueError("Invalid numeric pose value") from error
    if len(values) != count or not all(math.isfinite(v) and abs(v) <= 1e9 for v in values):
        raise ValueError("Pose value has an invalid size or range")
    return values
def binding_plan(pose, bones):
    """Match declared native names exactly, retaining missing and ambiguous names for review."""
    names = {}
    for bone in bones:
        if not isinstance(bone.get("id"), str) or not isinstance(bone.get("name"), str):
            raise ValueError("Invalid native bone binding")
        names.setdefault(bone["name"], []).append(bone["id"])
    matched, unmatched, ambiguous = [], [], []
    for control in pose["bones"]:
        candidates = names.get(control["name"], [])
        if len(candidates) == 1:
            matched.append(dict(bone_id=candidates[0], control=control.copy()))
        elif candidates:
            ambiguous.append(dict(name=control["name"], candidates=candidates.copy()))
        else:
            unmatched.append(control["name"])
    return dict(source_sha256=pose["source_sha256"], matched=matched,
                unmatched=unmatched, ambiguous=ambiguous, can_apply=bool(matched) and not ambiguous)
