"""Context-only successor of the root's retained passive color diagnostic."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/run_neon_color_diagnostic_20261117.py';raw=parent.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='a984985243d753cd53feb0898a59f73c3037da6109ddf168ab20aabe0d699e6f'
changes=[
 (b'neon_color_sampler_conjunction_diagnostic_20261117',b'neon_color_sampler_pixel_center_proposal_20261117'),
 (b'neon-color-diagnostic-696-',b'neon-color-diagnostic-center-'),
 (b'7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141',b'102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'),
 (b"b'696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'",b"b'3a3701ab6edfa81dc883759403c170b8555aab07'"),
 (b' assert H.sources()==frozen[\'source_sha256\']',b" frozen['source_sha256']['tests/color_sampler_smoke.gd']='102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'\n assert H.sources()==frozen['source_sha256']"),
]
source=raw
for a,b in changes:
 assert source.count(a)==1 and b not in source;source=source.replace(a,b,1)
inverse=source
for a,b in reversed(changes):assert inverse.count(b)==1;inverse=inverse.replace(b,a,1)
assert inverse==raw
scope={'__file__':str(parent),'__name__':'root_center_passive_diagnostic'}
exec(compile(source,str(parent),'exec'),scope)
if __name__=='__main__':raise SystemExit(scope['main']())
