# Integrated Studio review

Prepared only; Studio has not been launched from these shortcuts.

- **Open Studio discovery.bat** starts an empty Studio. Choose New scene, then Simple **Add > Asset discovery…**, or Advanced **Discover**. Local stays offline: choose directories and filter filenames. Online access and thumbnail previews require separate opt-in; online listings open their source website in your default browser, rather than downloading models.
- **Open Direct lights.bat** opens a generated room, model and reflective prop with the default Compatibility renderer. Choose **Lit**, then **Lights…** beside the lighting menu. Advanced exposes the full workspace. Add Directional, Point or Spot lights, select a row, edit color/intensity/shadows and **Apply light**. Expand Placement and beam to move or aim a lamp. Presets and edits support Undo/Redo.
- **Open Environment bounce.bat** uses optional Forward+ for a generated red-wall room and skinned panel. In Lights, expand **Environment bounce (SDFGI prototype, Forward+)**. Static environment geometry contributes bounced color; models receive it but do not provide dynamic indirect shadows. Rebuild after moving the room. The settling-frame budget spends rendering time; it is not path tracing or a guarantee for arbitrary scenes. Forward+ can cost more GPU time.

Each shortcut has its own Windows user-data profile under Profiles. Normal project work and launch logs can also appear in the source checkout output folder. USERPROFILE is unchanged. The two Projects/*.has files are packed, self-contained generated shapes with no original model artwork or external asset links. Their historical import-source paths are provenance only. Save any edits to a new project if you want to retain these starting examples.

These launchers use the current integration source checkout and existing Python installation. This folder is not a standalone packaged Studio build; keep the source checkout available. PREPARATION.json records the portability checks and artifact hashes.
