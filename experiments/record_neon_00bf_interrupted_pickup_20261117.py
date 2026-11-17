"""Record real restart/partial-run facts; keep the unfinished state untouched."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
authority = ROOT / 'experiments/neon_00bf_OS_interruptions_20261117/RESTART_AUTHORITY.json'
assert hashlib.sha256(authority.read_bytes()).hexdigest() == 'a69367aa1a317da33ac62fc4005c93f1cbac86df4fe6d92df72bd1b45071c3b0'
proof = json.loads(authority.read_bytes())
assert proof['full_pass_claimed'] is False and proof['suite_exit'] is None
summary = json.loads((ROOT / 'experiments/neon_00bf_interrupted_freeze_20261117_summary.json').read_bytes())
record = {
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'result': 'INTERRUPTED_NO_TERMINAL_RESULT', 'source_commit': proof['revision'],
    'old_state_unchanged': True, 'suite_exit': None, 'functional_sources_unchanged': 1029,
    'root_restart_authority_sha256': hashlib.sha256(authority.read_bytes()).hexdigest(),
    'known_boot_observations': proof['known_boot_observations'],
    'private_metadata_files': 215, 'phase_documents': 52, 'completed_receipts': 80,
    'normal_exit0': 79, 'registered_Krita_cancel_exit2': 1, 'inline_exact_matches': 11,
    'all_old_jobs_gracefully_closed': 'unknown', 'full_pass_claimed': False,
    'replay2_preflight_refusals_before_reservation': ['pythonw.exe', 'ffmpeg.exe'],
    'original_runtime_stamp_difference_fields': 'UNKNOWN_NOT_CAPTURED',
    'replay2_full_started': False, 'redesign_merged': False,
}
paragraph = '''
### November 17, 2026 — Windows restarts interrupted the unchanged00bf run

Windows booted at13:29:40.5000000Z and again15:44:12.5000000Z. Root observed
the original coordinator/Python absent and later strict ROOT/REVIEW test scopes
empty. The old run still says running, with no suite exit or source-after.
It is INTERRUPTED_NO_TERMINAL_RESULT, not a software failure or full pass. Root
did not edit that state or run a terminal helper with fabricated facts. All1029
current functional bytes still match the frozen candidate. No process was killed.

A bounded private snapshot preserves215 metadata files/52 phase documents,
80 individually completed private receipts(79exit0 and one registered Krita
cancel2) and11 exact inline matches. Every215 object/80 receipt and12 closure
negative checks passed. Overall interrupted/unwritten jobs and graceful closure
remain unknown. Native models, report internals and logs stay private; public
source/scalar evidence references the exact private manifest6ea95acc.

The same-candidate replay2 preparation preserves all original source/input/Git
guards. Source inverse and64 proof negatives pass. Two actual preflights refused
before reservation or engine launch at an in-read Pythonw/FFmpeg file-stamp
check. The original differing fields were not captured; cause remains unknown.
Four subsequent Pythonw reads matched the original approved identity exactly.
The checks are unchanged; runtime diagnosis and strict fresh preparation remain.
No fresh full, product merge, owner-copy or startup187 result is claimed.

Source-only public-full projection and certificate successor are sealed:14 and
18 CPU methods pass. They expose explicit scalar results and an opaque root
private-certificate hash; they do not verify omitted private evidence or authorize
an archive. Raw successful reports/canonical logs remain private. Human checks
stay deferred;55/62 acceptance and52/54 implementation remain unchanged.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
text = text.replace('CURRENT at 2026-11-17T04:44:03.096097+00:00:', 'HISTORICAL running observation at 2026-11-17T04:44:03.096097+00:00:', 1)
intro = '''
CURRENT: old00bf full is INTERRUPTED_NO_TERMINAL_RESULT after Windows reboots
13:29:40.5000000Z and15:44:12.5000000Z. State remainsrunning/noexit/nosource-after;
do NOT patch it or invoke its strict terminalhelper as though terminal existed.
Root exact oldprocess absence/current strictscope0 and1029source equality are
recorded in experiments/neon_00bf_OS_interruptions_20261117/RESTART_AUTHORITY.json
SHAa69367aa. Bounded PRIVATE snapshot215files/52phases/80completedreceipts/11inline
is6ea95acc; oldunwrittenjobs/overallgracefulclosure UNKNOWN. No root termination.

Same00bf replay2 source6bb62e6d retains ALL preflight/Git/input predicates; inverse
and64negative proof cases pass. Actualpreflight refused beforeanyreservation or
engine at in-readPythonw thenFFmpeg stamps; originaldifferingfield/cause UNKNOWN.
Four subsequentPythonw reads/originalidentity match; guards unchanged. Diagnose
all6approvedruntimes then retry strictpreflight/newprivate run with fresh births.
No replay2 full started at this dated observation. Root exclusive native lane.

Completedcold187 adapter remains INACTIVE; source29CPU is not startup187. Public
successful-full projection14/certificate18CPU is source-only; omittedprivate
data is not validated byprojection and archiveactivation still refuses.

'''
heading = '# HAS continuation — November 17, 2026\n'
assert text.count(heading) == 1
text = text.replace(heading, heading + intro, 1)
path.write_text(text, encoding='utf-8', newline='\n')
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = json.loads(path.read_bytes())
bench['interrupted00bf_prior_running_observation'] = bench['latest_observation']
bench['latest_observation'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = json.loads(path.read_bytes())
ledger['next_actions'][0]['action'] = ('Old00bf interrupted byOSrestart, never fabricate terminal/PASS/exit. '
    'Root restartauthority a693/source1029 unchanged and private215/80receipt freeze6ea complete; alloldjobgracefulclosure unknown. '
    'Diagnose unchanged strict runtime stamp refusals, then samecandidate replay2 fresh full/births/context. '
    'Publish source/scalar progress; raw full/logs private. Qualifiedmerge/copy/cold187 remain gated; manualdeferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(record))
