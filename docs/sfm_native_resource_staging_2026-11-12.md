# Bounded SFM resources and actual VMT closure

Root reviewed the output-only stager and authorized its exact frozen scope.
Actual read-only preflight passed, then the reviewed per-member extraction
staged **296 files / 181,460,484 bytes in 18.96 seconds**, with no broader archive
extraction. The native originals, pinned 7-Zip, frozen plan and source guards
retained their exact SHA256, size and modification stamps. The final stage has
only the allowlisted files in their original package layout; no scripts or
executables were extracted. No automatic cleanup occurred.

| Case | Staged resources | Actual VMT analysis | Finding |
| --- | --- | --- | --- |
| Nitori glove | 230 files / 134,276,708 bytes | 6 VMTs; 28 observed texture-reference edges | 25 edges resolve. Three unresolved edges all request `materials/hairbump.vtf`, one from each glow VMT. Full observed native texture closure is **incomplete**. All base textures used by the current simple bridge resolve. |
| Keiki chisels | 66 files / 47,183,776 bytes | 4 VMTs; 16 observed texture-reference edges | All observed references resolve within this case's owned package. Base-texture closure is complete. |

All ten selected VMTs are plain `VertexlitGeneric` files with no include,
conditional or nested-proxy branches in this observed set. All texture-key
references encountered by the parser were classified; no unknown path-like
values were found. It did not execute their shaders or decode their textures.
The missing Nitori bump resource was not replaced from Keiki's package or the
different nested Takane material directory. Installed content was not mounted.

These materials also request native bump, environment-map, Phong and warp
effects. The current bridge's Base Color/alpha approximation does not reproduce
those effects. Passing its base-texture closure neither makes Nitori's complete
native dependencies present nor proves glow/shader fidelity.

The independent CPU safety checks comprise **22 stager checks and 12 VMT
parser/closure controls**, with zero failures, errors or skips. They include
unsafe-path/link/encryption/duplicate checks, changed CRC/size/hash and overwrite
refusals, bounded subprocess output/timeouts, malformed VMT refusal, owned include
resolution, missing-base rejection and an explicit distinction between a missing
native-only map and complete supported base inputs. Earlier CPU logs/artifacts
remain retained as well.

Evidence:

- `runs/preflight-1794542745973314000/verification.json`: actual read-only archive
  preflight, zero staged files.
- `runs/execute-1794542752822327800/verification.json`: full exact resource
  inventory, original/tool/plan/source pre/post stamps and extraction evidence.
- `runs/vmt-closure-1794542959743314500/verification.json`: actual VMT reference
  graph and identical pre/post stamps for the 296 staged files, originals, plan
  and staging receipt.
- `cpu-tests-1794542645160595500/verification.json`: final 22-check stager CPU run.
- `vmt-cpu-tests-1794542948233374500/verification.json`: 12-check VMT CPU run.
- `real-staging-time.json`: measured elapsed time and exit zero.

`NATIVE-STAGING-HANDOFF.json` binds the implementation/evidence hashes.
`commands-for-owned-stage.json` contains future loose-MDL conversion command
arrays, still **unrun**. On that route both request checksums are the MDL hash;
the RAR checksum remains upstream provenance. Do not use the preserved earlier
plan's hypothetical staging paths as current paths.

Blender material-slot remapping/export, actual selected mesh membership,
bone/weight/morph preservation, rendered differences, application choice review
and adoption, Undo/Redo, linked/packed/fresh source-offline HAS and movie agreement
remain unrun or unimplemented. Neither candidate has procedural bones, so this
does not certify the other supplied models' native jiggle or component binding.
The normal application, installed tools, Steam content, owner originals and
current review source were unchanged. Keep these private staged payloads local;
promote only reviewed source and compact metadata/evidence to Git.
