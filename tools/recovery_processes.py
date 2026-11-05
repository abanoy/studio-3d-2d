"""Read liveness of only the supplied recovery-owner PIDs; never enumerate or stop processes."""
import ctypes
from ctypes import wintypes
import json
import os
import sys

def details(pids):
    if os.name!='nt':return {'owners':{str(pid):'unknown' for pid in pids},'created_100ns':{}}
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)];kernel.GetProcessTimes.restype=wintypes.BOOL
    result={};created={}
    for pid in pids:
        ctypes.set_last_error(0)
        # Read-only query + wait rights. If query access is denied, preserve the
        # original wait-only liveness result; never infer an incarnation then.
        handle=kernel.OpenProcess(0x00101000,False,pid)
        timing=bool(handle)
        if not handle and ctypes.get_last_error()!=87:handle=kernel.OpenProcess(0x00100000,False,pid)
        if not handle:
            result[str(pid)]='exited' if ctypes.get_last_error()==87 else 'unknown'
            continue
        try:
            state=kernel.WaitForSingleObject(handle,0)
            result[str(pid)]='alive' if state==258 else 'exited' if state==0 else 'unknown'
            if timing and state==258:
                times=[wintypes.FILETIME() for _ in range(4)]
                if kernel.GetProcessTimes(handle,*(ctypes.byref(t) for t in times)):
                    value=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
                    if value>0:created[str(pid)]=str(value)
        finally:
            if not kernel.CloseHandle(handle):result[str(pid)]='unknown';created.pop(str(pid),None)
    return {'owners':result,'created_100ns':created}

def query(pids):
    return details(pids)['owners']

def main():
    if not 0<len(sys.argv)-1<=1024:raise ValueError('Expected 1–1024 recovery owner PIDs')
    pids=[int(value) for value in sys.argv[1:]]
    if any(not 1<=pid<=2147483647 for pid in pids):raise ValueError('Invalid recovery owner PID')
    print(json.dumps({'format':'studio_process_liveness_1',**details(pids)}))
if __name__=='__main__':main()
