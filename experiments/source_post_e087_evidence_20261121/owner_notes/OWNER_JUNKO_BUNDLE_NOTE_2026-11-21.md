# Junko as one character

The folder contains six actual model families: body, hair, dress, skirt, miniskirt and character mask. The VVD/VTX files and materials are their dependencies, so they should not appear as extra character pieces. All99 original files remained unchanged during the read-only audit.

The first visible addition should load the six models under one Junko entry in World, with a Parts list. Moving or scaling Junko moves the whole bundle. Right-click → Manage parts should provide Show/Hide at the current frame and grouping Attach/Detach. The pieces keep their own morphs, hair/clothes setup and original geometry.

Body and hair can be the initial visible set. Dress, skirt and miniskirt should be available as reviewed outfit sets, with the mask optional. Loading everything must not stack every clothing alternative visibly. One outfit switch should be one Undo operation, and hiding a piece must keep it available.

The shared size reference belongs to the body/bundle once. Hair, mask and clothing must retain their source alignment rather than each being resized to six feet independently.

Posing needs a separate step from grouping. Body and dress share56 identical bone rest mappings, but two of those bones already own procedural motion. Hair has six shared anchors with slightly different rest data; the mask changes some parent relationships. Skirt and miniskirt reuse136 bone names while135 rest poses differ. Automatically merging matching names would risk breaking motion and shape. The first grouping stage therefore preserves separate rigs; later body-pose following needs an explicit checked link that leaves child hair/clothing motion in control of its own joints. Saved bone links must make unsupported old readers refuse them clearly.

The compact [six-family audit](C:/a/Programming/cloudflare/has-body-addition-20261120/output/source-junko-root-bundle-prep-20261121/BUNDLE_AUDIT.json) and [implementation map](C:/a/Programming/cloudflare/has-body-addition-20261120/output/source-junko-root-bundle-prep-20261121/README.md) record these findings. The pure bundle planner’s25 tests passed. This proves the planning rules; model conversion, alignment, World controls, Undo/cold reopen and posed part-following still need their own qualification. The bundle has not been added to the current application yet.
