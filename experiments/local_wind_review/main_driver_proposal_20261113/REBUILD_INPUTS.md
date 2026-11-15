# Exact fixture rebuild recipes and limits

These recipes are proposed, not executed in this task. Reuse approved installed Python/Godot/Blender and the separately approved disposable pinned SourceIO runtime. Do not install/replace tools, access network sources, search Steam automatically, or use an old prototype cache to fill a missing fixture. Raw originals remain read-only; all generated destinations must be fresh owned directories.

## Identity map

| Role | Original input and SHA256 | Required prepared GLB SHA256 | Required parameters.json SHA256 |
| --- | --- | --- | --- |
| VRM0 | AvatarSample_Avrm0.vrm; `f7b4573b241b3e91c7c5f58bed342133a4e5f7e0c1125e1cedc49723ace9b288` | `3caa50b76d0f481bb7ee66daeb6ebe7485aefb966140321b599ca60d9d464b56` | `0f8f746ca68a821acaf9e502b6895a2f2798d8d1d2bd62569d78deea652fc0ef` |
| VRM1 | AvatarSample_A.vrm; `14d2b2c751e2d6b7739471b961d71b7b16ca28089c04d9465b9c71a113033ee3` | `a0b095f399e0f7f95c88b91d12e74f8d1816052c1552b9d2dd758ceed8a6b062` | `21f11bfb2c606fd13fa21e2d4cdbe130555918b52f92ff6030598b10ce680372` |
| Ribbon-derived Reimu | touhou_reimu_bikini.gma; `66442ce25e36ca4a8dbccbe0c321278d4d2afbbd5603495d470ad366f869a88b`; member models/player/reimu_hakurei_bikini.mdl | `4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5` | `f4e1850d9f4fa9359a72d43f3c945aaf61a1bd726538b025da31c4fa5f8071ba` |

The Reimu **player** member is required. The earlier ragdoll member is a different fixture and cannot substitute for this case. The raw SHA in its parameter report refers to the GMA archive, even though `source_file` names the selected MDL.

## VRM preparation

Use current main `tools/prepare_vrm.py`, preserving its code hash in the preparation receipt. It directly prepares actual native VRM bytes; a renamed GLB is invalid. Check original hashes before and after. With `<fixture root>/wind-native/vrm0` and `vrm1` absent:

```powershell
python tools/prepare_vrm.py 'C:\path\to\originals\AvatarSample_Avrm0.vrm' --scale 1 --output 'C:\path\to\owned\prepared-fixtures\wind-native\vrm0'
python tools/prepare_vrm.py 'C:\path\to\originals\AvatarSample_A.vrm' --scale 1 --output 'C:\path\to\owned\prepared-fixtures\wind-native\vrm1'
```

Compare both resulting GLB and parameter-report hashes with the table. VRM0's documented180degree Y conversion and VRM1's native facing remain handled by the production adapter.

## Pristine Source preparation and the existing ribbon

Recorded preparation uses Blender5.1.2 and SourceIO5.5.5 at commit `fe24260b97ac03b899d9b5d4f0fd7b34772f3647`. The pinned SourceIO archive SHA256 in dependencies.json is `cd44e1d053ac853c5d1628da9faa27a594337ebacb3587744dfa5d60758623de`. Use the already approved session-owned runtime; this recipe does not download it. Scale is exactly0.01905. Keep `source_profile: standalone`, selected member and original GMA identity in the resulting parameter report.

```powershell
python tools/prepare_source.py 'C:\a\tools\touhou_reimu_bikini.gma' --member models/player/reimu_hakurei_bikini.mdl --scale 0.01905 --sourceio 'C:\path\to\owned\sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647' --blender 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --output 'C:\path\to\owned\prepared-fixtures\wind-native\pristine'
```

The exact Windows pristine prepared GLB is `4b23dbf5dfc402a08871d392143efa687dc10b869fc9344aa3f565099947e1f2`. Require that identity before helper generation. The older Linux preparation `f7717417...` is different; its node numbers/bytes cannot silently replace this Windows fixture.

The accompanying `ribbon-request.json` is the exact reviewed request recovered from retained worker receipts. Canonical `json.dumps(request,sort_keys=True)` produces SHA256 prefix `26e82282b205`, matching the embedded `__HAS_Loose_26e82282b205` declaration. It chooses node85, primitive0, component2, anchor14,3segments and the exact4reviewed control points; production defaults strength0.95 and pin_fraction0.2 remain implicit as in the historical request. Do not add those otherwise-equal defaults to the request object: the request digest contributes to generated node names and therefore file bytes.

With the destination `ribbon` absent:

```powershell
python tools/secondary_helpers.py 'C:\path\to\owned\prepared-fixtures\wind-native\pristine\scene.glb' --request 'C:\path\to\retained\ribbon-request.json' --output 'C:\path\to\owned\prepared-fixtures\wind-native\ribbon'
Copy-Item -LiteralPath 'C:\path\to\owned\prepared-fixtures\wind-native\pristine\parameters.json' -Destination 'C:\path\to\owned\prepared-fixtures\wind-native\ribbon\parameters.json'
```

Current main secondary_helpers.py SHA256 during this proposal is `dc5ff2353bbc3759b8464eb52f4de30996b09d07392534b26da1d5af5e376fe6`. The exact ribbon output must match `4d62236...ab7b5`, contain1spring with joints99/100/101/102, and preserve embedded pristine-source provenance and the244vertex hair_ribbon_left region. This is a reviewed generated helper, not a native Source jiggle descriptor.

## Back hair configuration inside each verifier run

The fixture manifest points to **ribbon-only** input, not a previously configured2chain output. The verifier stages a byte/mtime-exact copy, then uses current main backend preview/build with this exact request:

```json
{"source_sha256":"4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5","node":80,"primitive":1,"component":5,"review_only":true,"use_existing_joints":true,"reviewed":true}
```

Require native joints11/10/9 and3affected regions/1369weighted vertices, then retain the old ribbon and verify2declarations,0changed vertices, preserved skin and exact original geometry/material/binary structures. The older composition proof's configured hash `d7036490...` came from a **different request identity** (`__HAS_Existing_0a73a19d648d_End`). The retained Wind driver request above produces prefix `__HAS_Existing_a4499d1a1dfc`; do not incorrectly pin its configured output to d703. Its newly generated hash and full report must be recorded from the actual run.

## Honest reproducibility limits

These are exact input recipes and pins, not a fresh bit-rebuild result. Source export bytes may differ with Blender/exporter version, dependency mounts, preparation code or platform. The Source parameter report also contains the absolute `original_source` path; moving the GMA to another path can legitimately change that report's bytes. Preserve the existing accepted report when staging an accepted bundle. A fresh rebuild that differs must retain its complete provenance and undergo review; do not remove path fields, relabel the source, accept an arbitrary manifest hash, or relax the gate to obtain a pass.

The published packet contains source/evidence only. Native model payloads stay local/private. `native_fixture_plans` currently has no saved first-class role for these3wind inputs; this proposal adds that narrow resolver using the established `fixture_output()` convention. Catalogue shape plans and recorded native models remain separate inputs and cannot replace the declared-chain wind fixtures.
