# Separate Windows review copy — November 11

Ready for later use; no owner review or feedback is requested while the owner is
busy. Pending artist/device observations remain pending until the owner chooses
to resume them. Automated checks cannot certify those observations.

Current review folder:

`C:\a\Programming\cloudflare\has-acceptance-session-20261111\output\owner-review-current`

Owner-operated launchers:

- `Open Avatar.bat`: native VRM, camera controls, nested docking and fan controls.
- `Open Flatgrass.bat`: supported native BSP conversion.
- `Open Street.bat`: native PMX environment with its five supplied atlases.
- `Open Reimu helpers.bat`: native player model with the reviewed ribbon helper
  and its saved recorded animation. This demonstrates selected weighted helper
  generation; it does not claim complete automatic hair or cloth rigging.
- `Start review.bat`: ordinary Home with an independent settings profile.

The source copy was frozen from retrieval commit
`bd09769150ede7a47590b6024928bc050bc52c9d`, including the verified Windows metadata
separator fix. Normal Home/startup was tested on a
private desktop, with no foreground child and a closed job/desktop. All four
packed project copies retained their hashes after preparation. Originals and
installed Studio were preserved. No automated visible launch was performed.

Today's earlier `output\owner-review` copy is retained too. Yesterday's review is
still retained at
`C:\a\Programming\cloudflare\has-acceptance-session-20261110\output\owner-review`.
Its `Studio\output\recovery` contains private owner work and must remain intact.
Nothing was migrated out of that recovery folder or overwritten there.

To recreate source later, fetch the retrieval commit and use
`tools/build_owner_review_snapshot.py --output output/owner-review-current` with
separately preserved private packed
projects. The repository deliberately excludes those private projects. Native
Mima preparation is reproducible using `tests/prepare_mima_fixture.py` and the
checksum-bound original archive. Existing approved tools and the pinned
temporary SourceIO runtime remain separate from the source snapshot.

The builder refuses a folder outside this checkout's output and refuses to
overwrite an existing Studio. The current snapshot's four launchers include
Reimu helpers automatically. Neither old review source nor its profile/recovery
was replaced.

Detailed observations, when the owner grants time, remain in
[windows_acceptance_followup.md](windows_acceptance_followup.md). A configured
development PC and same-machine source copy do not establish clean offline
Windows installation, physical tablet latency or novice/artist acceptance.
