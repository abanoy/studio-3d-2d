"""Read liveness of only the supplied recovery-owner PIDs; never enumerate or stop processes."""
import ctypes
from ctypes import wintypes
import json
import os
import sys
from pathlib import Path
import re

def linux_details(pids, proc=Path('/proc')):
    """Read only requested PIDs. Boot UUID + start ticks distinguish PID reuse.

    Unknown/denied/malformed observations always protect the session. No
    process enumeration, terminating signals or wall-clock identities are used.
    """
    result={};started={}
    try:
        boot=(proc/'sys/kernel/random/boot_id').read_text().strip()
        if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot):boot=None
    except OSError:boot=None
    for pid in pids:
        if type(pid) is not int or not 1<=pid<=2147483647:raise ValueError('Invalid recovery owner PID')
        key=str(pid);result[key]='unknown'
        try:
            # comm can itself contain spaces and closing parentheses.
            with (proc/key/'stat').open('rb') as stream:raw=stream.read(65537)
            if len(raw)>65536:continue
            prefix,separator,tail=raw.rpartition(b') ')
            fields=tail.split()
            if not separator or not prefix.startswith(key.encode()+b' (') or len(fields)<20:continue
            if fields[0] in [b'Z',b'X',b'x']:result[key]='exited';continue
            if fields[0] not in [b'R',b'S',b'D',b'T',b't',b'W',b'K',b'P',b'I']:continue
            ticks=fields[19].decode('ascii')
            if not re.fullmatch(r'[1-9][0-9]{0,19}',ticks) or int(ticks)>18446744073709551615:continue
            result[key]='alive'
            if boot:started[key]=boot+':'+ticks
        except FileNotFoundError:
            # A missing proc mount or missing stat for an existing/hidden owner
            # is not evidence that this PID exited.
            try:
                if (proc/'self/stat').is_file():
                    try:os.kill(pid,0)  # existence check only; sends no signal
                    except ProcessLookupError:result[key]='exited'
            except OSError:pass
        except (OSError,UnicodeError):pass
    return {'owners':result,'created_100ns':{},'linux_start':started}

def details(pids):
    if sys.platform=='linux':return linux_details(pids)
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
    print(json.dumps({'format':'studio_process_liveness_2' if sys.platform=='linux' else 'studio_process_liveness_1',**details(pids)}))
if __name__=='__main__':main()
