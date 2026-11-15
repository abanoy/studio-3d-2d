# Pinned native jiggle reference — research only

Reference: [Valve's solver at019e91ccd650a34745934c65cdbbe89ffcc44ede](https://github.com/ValveSoftware/source-sdk-2013/blob/019e91ccd650a34745934c65cdbbe89ffcc44ede/src/public/jigglebones.cpp),
[declarations](https://github.com/ValveSoftware/source-sdk-2013/blob/019e91ccd650a34745934c65cdbbe89ffcc44ede/src/public/studio.h#L186).
The file's last change is committed November3,2026; this immutable reference is
not a claim about the exact closed SFM/GMod client binary used by the artist.
Full source stays local. FETCH.json and REFERENCE_HASH_CHECK.json record exact
Git blob and SHA256 identities; no reference code was compiled or executed.

The target tip follows the goal transform's localZ column. Junko's0x31 combines
flexible, angle and length constraints. Under length constraint, yaw/pitch
springs are active and along-axis spring terms are bypassed. Tip mass is used
as global downward acceleration, not inverse mass. Euler velocity/position
updates precede angle/length projection and radial-velocity removal.

The reference has frame-rate fallback/history, a minimum timestep and skipped
update reinitialization. HAS needs an explicit preview/export clock policy
before numerical comparison. Its existing generic helper spring is a separate
behavior. The declaration has34float fields after flags; the current app's
independently checked29float prefix remains unchanged and inactive. This
research does not upgrade the production full-layout verification flag.

Next: complete actual neutral/rest/native-Z mapping, then independent numerical
traces for the restricted0x31 subset, followed by actual HAS positive/negative
axis rotations, moved roots/parents and two-scale tests. No native solver, wind
response, recorded take or source-fidelity acceptance is implemented here.
