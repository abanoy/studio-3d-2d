# Additional helper-workflow limit

This follows sealed integration-map INDEX `474b6bc933c41d869bb32f1cdbf101800f81c5634e886822aff9ba72005c9470`; that packet is unchanged. This is source review only, without native input or engine use.

The ordinary scene loader's GLB limit is128MiB and its JSON length is bounded by that file. A separate current consumer has a tighter limit: `tools/secondary_helpers.py:16,88` admits at most16MiB GLB JSON and exactly JSON/BIN chunks. Both helper writers enforce the same16MiB encoded-JSON limit at lines634/671. Thus the proposed archive assembler should also measure the **whole resulting JSON chunk** against the helper-compatible16MiB profile when offering future helper compatibility; a2MiB capsule cap alone is insufficient when the original GLB already has substantial metadata. Unsupported limits must be disclosed, not silently solved by dropping the archive or widening helper limits.

The helper writes the parsed GLB document back, so an unrelated asset-extra envelope has a source-level preservation path. Its `helpers.json` contains the generated helper report, not the entire GLB document (`secondary_helpers.py:644,681`). This does not prove actual byte-level capsule preservation or resource use. The future synthetic integration suite must exercise a helper derivation and extract the exact original capsule text after it. Root-owned native tests must later confirm the same without changing raw source identity/provenance. A changed derived-GLB checksum must not be mistaken for a changed native capsule source SHA.

`src/wind_helper_candidate.gd:15–23` has a512MiB metadata-inspection file ceiling and no separate small JSON cap; its later model import still delegates to the ordinary scene loader. Its paused candidate metadata is constructed separately for preview, not copied from all asset extras. This is not a guarantee that a512MiB model can be imported or that large metadata is cheap.

No capsule/copier, limits, runtime activation, source format or UI is implemented by either planning packet.
