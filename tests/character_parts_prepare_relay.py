"""Generated-fixture handoff to exercise the real sequential preparer route."""
import argparse
import json
from pathlib import Path
import shutil
parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--status-file', type=Path, required=True)
args, _ = parser.parse_known_args()
fixture = Path(args.source.read_text(encoding='utf-8').strip())
args.output.mkdir(parents=True)
target = args.output / 'scene.glb'
shutil.copyfile(fixture, target)
args.status_file.write_text(json.dumps({'ok': True, 'glb': str(target)}), encoding='utf-8')
