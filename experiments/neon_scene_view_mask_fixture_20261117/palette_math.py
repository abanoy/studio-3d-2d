"""CPU arithmetic oracle only. No UI/native image or asset reads."""
from math import isfinite
MASK=(4/255,5/255,8/255)
ALPHA=.62
TOLERANCE=2/255

def forward(base,neon):
    return tuple((1-ALPHA)*x+ALPHA*m for x,m in zip(base,MASK)) if neon else tuple(base)

def recover(pixel,neon):
    return tuple((x-ALPHA*m)/(1-ALPHA) for x,m in zip(pixel,MASK)) if neon else tuple(pixel)

def qualify(base,pixel,neon):
    if len(base)!=3 or len(pixel)!=3 or not all(isfinite(x) for x in (*base,*pixel)):return False
    expected=forward(base,neon)
    recovered=recover(pixel,neon)
    return base[1]>.45 and base[2]>.3 and max(abs(x-y) for x,y in zip(pixel,expected))<=TOLERANCE and recovered[1]>.45 and recovered[2]>.3
