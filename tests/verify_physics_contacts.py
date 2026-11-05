"""Actual self-contact, mesh-weight fitting and native joint-stretch checks."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command
def main():
    p=subprocess.run(command('tests/physics_contacts_smoke.gd'),cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200)
    text=p.stdout+p.stderr
    (ROOT/'output/physics-contacts-verification.log').write_text(text,encoding='utf-8')
    if p.returncode or 'PHYSICS_CONTACTS ' not in text or '"failures":0' not in text or any(x in text for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']):raise RuntimeError(text)
    report=json.loads((ROOT/'output/physics-contacts-result.json').read_text(encoding='utf-8'))
    (ROOT/'output/physics-contacts-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
