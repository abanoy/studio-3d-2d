# Optional wording review, no code changes

The exact candidate retains the wording used by the successful830-check isolated
run. Suggestions below have **not** been applied or approved as product changes.
Keep implementation phase numbers out of Simple controls. Put unfinished scope
in development/review notes; explain only limits that help a user choose an action.

References are line numbers in `overlay/src/wind_review.gd`.

| Lines | Current wording | Possible wording | Purpose |
| --- | --- | --- | --- |
| 44,82 | Review local wind… / Try local wind | Preview wind… / Preview wind | One familiar name for the same action. |
| 45 | checked declared hair/clothing groups | existing hair and clothing groups | Remove an implementation term. Keep the promise that scene settings and recorded animation stay unchanged. |
| 85 | Clicking a row changes the focus; checks stay separate | Select a row, then turn wind on or off for that group | Describe the actual steps and separate selection from inclusion. |
| 88 | Try wind on this group | Use wind on this group | Separate per-group membership from the master start/stop switch. |
| 90,93 | Strength; From right/left/front/behind | Wind strength; a note that directions use the view when preview starts | Make the reference direction clear without changing camera behavior. |
| 95 | Try a local blow | Run wind preview | A possible clearer master action; the owner originally used “Try a local blow,” so preserve that preference unless changing it helps the final flow. |
| 130 | weighted regions and descendant joints | areas attached to these linked chains move together | Explain why one native group may affect several visible areas; retain the limitation that separate areas require different weights. |
| 132 | preparing / local try-out running / scene settings unchanged | Preparing preview… / Preview running / Preview stopped | Name the current state directly; keep “Scene settings stay unchanged” as a separate persistent note. |
| 176 | also drives a body joint | shares a joint with this model's body physics | Explain the conflict, then the concrete action to pause body Physics for that model. |
| 177–182 | model source changed | model file changed; close and reopen Wind Preview | Give a concrete recovery action. |

A status detail needs separate review if clearer stop reasons are wanted:
`stop_preview` at260 accepts `_reason` but does not display it. “Stopped,”
“Cancelled” and “Review changed” are therefore internal call arguments today,
not visible explanations. Do not claim the UI already explains these reasons.

The delivered scope remains explicit in review/help notes: only groups already
defined in the model are previewed; temporary wind checks are separate from
**Include in setup**. Pending helper setup preview before Apply and permanent
per-group exclusions are still open. A wording edit must get its own source
hashes and relevant UI verification; don't silently treat altered source as the
exact830-check version.
