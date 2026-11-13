"""Read-only PE header/literal evidence; no external modules or memory dump input."""
import hashlib
import json
import pathlib
import struct

image = pathlib.Path(r"C:\a\tools\Godot\Godot_v4.6-stable_win64.exe")
blob = image.read_bytes()
pe = struct.unpack_from("<I", blob, 0x3C)[0]
assert blob[pe:pe + 4] == b"PE\0\0"
section_count = struct.unpack_from("<H", blob, pe + 6)[0]
symbol_pointer, symbol_count = struct.unpack_from("<II", blob, pe + 12)
optional_size = struct.unpack_from("<H", blob, pe + 20)[0]
characteristics = struct.unpack_from("<H", blob, pe + 22)[0]
optional = pe + 24
assert struct.unpack_from("<H", blob, optional)[0] == 0x20B
image_base = struct.unpack_from("<Q", blob, optional + 24)[0]
debug_rva, debug_size = struct.unpack_from("<II", blob, optional + 112 + 6 * 8)
sections = []
for index in range(section_count):
    start = optional + optional_size + index * 40
    name = blob[start:start + 8].split(b"\0")[0].decode()
    virtual_size, rva, raw_size, raw_pointer = struct.unpack_from("<IIII", blob, start + 8)
    sections.append(dict(name=name, virtual_size=hex(virtual_size), rva=hex(rva),
                         raw_size=hex(raw_size), raw_pointer=hex(raw_pointer)))

def read_literal(va):
    rva = va - image_base
    for section in sections:
        section_rva = int(section["rva"], 16)
        raw_size = int(section["raw_size"], 16)
        if section_rva <= rva < section_rva + raw_size:
            offset = int(section["raw_pointer"], 16) + rva - section_rva
            end = blob.index(b"\0", offset)
            return dict(va=hex(va), rva=hex(rva), file_offset=hex(offset),
                        section=section["name"], text=blob[offset:end].decode("utf-8"))
    raise ValueError(hex(va))

evidence = dict(image=str(image), length=len(blob), sha256=hashlib.sha256(blob).hexdigest(),
                preferred_base=hex(image_base), characteristics=hex(characteristics),
                coff_symbol_pointer=hex(symbol_pointer), coff_symbol_count=symbol_count,
                debug_directory_rva=hex(debug_rva), debug_directory_size=debug_size,
                sections=sections,
                literals=[read_literal(va) for va in
                          (0x147209528, 0x14720954B, 0x1472094F8, 0x147C4C4E0)],
                stack_rvas=[hex(x) for x in (0x3D95B6C, 0x3D95E44, 0x4B6049C)],
                lock_helper_rva="0x37f8890", critical_section_rva="0xa3caf80")
output = pathlib.Path(__file__).with_name("pe-evidence.json")
output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(output)
