from pathlib import Path
import json
import sys
from mathutils import Euler

root=Path(sys.argv[sys.argv.index('--')+1])
value=Euler((.31,-.28,.62),'XYZ').to_quaternion()
result=Euler((.2,-.2,.4),'XYZ').to_quaternion()
(root/'euler.json').write_text(json.dumps({'input':[value.x,value.y,value.z,value.w],'minimum':[-.1,-.2,-.3],'maximum':[.2,.1,.4],'expected':[result.x,result.y,result.z,result.w]}),encoding='utf-8')
print('JOINT_EULER_REFERENCE')
