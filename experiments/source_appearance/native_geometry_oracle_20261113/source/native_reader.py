"""Independent bounded Source1 base-geometry reader: stdlib struct only.

Disk offsets/layouts are documented in review/FORMAT-BOUNDS.md. No converter,
SourceIO, NumPy, Blender or engine modules are imported. VTX scope is explicit
legacy packed VTX7 TRI_LIST; alternative/extended layouts are not guessed.
"""
from __future__ import annotations
import hashlib
import math
import struct


class FormatError(ValueError):
    pass


def require(value, message):
    if not value:
        raise FormatError(message)


class Buffer:
    def __init__(self, raw, label, maximum=16*1024*1024):
        require(isinstance(raw, bytes) and 0 < len(raw) <= maximum, label+": byte budget")
        self.raw, self.label = raw, label

    def span(self, offset, count):
        require(type(offset) is int and type(count) is int and offset >= 0 and count >= 0
                and offset+count <= len(self.raw), self.label+": range outside file")
        return self.raw[offset:offset+count]

    def read(self, fmt, offset):
        return struct.unpack("<"+fmt, self.span(offset, struct.calcsize("<"+fmt)))

    def table(self, base, relative, count, stride, maximum=200000):
        require(type(count) is int and 0 <= count <= maximum and type(relative) is int and relative >= 0,
                self.label+": table count/relative offset")
        start = base+relative
        if count:
            require(relative > 0, self.label+": nonempty table has zero offset")
            self.span(start, count*stride)
        return [start+i*stride for i in range(count)]

    def cstring(self, start, maximum=1024):
        self.span(start, 1)
        end = self.raw.find(b"\0", start, min(len(self.raw), start+maximum))
        require(end >= start, self.label+": unterminated string")
        raw = self.raw[start:end]
        return raw.decode("latin1"), hashlib.sha256(raw).hexdigest()


def mdl(raw):
    b = Buffer(raw, "MDL")
    require(b.span(0, 4) == b"IDST", "MDL: magic")
    version, checksum = b.read("iI", 4)
    require(version == 49, "MDL: only explicitly bounded version49")
    require(b.read("I", 76)[0] == len(raw), "MDL: declared length differs")
    bone_count, bone_offset = b.read("2i", 156)
    bones = []
    for index, at in enumerate(b.table(0, bone_offset, bone_count, 216, 512)):
        relative, parent = b.read("2i", at)
        name, name_hash = b.cstring(at+relative)
        require(name and -1 <= parent < bone_count and parent != index, "MDL: bone identity/parent")
        bones.append({"index": index, "name": name, "name_bytes_sha256": name_hash, "parent": parent})
    require(bones and len({bone["name"] for bone in bones}) == len(bones), "MDL: missing/ambiguous bone names")
    for bone in bones:
        seen, current = set(), bone["index"]
        while current >= 0:
            require(current not in seen, "MDL: parent cycle")
            seen.add(current)
            current = bones[current]["parent"]
    texture_count, texture_offset = b.read("2i", 204)
    materials = []
    for at in b.table(0, texture_offset, texture_count, 64, 4096):
        relative = b.read("i", at)[0]
        name, _ = b.cstring(at+relative)
        require(name, "MDL: empty material identity")
        materials.append(name)
    references, families, skin_offset = b.read("3i", 220)
    require(0 < references <= 4096 and 0 < families <= 256, "MDL: skin bounds")
    b.span(skin_offset, references*families*2)
    skins = [list(b.read(str(references)+"H", skin_offset+2*references*f)) for f in range(families)]
    require(all(0 <= material < len(materials) for row in skins for material in row), "MDL: skin material index")
    group_count, group_offset = b.read("2i", 232)
    groups = []
    for group_index, at in enumerate(b.table(0, group_offset, group_count, 16, 128)):
        name_offset, count, base, model_offset = b.read("4i", at)
        name, _ = b.cstring(at+name_offset)
        require(name and base > 0, "MDL: group name/base")
        models = []
        for model_index, model_at in enumerate(b.table(at, model_offset, count, 148, 128)):
            fixed_name = b.span(model_at, 64)
            require(b"\0" in fixed_name, "MDL: model name termination")
            model_name = fixed_name.split(b"\0", 1)[0].decode("latin1") or "blank"
            mesh_count, mesh_offset, vertex_count, vertex_bytes = b.read("4i", model_at+72)
            require(0 <= vertex_count <= 200000 and vertex_bytes >= 0 and vertex_bytes % 48 == 0,
                    "MDL: model VVD byte origin/count")
            meshes = []
            for mesh_index, mesh_at in enumerate(b.table(model_at, mesh_offset, mesh_count, 116, 4096)):
                column, model_back, count_, start = b.read("4i", mesh_at)
                require(mesh_at+model_back == model_at and 0 <= column < references and 0 <= start <= vertex_count
                        and 0 <= count_ <= vertex_count-start, "MDL: mesh parent/column/vertex range")
                lod_counts = b.read("8i", mesh_at+52)
                require(lod_counts[0] == count_, "MDL: mesh LOD0 count differs")
                meshes.append({"index": mesh_index, "material_column": column, "vertex_start": start,
                               "vertex_count": count_, "lod_vertex_counts": list(lod_counts)})
            require(sum(m["vertex_count"] for m in meshes) == vertex_count, "MDL: model/mesh vertex totals")
            covered = [i for m in meshes for i in range(m["vertex_start"], m["vertex_start"]+m["vertex_count"])]
            require(sorted(covered) == list(range(vertex_count)), "MDL: overlapping/gapped mesh vertex ranges")
            models.append({"index": model_index, "name": model_name, "vertex_count": vertex_count,
                           "vvd_lod0_origin": vertex_bytes//48, "meshes": meshes})
        groups.append({"index": group_index, "name": name, "base": base, "models": models})
    require(groups, "MDL: no bodygroups")
    return {"version": version, "checksum": checksum, "bones": bones, "materials": materials,
            "skin_reference_count": references, "skins": skins, "groups": groups}


def vvd(raw, checksum, bone_count):
    b = Buffer(raw, "VVD")
    require(b.span(0, 4) == b"IDSV", "VVD: magic")
    version, actual_checksum, lod_count = b.read("3I", 4)
    require(version == 4 and checksum == actual_checksum and 1 <= lod_count <= 8, "VVD: version/checksum/LOD count")
    counts = b.read("8I", 16)
    require(0 < counts[0] <= 200000 and all(counts[i] <= counts[i-1] for i in range(1, lod_count)), "VVD: LOD vertex counts")
    fixup_count, fixup_offset, vertex_offset, tangent_offset = b.read("4I", 48)
    require(vertex_offset >= 64, "VVD: vertex table before header")
    b.span(vertex_offset, counts[0]*48)
    if tangent_offset:
        require(tangent_offset >= vertex_offset+counts[0]*48, "VVD: overlapping tangent data")
        b.span(tangent_offset, counts[0]*16)
    rows = []
    for index in range(counts[0]):
        values = b.read("3f3BB3f3f2f", vertex_offset+index*48)
        weights, ids, active = values[:3], values[3:6], values[6]
        position, normal, uv = values[7:10], values[10:13], values[13:15]
        require(all(math.isfinite(x) for x in (*weights, *position, *normal, *uv)), "VVD: nonfinite vertex data")
        require(1 <= active <= 3 and all(0 <= w <= 1 for w in weights) and abs(sum(weights)-1) < 1e-4
                and all(w == 0 for w in weights[active:]) and all(0 <= j < bone_count for j in ids[:active]),
                "VVD: native bone indices/weights")
        named = {}
        for joint, weight in zip(ids[:active], weights[:active]):
            named[joint] = named.get(joint, 0.)+weight
        rows.append({"source_row": index, "position": tuple(position), "normal": tuple(normal), "uv": tuple(uv),
                     "normal_length_squared": sum(x*x for x in normal),
                     "weights": {j: w for j, w in named.items() if w > 0}, "active_weights": active})
    fixups = []
    order = []
    for at in b.table(0, fixup_offset, fixup_count, 12, 200000):
        lod, start, count = b.read("3i", at)
        require(0 <= lod < lod_count and 0 <= start < counts[0] and 0 < count <= counts[0]-start, "VVD: fixup range/LOD")
        fixups.append({"lod": lod, "source_start": start, "count": count})
        order.extend(range(start, start+count))  # At root LOD0, every valid fixup qualifies.
    if not fixups:
        order = list(range(counts[0]))
    require(len(order) == counts[0] and sorted(order) == list(range(counts[0])),
            "VVD: LOD0 fixups must be a complete, nonoverlapping native-row permutation in this oracle")
    return {"version": version, "checksum": checksum, "lod_count": lod_count, "lod_vertex_counts": list(counts),
            "fixups": fixups, "lod0": [dict(rows[source], lod0_row=i) for i, source in enumerate(order)]}


def vtx(raw, mdl_data, vvd_data):
    b = Buffer(raw, "VTX")
    version, cache, max_strip, max_tri, max_vertex, checksum, lod_count, replacement_offset, group_count, group_offset = b.read("IIHH6I", 0)
    require(version == 7 and checksum == mdl_data["checksum"] == vvd_data["checksum"] and max_vertex == 3
            and 1 <= lod_count <= 8 and lod_count == vvd_data["lod_count"] and 1 <= max_strip <= 256,
            "VTX: version/checksum/LOD/bone limits")
    require(group_count == len(mdl_data["groups"]), "VTX: bodygroup count differs")
    replacements = []
    if replacement_offset:
        for at in b.table(0, replacement_offset, lod_count, 8, 8):
            count, _ = b.read("2i", at)
            require(count >= 0, "VTX: material replacement count")
            replacements.append(count)
        require(replacements[0] == 0, "VTX: LOD0 material replacements are outside this oracle")
    result = []
    for g, group_at in zip(mdl_data["groups"], b.table(0, group_offset, group_count, 8, 128)):
        model_count, model_offset = b.read("2i", group_at)
        require(model_count == len(g["models"]), "VTX: choice count differs")
        for model, model_at in zip(g["models"], b.table(group_at, model_offset, model_count, 8, 128)):
            model_lods, lod_offset = b.read("2i", model_at)
            require(0 <= model_lods <= lod_count, "VTX: model LOD count")
            lods = b.table(model_at, lod_offset, model_lods, 12, 8)
            if not model["vertex_count"]:
                require(not model["meshes"], "VTX: blank MDL model has meshes")
                if lods:require(b.read("i", lods[0])[0] == 0, "VTX: blank choice has rendered mesh")
                continue
            require(lods, "VTX: visible choice lacks LOD0")
            mesh_count, mesh_offset, switch = b.read("2if", lods[0])
            require(mesh_count == len(model["meshes"]) and math.isfinite(switch), "VTX: LOD0 mesh count/switch")
            for mesh, mesh_at in zip(model["meshes"], b.table(lods[0], mesh_offset, mesh_count, 9, 4096)):
                count, relative, mesh_flags = b.read("2iB", mesh_at)
                require(mesh_flags & ~3 == 0, "VTX: unknown mesh flags")
                triangles, vertex_records, group_observations = [], {}, []
                for sg_index, sg_at in enumerate(b.table(mesh_at, relative, count, 25, 4096)):
                    vertex_count, vertex_rel, index_count, index_rel, strip_count, strip_rel, flags = b.read("6iB", sg_at)
                    require(flags & ~7 == 0 and 0 < vertex_count <= 65535 and 0 < index_count <= 1000000
                            and index_count % 3 == 0 and 0 < strip_count <= 4096,
                            "VTX: stripgroup legacy bounds/flags: group=%d model=%d mesh=%d sg=%d at=%d fields=%s" %
                            (g['index'],model['index'],mesh['index'],sg_index,sg_at,
                             (vertex_count,vertex_rel,index_count,index_rel,strip_count,strip_rel,flags)))
                    entries = []
                    for vi, at in enumerate(b.table(sg_at, vertex_rel, vertex_count, 9, 65535)):
                        w0, w1, w2, active, original, h0, h1, h2 = b.read("4BH3B", at)
                        require(0 <= original < mesh["vertex_count"] and 1 <= active <= 3
                                and all(w < 3 for w in (w0, w1, w2)[:active]), "VTX: native mesh vertex/weight slots")
                        absolute = model["vvd_lod0_origin"]+mesh["vertex_start"]+original
                        require(0 <= absolute < len(vvd_data["lod0"]), "VTX: VVD origin/range")
                        entries.append(absolute)
                        vertex_records[(sg_index, vi)] = absolute
                    raw_indices = [b.read("H", at)[0] for at in b.table(sg_at, index_rel, index_count, 2, 1000000)]
                    require(all(i < vertex_count for i in raw_indices), "VTX: group index outside vertex table")
                    covered = []
                    strips = []
                    for at in b.table(sg_at, strip_rel, strip_count, 27, 4096):
                        n_indices, first_index, n_vertices, first_vertex, n_bones, strip_flags, changes, changes_rel = b.read("4iHB2i", at)
                        require(strip_flags == 1, "VTX: only explicit legacy TRI_LIST supported; no strip/quad/restart guessing")
                        require(n_indices > 0 and n_indices % 3 == 0 and 0 <= first_index <= index_count
                                and n_indices <= index_count-first_index and 0 <= first_vertex < vertex_count
                                and 0 < n_vertices <= vertex_count-first_vertex and n_bones <= max_strip,
                                "VTX: strip ranges/bone count")
                        state = [b.read("2i", pos) for pos in b.table(at, changes_rel, changes, 8, 65535)]
                        require(all(0 <= slot < max_strip and 0 <= bone < len(mdl_data["bones"]) for slot, bone in state),
                                "VTX: hardware bone state range")
                        selected = raw_indices[first_index:first_index+n_indices]
                        require(all(first_vertex <= i < first_vertex+n_vertices for i in selected), "VTX: strip vertex range differs")
                        for i in range(0, n_indices, 3):
                            triples = tuple(selected[i:i+3])
                            require(len(set(triples)) == 3, "VTX: degenerate/restart triangle outside first oracle")
                            triangles.append(tuple(entries[j] for j in triples))
                        covered.extend(range(first_index, first_index+n_indices))
                        strips.append({"indices": n_indices, "first_index": first_index, "vertices": n_vertices,
                                       "first_vertex": first_vertex, "bone_state_changes": len(state)})
                    require(sorted(covered) == list(range(index_count)), "VTX: strip index coverage overlap/gap")
                    group_observations.append({"index": sg_index, "flags": flags, "vertex_records": vertex_count,
                                               "index_count": index_count, "strips": strips})
                require(triangles, "VTX: visible native mesh has no triangles")
                result.append({"group_index": g["index"], "group_name": g["name"], "model_index": model["index"],
                               "model_name": model["name"], "mesh_index": mesh["index"],
                               "material_column": mesh["material_column"], "triangles": triangles,
                               "compiled_vertex_records": vertex_records, "stripgroups": group_observations})
    return {"version": version, "checksum": checksum, "layout": "packed legacy VTX7 (SG25/strip27), TRI_LIST only",
            "hardware_palette_render_equivalence": "UNTESTED; authoritative native weights come from VVD global bone IDs",
            "meshes": result}


def source_to_gltf(position, scale=.01905):
    x, y, z = position
    return (x*scale, z*scale, -y*scale)


def normal_to_gltf(normal):
    x, y, z = normal
    return (x, z, -y)


def adapter_triangle(triangle):
    # Documented SourceIO from_pydata(np.flip(indices)) reverses each winding.
    return tuple(reversed(triangle))
