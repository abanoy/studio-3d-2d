# Keep a reference sheet with a project

Open **Reference sheet…** in Draw, load a PNG, and enable **Keep PNG in project**.
The sheet remains an editing aid; it never appears in movie frames or drawing-only
PNG output. One reference PNG is kept with the enclosing project and remains
available while editing its child sequences.

Keeping, replacing, reloading or clearing a kept sheet creates one document Undo
action. Unchecking Keep removes project ownership and leaves the sheet available
for the current session. Undo restores its previous PNG from a verified managed
copy, including when the original file has changed or disappeared. Opening a
project restores its kept sheet ready to view; **Guide over Draw** starts off.
Guide visibility, opacity, zoom and pan remain editor controls.

Default packed `.has` saves embed the exact original PNG bytes. Linked saves put
a verified PNG beside the project in its `.assets` directory and refer to that
file. Keep the sidecar directory when moving a linked project. Original PNG files
remain unchanged. Explicit **Reload** reviews an external change before replacing
the current sheet; opening a kept sheet from a project uses its managed copy.

Projects with a kept sheet use **schema 7**, with an explicit
`content_schema_version` for the existing legacy scene (3), world (4/5) or editable
sequence project (6). The single `studio_reference_sheet_1` record stores its name,
PNG checksum and managed `references/<checksum>.png` path. Older readers reject
schema 7. Current readers reject reference fields attached to older schemas,
invalid wrappers, unsafe paths, changed/missing bytes and invalid PNGs before
replacing the current project. Projects without a kept sheet retain their existing
format. This does not choose the still-OPEN native model/map package extensions.

The image uses the same bounded PNG loader as the session viewer: 16 MiB,
4 megapixels, maximum side 8192. Content-addressed editor copies retain the viewed
version for Undo; manual save and recovery copy it into their own managed stores.
Recovery's existing 512 MiB budget includes the reference source. Ordinary autosave
retains the sheet and active sequence editor/frame. Recovery restores a dirty,
unsaved project copy while keeping explicit `.has` files unchanged.

The focused test is:

```sh
python tests/verify_project_reference.py --isolated-display :100
```

Use an explicitly provisioned private Linux display, or Windows's existing private
desktop launcher. Fresh Linux checks cover all four content schemas, strict
metadata/size guards, actual Keep/replace/Clear/Undo, packed and linked files,
source/cache loss, exact alpha, invalid-image Open preserving the current project,
unchanged originals, nested picture/PCM, a real H264/AAC movie, actual SIGKILL and
ordinary automatic startup recovery, and lesson New/Continue with a kept sheet.
The earlier session-only verifier also
passes. This is procedural software-rendering evidence; native Windows/GPU,
physical-input and artist acceptance remain separate.

Multiple kept sheets, saved overlay alignment, reference palettes, proportion
helpers and optional anatomy suggestions remain separate work.
