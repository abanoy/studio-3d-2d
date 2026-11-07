"""Declared project drawing/file counts; retained bytes have separate admission."""
MAX_CELS=400
MAX_PROJECT_FILES=1024

def error(layers):
    if not isinstance(layers,list) or len(layers)>4:return 'Invalid drawing tracks'
    total=0
    for layer in layers:
        if not isinstance(layer,dict) or not isinstance(layer.get('cels'),list):return 'Invalid drawing track'
        total+=len(layer['cels'])
    return '' if total<=MAX_CELS else 'Project exceeds the supported400drawing limit'
