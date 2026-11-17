# Independent PMX 2.0 physics-byte reader design

Source-only design for the parent implementer; no parser is implemented here.
Primary source is the installed pure MMD Tools PMX reader, 51,956 bytes, SHA256
`fb9aafe369025f221bc5a1c952d868260b1a4bb950dc33bca62645b4da454e5a`.
Its installed addon manifest is version 4.5.11. The source was read and AST-indexed,
not imported or executed. No native model, engine, CIM, Git or review file was used.

This design locates native physics bytes by walking the preceding PMX layout.
It does not validate all geometry, establish physical plausibility, bind HAS
bones, convert units/axes/scale, simulate, or qualify portable/native behavior.
PMX 2.1 and its soft-body section remain explicitly unsupported.

## Notation and header

All numbers are little endian. `I` is a signed 32-bit count; `F` is one raw
binary32 word; `F3/F4` are 12/16 bytes. `TEXT` is signed I byte length followed
by exactly that many encoded bytes. Length must be nonnegative, bounded and in
range before reading. Preserve original name bytes and the encoding; do not use
replacement decoding. Strict UTF-16LE also requires an even byte length.

Header is exactly 17 bytes: four-byte `PMX ` signature; exact F32 version bytes
`00000040` (2.0); one byte equal to 8; then eight global bytes. Those globals are
encoding 0=UTF-16LE or 1=UTF-8, additional UV count A (0..4), and widths V,T,M,B,O,R.
Each width is exactly 1, 2 or 4. V is an unsigned vertex index; texture T, material
M, bone B, morph O and rigid R indices are signed. Preserve width and raw word.
Reject the 2.1 word `66660640`, other versions, unknown header lengths and unknown
index widths before attempting a prefix walk.

Pinned anchors: `FileReadStream` 47–119; `Header.load` 262–298; `Model.load`
349–560. This reader checks only the first three signature bytes and merely warns
on a header length other than 8; a strict successor must not copy either behavior.

## Exact prefix order and skip lengths

Following the header: four TEXT values (model name, English name, comment,
English comment), then the following count/table pairs in order. All table and
nested counts must be nonnegative, bounded and checked against remaining bytes
before loops or allocations.

| Table | Record layout from pinned reader |
| --- | --- |
| Vertices | I count. Each: position F3, normal F3, UV F2, A additional F4 vectors; deform byte; deformation payload below; edge scale F |
| Face indices | I **index** count, then count × unsigned V bytes. Require count divisible by 3. Do not floor the count |
| Textures | I count, then TEXT per entry; never resolve or open texture paths |
| Materials | I count. Each: TEXT ×2; diffuse F4, specular F3, shininess F, ambient F3; flags u8; edge F4, edge size F; T texture index, T sphere index; sphere mode i8; shared-toon flag i8; shared toon i8 if flag 1, otherwise T toon index if flag 0; TEXT comment; I surface-index count |
| Bones | I count. Variable record described below |
| Morphs | I count. TEXT ×2, category i8, type i8, I offset count, then fixed-width offsets by type below |
| Display frames | I count. TEXT ×2, special byte (0/1), I element count; each element has a byte tag, then B for tag 0 or O for tag 1 |
| Rigid bodies | I count, then native records below |
| Joints | I count, then native records below; require exact EOF afterward |

Vertex deformation payload sizes, excluding its tag and trailing edge F:

| Tag | Payload bytes |
| --- | --- |
| 0 BDEF1 | B |
| 1 BDEF2 | 2B + 4 |
| 2 BDEF4 | 4B + 16 |
| 3 SDEF | 2B + 40: two bone indices, one weight F, C/R0/R1 each F3 |

Thus each vertex is `32 + 16A + 1 + payload + 4` bytes. Refuse QDEF/tag 4 and
unknown tags for the first restricted 2.0 profile; do not assume another tag has
the BDEF4 size. `Vertex.load` is 657–666 and `BoneWeight.load` is 722–748.

Material fixed data after the two names and before the comment is
`67 + 2T + (1 if shared else T)` bytes. Only flag values 0/1 may choose the toon
branch. Keep unsupported flag/mode policy explicit; do not interpret any non-1
value as a valid unshared toon. `Material.load` is 845–879. Its texture-index
clamping and loss of unrecognized flag bits must not be used as a byte oracle.

## Variable bone records

`Bone.load` 969–1028 reads TEXT ×2, location F3, parent B, transform layer I,
and a **16-bit flags word** (source reads signed; retain raw u16 bits). The known
bits consumed or represented by this source form mask `0x3f3f`. Other bits should
explicitly refuse in the narrow initial profile rather than be guessed away.

Process conditional payloads in this exact order:

1. Bit `0x0001`: display-connection bone B; otherwise display offset F3.
2. Bits `0x0100` or `0x0200`: grant source B plus influence F **once**, including
   when both bits are set. Neither bit means zero bytes.
3. Bit `0x0400`: fixed axis F3.
4. Bit `0x0800`: local X axis F3 and local Z axis F3.
5. Bit `0x2000`: external parent transform key I.
6. Bit `0x0020`: IK target B, iterations I, per-step limit F, link count I;
   each link is B target plus one limit byte, followed by minimum F3 and maximum
   F3 only for byte 1. Byte 0 has no angle data; refuse other limit bytes.

Other recognized bits alter no record length: `0x0002/4/8/10` and `0x1000`.
`IKLink.load` is 1094–1102. The pinned reader treats every limit byte other than
1 as false and ignores unknown bone flags; neither is a safe strict-layout rule.

Retain every bone's original table index and raw/native names, including empty
or duplicate names. Do not infer a HAS identity. Parent and connection -1 are
represented by the upstream writer; preserve them. Do not indiscriminately allow
-1 in every bone/IK/weight/morph reference: any additional semantic reference
validation must state its own field-specific scope. Prefix byte traversal alone
does not qualify a valid skeleton or skin.

## Morph widths and display selectors

Anchors: `Morph.create` 1134–1154; offset loaders 1190–1348. Each width below is
per offset, excluding names/category/type/count:

| Morph type | Bytes |
| --- | --- |
| 0 group | O + 4 |
| 1 vertex | V + 12 |
| 2 bone | B + 28: translation F3 plus quaternion F4 |
| 3..7 UV/additional UV | V + 16, including ordinary UV type 3 |
| 8 material | M + 113: mode i8 and **28** F32 words |

The material words are diffuse4, specular3, shininess1, ambient3, edge-color4,
edge-size1, texture-factor4, sphere-factor4, toon-factor4. Refuse unknown morph
types (including 2.1 flip/impulse), negative/excessive counts and unknown
selectors. A restrictive first profile can also refuse out-of-domain categories,
material operation modes or UV-layer declarations; disclose that restriction.
`Display.load` 1367–1384 accepts element tags only 0/1. The special flag should
also be strict 0/1, rather than mapping unknown values to false.

## Physics record boundaries and exact preservation

`Rigid.load` 1437–1462: TEXT name; TEXT English name; signed bone B; group i8;
mask **u16**; shape i8; size F3; location F3; rotation F3; mass F; velocity
attenuation F; rotation attenuation F; bounce F; friction F; mode i8. Payload
after the two TEXTs is **B + 61** bytes (14 F32 words). Preserve the high mask bit.
Shapes/modes 0/1/2 are known to the pinned reader. Refuse unknown codes in the
first direct-reader profile; do not silently decode a future record layout.

`Joint._load` 1529–1551: TEXT ×2; mode i8; source R; destination R; location F3;
rotation F3; minimum location F3; maximum location F3; minimum rotation F3;
maximum rotation F3; linear spring F3; angular spring F3. Payload after the names
is **97 + 2R** bytes (24 F32 words). Only mode 0 is represented by this source's
declared enum; explicitly refuse other types before assuming this layout.

Physics absent references are raw **-1**, not every negative value. Body bone
must be -1 or [0,bone_count); joint source/destination must be -1 or
[0,rigid_count). Reject values below -1 and out-of-range positive indices.
The pinned body loader wrongly collapses all negative bone words to None;
the joint loader explicitly maps only -1. Retain the native signed word and
index even if any friendly decoded representation is also provided.

Preserve every physics F32 **raw four-byte word**, signed zero, name byte string,
encoding, original index/mask, record begin/end offsets and complete source SHA.
Any float view must derive from those same words. Reject nonfinite physics values
under the declared finite profile; do not normalize, round, repair zero
quaternions, change units or clamp physical values. Record/data validity and
runtime support remain separate from exact byte provenance.

## Upstream loss/truncation behaviors not to copy

The reader has no count/name/resource caps and no final EOF check. Negative
counts can skip loops; face counts are floored into triples. String decode uses
replacement characters. Texture paths are resolved/normalized. Material texture
indices outside the table become -1. Unknown flags/selectors can disappear.
`BoneMorphOffset.load` replaces an all-zero quaternion with identity.
`Joint.load` 1514–1527 can replace truncated missing vectors with zeros, and
top-level `load` 1580–1603 catches `struct.error` without re-raising it. A direct
reader must fail on every short read and must not call this tolerant decoder to
claim an exact native-file join.

Require exact EOF after the final 2.0 joint. Extra zero padding, a zero soft-body
count, unknown extensions, appended bytes or a second file are not silently
discarded. PMX 2.1/soft-body capture must be a separately reviewed extension.

## Suggested bounded profile and independent fixtures

These are proposed resource caps, not PMX specification maxima or implemented
HAS support: source128 MiB; vertices2M; indices12M; textures/materials10k each;
bones4096; morphs/display frames4096; aggregate morph offsets1M; total IK links
65536; display elements65536; bodies512; joints1024; per-string1 MiB and aggregate
strings8 MiB. Apply smaller name/capsule limits consistent with the decoded
prototype (1024 UTF-8 bytes/name, 128 KiB capsule), including a whole-output size
check. Oversize means explicit refusal, not truncation. Validate count×width and
offset arithmetic against remaining bytes before iteration or allocation.

`FIXTURE_EXPECTATIONS.json` contains one manually offset-specified 339-byte
authored, geometry-free 2.0 source as hex, with two duplicate-name bones, one
body and one joint. It is not a renderable-model fixture. Independent expected
offsets/words allow parent tests to avoid trusting a fixture writer that mirrors
the parser. No installed reader was executed to produce or verify it.

Additional fixture matrix: all widths1/2/4; UTF8/UTF16LE names (including duplicate,
empty and malformed encodings); A0/A4 and every deform; both grant flags together;
every optional bone flag and IK-limit branch; all morph types0..8; shared/unshared
toon; both display tags; masks0/0x8000/0xffff; legal -1 versus -2 and positive
reference boundaries; each field truncated at every byte boundary; every count
negative/limit/limit+1; unknown flags/tags; NaN/Inf physics words; raw negative
zero; trailing bytes; source2.1 refusal. Authored expected offsets and raw words
must be independent of parser output. Native-file and portable cold tests remain
root-owned later; no native or solver qualification follows from synthetic passes.
