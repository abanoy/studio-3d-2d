from pathlib import Path
import json,time
out=Path(__file__).resolve().parent
text=(out/'remove_verified_easing_cpu_stages_20261121.ps1').read_text()
old='(Split-Path -LiteralPath $resolvedTarget -Parent)';assert text.count(old)==1
text=text.replace(old,'([System.IO.Path]::GetDirectoryName($resolvedTarget))')
anchor='$processes = @';assert text.count(anchor)==1
prefix="""& 'C:/Program Files/Python313/python.exe' -I -S -B 'C:/a/Programming/cloudflare/has-body-addition-20261120/output/check_easing_cleanup_ready_20261121.py' --verify-only
if ($LASTEXITCODE -ne 0) { throw 'Fresh exact native/hash/recovery verification failed' }
"""
text=text.replace(anchor,prefix+anchor)
path=out/'remove_verified_easing_cpu_stages_v2_20261121.ps1';assert not path.exists();path.write_text(text)
(out/'EASING_CLEANUP_INITIAL_PREFLIGHT_API_REFUSAL_20261121.json').write_text(json.dumps({'status':'REFUSED_BEFORE_REMOVAL','directories_removed':0,'tool_result':'765eaf exit1','cause':'PowerShell Split-Path LiteralPath/Parent parameter-set mismatch. Version2 uses exact Path.GetDirectoryName and an immediate fresh full-byte/native-identity preflight.','subsequent_creator_attempt':'068a55 parser refused before Python; 4e00a6 missing script refused before removal. Correct creator uses a source file, preserving all refusals.','recorded_ns':time.time_ns()},indent=2)+'\n')
print(str(path))
