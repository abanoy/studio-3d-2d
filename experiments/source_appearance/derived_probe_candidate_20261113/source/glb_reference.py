"""Independent, stdlib-only derived-GLB reference. No Godot/Blender imports.

This is deliberately a bounded reader for the actual embedded-buffer fixtures.
Sparse values are bounds/ordering checked; unsupported extensions/images fail. It is not
an independent reader of native Source VVD/VTX/VTF or a Source shader renderer.
"""
from __future__ import annotations
import hashlib
import json
import math
import struct
import zlib


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


IDENTITY = (1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.)


def mul(a, b):
    return tuple(sum(a[r*4+k]*b[k*4+c] for k in range(4)) for r in range(4) for c in range(4))


def point(matrix, value):
    return [sum(matrix[r*4+c]*value[c] for c in range(3))+matrix[r*4+3] for r in range(3)]


def rotation(q):
    require(len(q) == 4 and all(math.isfinite(x) for x in q), "Invalid quaternion")
    x, y, z, w = q
    require(abs(sum(v*v for v in q)-1.) < 1e-4, "Nonunit quaternion")
    return (1-2*y*y-2*z*z, 2*x*y-2*z*w, 2*x*z+2*y*w, 0.,
            2*x*y+2*z*w, 1-2*x*x-2*z*z, 2*y*z-2*x*w, 0.,
            2*x*z-2*y*w, 2*y*z+2*x*w, 1-2*x*x-2*y*y, 0., 0., 0., 0., 1.)


def local(node):
    if "matrix" in node:
        require(not any(k in node for k in ("translation", "rotation", "scale")), "Mixed matrix/TRS")
        a = node["matrix"]
        require(len(a) == 16, "Matrix length")
        return tuple(a[c*4+r] for r in range(4) for c in range(4))
    result = list(rotation(node.get("rotation", [0., 0., 0., 1.])))
    scale = node.get("scale", [1., 1., 1.])
    translation = node.get("translation", [0., 0., 0.])
    require(len(scale) == len(translation) == 3, "TRS dimensions")
    for r in range(3):
        for c in range(3):
            result[r*4+c] *= scale[c]
        result[r*4+3] = translation[r]
    require(all(math.isfinite(x) for x in result), "Nonfinite transform")
    return tuple(result)


def png_rgba(raw):
    """CRC-checked noninterlaced eight-bit PNG, decoded independently of Godot."""
    require(raw[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature")
    offset, chunks, ids, header = 8, [], b"", None
    while offset < len(raw):
        require(offset+12 <= len(raw), "Truncated PNG chunk")
        n = struct.unpack_from(">I", raw, offset)[0]
        kind = raw[offset+4:offset+8]
        require(n <= 16*1024*1024 and offset+12+n <= len(raw), "PNG chunk bounds")
        data = raw[offset+8:offset+8+n]
        require(zlib.crc32(kind+data) & 0xffffffff == struct.unpack_from(">I", raw, offset+8+n)[0], "PNG CRC")
        chunks.append(kind)
        if kind == b"IHDR":
            require(header is None and not ids, "PNG header order")
            header = struct.unpack(">IIBBBBB", data)
        elif kind == b"IDAT":
            ids += data
        elif kind == b"IEND":
            require(n == 0 and offset+12 == len(raw), "PNG end")
            break
        elif kind[0] & 32 == 0:
            raise ValueError("Unsupported critical PNG chunk")
        offset += 12+n
    require(header is not None and chunks[-1:] == [b"IEND"], "Missing PNG header/end")
    width, height, depth, color, compression, filtering, interlace = header
    require(0 < width <= 4096 and 0 < height <= 4096 and depth == 8 and color in (0, 2, 4, 6)
            and (compression, filtering, interlace) == (0, 0, 0), "Unsupported PNG layout")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    stride = width*channels
    dec = zlib.decompressobj()
    packed = dec.decompress(ids, (stride+1)*height+1)
    require(dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(packed) == (stride+1)*height,
            "PNG decompression length/trailing data")
    rgba, previous = bytearray(), bytearray(stride)
    for y in range(height):
        mode = packed[y*(stride+1)]
        require(mode in range(5), "PNG filter")
        row = bytearray(packed[y*(stride+1)+1:(y+1)*(stride+1)])
        for x in range(stride):
            left = row[x-channels] if x >= channels else 0
            above = previous[x]
            upper_left = previous[x-channels] if x >= channels else 0
            p = left+above-upper_left
            pa, pb, pc = abs(p-left), abs(p-above), abs(p-upper_left)
            predictor = (0, left, above, (left+above)//2,
                         left if pa <= pb and pa <= pc else above if pb <= pc else upper_left)[mode]
            row[x] = (row[x]+predictor) & 255
        for x in range(width):
            px = row[x*channels:(x+1)*channels]
            rgba.extend(px if color == 6 else (*px, 255) if color == 2 else
                        (px[0], px[0], px[0], px[1]) if color == 4 else (px[0], px[0], px[0], 255))
        previous = row
    return {"width": width, "height": height, "png_sha256": sha(raw),
            "rgba8_sha256": sha(rgba), "rgba8_bytes": len(rgba)}


class GLB:
    def __init__(self, raw):
        require(28 <= len(raw) <= 16*1024*1024, "GLB byte budget")
        require(struct.unpack_from("<III", raw) == (0x46546c67, 2, len(raw)), "GLB header")
        offset, chunks = 12, []
        while offset < len(raw):
            require(offset+8 <= len(raw), "GLB chunk header")
            size, kind = struct.unpack_from("<II", raw, offset)
            require(size % 4 == 0 and offset+8+size <= len(raw), "GLB chunk bounds")
            chunks.append((kind, raw[offset+8:offset+8+size]))
            offset += 8+size
        require([x[0] for x in chunks] == [0x4e4f534a, 0x004e4942], "Expected exact JSON/BIN chunks")
        self.data = json.loads(chunks[0][1])
        self.binary = chunks[1][1]
        self.raw_sha = sha(raw)
        d = self.data
        require(d.get("asset", {}).get("version") == "2.0" and not d.get("extensionsRequired"), "GLB version/extensions")
        require(len(d.get("buffers", [])) == 1 and "uri" not in d["buffers"][0]
                and 0 <= len(self.binary)-d["buffers"][0]["byteLength"] <= 3, "Expected embedded buffer")
        self.parents = {}
        for i, node in enumerate(d["nodes"]):
            for child in node.get("children", []):
                require(type(child) is int and 0 <= child < len(d["nodes"]) and child not in self.parents,
                        "Invalid/multiply parented node")
                self.parents[child] = i
        roots = d["scenes"][d.get("scene", 0)]["nodes"]
        require(len(set(roots)) == len(roots), "Duplicate scene root")
        self.active = set()
        def visit(index, ancestors):
            require(type(index) is int and 0 <= index < len(d["nodes"]) and index not in ancestors, "Scene graph cycle/index")
            self.active.add(index)
            for child in d["nodes"][index].get("children", []):
                visit(child, ancestors | {index})
        for root in roots:
            require(root not in self.parents, "Scene root has parent")
            visit(root, set())
        self._accessors = {}

    def view(self, index):
        require(type(index) is int and 0 <= index < len(self.data["bufferViews"]), "Buffer view index")
        view = self.data["bufferViews"][index]
        require(view.get("buffer", 0) == 0, "External buffer view")
        start, size = view.get("byteOffset", 0), view["byteLength"]
        require(type(start) is int and type(size) is int and start >= 0 and size >= 0
                and start+size <= self.data["buffers"][0]["byteLength"], "Buffer view bounds")
        return self.binary[start:start+size], view

    def accessor(self, index):
        if index in self._accessors:
            return self._accessors[index]
        require(type(index) is int and 0 <= index < len(self.data["accessors"]), "Accessor index")
        a = self.data["accessors"][index]
        fmt, width = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
                      5125: ("I", 4), 5126: ("f", 4)}[a["componentType"]]
        count = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        size, start = count*width, a.get("byteOffset", 0)
        require(type(a["count"]) is int and 0 < a["count"] <= 200000 and type(start) is int and start >= 0,
                "Accessor count/offset")
        def decode(raw, offset):
            value = struct.unpack_from("<"+fmt*count, raw, offset)
            if a.get("normalized", False):
                require(fmt != "f", "Normalized float")
                maximum = {"b": 127, "B": 255, "h": 32767, "H": 65535, "I": 4294967295}[fmt]
                value = tuple(max(-1., x/maximum) for x in value)
            require(all(math.isfinite(x) for x in value), "Nonfinite accessor")
            return value
        if "bufferView" in a:
            raw, view = self.view(a["bufferView"])
            stride = view.get("byteStride", size)
            require(type(stride) is int and stride >= size and start+(a["count"]-1)*stride+size <= len(raw), "Accessor bounds")
            values = [decode(raw, start+i*stride) for i in range(a["count"])]
        else:
            require(start == 0, "Implicit accessor has byte offset")
            values = [(0.,)*count for _ in range(a["count"])]
        if "sparse" in a:
            sparse = a["sparse"]
            require(isinstance(sparse, dict) and {"count", "indices", "values"} <= sparse.keys(), "Malformed sparse accessor")
            n = sparse["count"]
            require(type(n) is int and 0 < n <= a["count"], "Sparse count")
            indices, replacements = sparse["indices"], sparse["values"]
            require(isinstance(indices, dict) and isinstance(replacements, dict)
                    and {"bufferView", "componentType"} <= indices.keys() and "bufferView" in replacements,
                    "Sparse indices/values declaration")
            require(indices["componentType"] in (5121, 5123, 5125), "Sparse index component type")
            sparse_fmt, sparse_width = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4)}[indices["componentType"]]
            index_raw, index_view = self.view(indices["bufferView"])
            value_raw, value_view = self.view(replacements["bufferView"])
            index_start, value_start = indices.get("byteOffset", 0), replacements.get("byteOffset", 0)
            require("byteStride" not in index_view and "byteStride" not in value_view
                    and type(index_start) is int and type(value_start) is int and index_start >= 0 and value_start >= 0
                    and index_start+n*sparse_width <= len(index_raw) and value_start+n*size <= len(value_raw), "Sparse bounds/stride")
            previous = -1
            for i in range(n):
                target = struct.unpack_from("<"+sparse_fmt, index_raw, index_start+i*sparse_width)[0]
                require(previous < target < a["count"], "Sparse indices not strictly increasing/in range")
                values[target] = decode(value_raw, value_start+i*size)
                previous = target
        self._accessors[index] = values
        return values

    def globals(self, pose_node=None, pose_quaternion=None):
        memo, visiting = {}, set()
        def get(i):
            if i in memo:
                return memo[i]
            require(i not in visiting, "Node hierarchy cycle")
            visiting.add(i)
            matrix = local(self.data["nodes"][i])
            if i == pose_node:
                matrix = mul(matrix, rotation(pose_quaternion))
            memo[i] = mul(get(self.parents[i]), matrix) if i in self.parents else matrix
            visiting.remove(i)
            return memo[i]
        for index in self.active:
            get(index)
        return memo

    def primitives(self):
        for index in sorted(self.active):
            node = self.data["nodes"][index]
            if "mesh" in node:
                for primitive_index, primitive in enumerate(self.data["meshes"][node["mesh"]]["primitives"]):
                    require(primitive.get("mode", 4) == 4, "Expected triangles")
                    yield index, primitive_index, primitive

    def native_bindings(self, native_bones):
        """Join native indices to the actual used palette by exact unique names/parents.

        Blender may preorder the palette differently from the native MDL table.
        The explicit join preserves both identities rather than treating indices
        from these separate tables as interchangeable.
        """
        used_skins = {self.data["nodes"][node]["skin"] for node, _, _ in self.primitives()}
        require(used_skins, "Expected native skinned components")
        palettes = [self.data["skins"][i]["joints"] for i in used_skins]
        require(all(nodes == palettes[0] for nodes in palettes), "Ambiguous used skin palettes")
        palette = palettes[0]
        names = [self.data["nodes"][j].get("name") for j in palette]
        native_names = [b["name"] for b in native_bones]
        require(len(names) == len(set(names)) == len(native_names) == len(set(native_names))
                and set(names) == set(native_names), "Native/GLB binding name correspondence differs")
        joint_set = set(palette)
        result = []
        for native_index, bone in enumerate(native_bones):
            palette_index = names.index(bone["name"])
            node = palette[palette_index]
            parent = self.parents.get(node)
            seen = set()
            while parent is not None and parent not in joint_set:
                require(parent not in seen, "Joint ancestor cycle")
                seen.add(parent)
                parent = self.parents.get(parent)
            actual_parent = self.data["nodes"][parent].get("name") if parent is not None else None
            require(type(bone["parent"]) is int and -1 <= bone["parent"] < len(native_bones), "Native parent index")
            expected_parent = native_bones[bone["parent"]]["name"] if bone["parent"] >= 0 else None
            require(actual_parent == expected_parent, "Native/GLB binding parent correspondence differs")
            result.append({"native_index": native_index, "native_name": bone["name"], "native_parent_index": bone["parent"],
                           "glb_palette_index": palette_index, "source_node": node})
        return result

    def positions(self, morph_weight=None, pose_node=None, pose_quaternion=None):
        globals_ = self.globals(pose_node, pose_quaternion)
        result = []
        for node_index, primitive_index, p in self.primitives():
            node = self.data["nodes"][node_index]
            mesh = self.data["meshes"][node["mesh"]]
            base = self.accessor(p["attributes"]["POSITION"])
            require(all(len(v) == 3 for v in base), "POSITION dimensions")
            indices = sorted(set(x[0] for x in self.accessor(p["indices"]))) if "indices" in p else list(range(len(base)))
            require(all(type(i) is int and 0 <= i < len(base) for i in indices), "Primitive index range")
            targets = p.get("targets", [])
            weights = list(node.get("weights", mesh.get("weights", [0.]*len(targets))))
            require(len(weights) == len(targets), "Morph weight length")
            if morph_weight is not None and mesh.get("extras", {}).get("targetNames") == ["Tools"]:
                weights = [morph_weight]
            deltas = [self.accessor(t["POSITION"]) if "POSITION" in t else [(0., 0., 0.)]*len(base) for t in targets]
            require(all(len(t) == len(base) for t in deltas), "Morph accessor length")
            skin = self.data["skins"][node["skin"]] if "skin" in node else None
            if skin:
                require(set(k for k in p["attributes"] if k.startswith("JOINTS_")) == {"JOINTS_0"}, "Expected one influence set")
                joints = self.accessor(p["attributes"]["JOINTS_0"])
                influence = self.accessor(p["attributes"]["WEIGHTS_0"])
                binds = self.accessor(skin["inverseBindMatrices"])
                require(len(binds) == len(skin["joints"]), "Inverse bind length")
                matrices = [mul(globals_[j], tuple(b[c*4+r] for r in range(4) for c in range(4)))
                            for j, b in zip(skin["joints"], binds)]
            points = []
            for v in indices:
                vertex = [base[v][c]+sum(weights[t]*deltas[t][v][c] for t in range(len(targets))) for c in range(3)]
                if skin:
                    require(len(joints[v]) == len(influence[v]) == 4 and abs(sum(influence[v])-1) < 1e-4,
                            "Invalid skin influences")
                    position = [0., 0., 0.]
                    for j, w in zip(joints[v], influence[v]):
                        require(type(j) is int and 0 <= j < len(matrices) and 0 <= w <= 1, "Skin joint/weight")
                        transformed = point(matrices[j], vertex)
                        for c in range(3):
                            position[c] += w*transformed[c]
                else:
                    position = point(globals_[node_index], vertex)
                require(all(math.isfinite(x) and abs(x) < 100000 for x in position), "Invalid derived point")
                points.append(position)
            material_index = p["material"]
            result.append({"source_node": node_index, "source_name": node.get("name", ""),
                           "primitive": primitive_index, "material_index": material_index,
                           "material_name": self.data["materials"][material_index].get("name", ""),
                           "positions": points})
        return result

    def materials(self):
        result = []
        for i, material in enumerate(self.data.get("materials", [])):
            texture_index = material["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            image_index = self.data["textures"][texture_index]["source"]
            image = self.data["images"][image_index]
            require(image.get("mimeType") == "image/png" and "uri" not in image, "Expected embedded PNG")
            raw, _ = self.view(image["bufferView"])
            result.append({"material_index": i, "name": material.get("name", ""), "definition": material,
                           "texture_index": texture_index, "image_index": image_index, "image": png_rgba(raw)})
        return result


def bounds(primitives):
    points = [p for primitive in primitives for p in primitive["positions"]]
    require(points, "No reference points")
    return [[min(p[c] for p in points) for c in range(3)], [max(p[c] for p in points) for c in range(3)]]
