"""Separate Root headless Job; approved handle API/layout, no desktop APIs."""
import ctypes as C
from ctypes import wintypes as W
import os,sys
class Accounting(C.Structure):
    _fields_=[('TotalUserTime',C.c_int64),('TotalKernelTime',C.c_int64),
              ('ThisPeriodTotalUserTime',C.c_int64),('ThisPeriodTotalKernelTime',C.c_int64),
              ('TotalPageFaultCount',W.DWORD),('TotalProcesses',W.DWORD),
              ('ActiveProcesses',W.DWORD),('TotalTerminatedProcesses',W.DWORD)]
class RootJob:
    def __init__(self,layout):
        if os.name!='nt' or sys.implementation.name!='cpython' or sys.version_info[:2]!=(3,13):
            raise RuntimeError('Approved Windows CPython3.13 required; no fallback')
        if C.sizeof(C.c_void_p)!=8 or C.sizeof(layout.ExtendedLimits)!=144 or C.sizeof(Accounting)!=48:
            raise RuntimeError('Unexpected approved native Job ABI')
        self.kernel=C.WinDLL('kernel32',use_last_error=True)
        def api(name,result,*args):
            value=getattr(self.kernel,name);value.restype=result;value.argtypes=args;return value
        self.create=api('CreateJobObjectW',W.HANDLE,C.c_void_p,W.LPCWSTR)
        self.configure=api('SetInformationJobObject',W.BOOL,W.HANDLE,C.c_int,C.c_void_p,W.DWORD)
        self.assign_native=api('AssignProcessToJobObject',W.BOOL,W.HANDLE,W.HANDLE)
        self.contains_native=api('IsProcessInJob',W.BOOL,W.HANDLE,W.HANDLE,C.POINTER(W.BOOL))
        self.terminate_native=api('TerminateJobObject',W.BOOL,W.HANDLE,W.UINT)
        self.query_native=api('QueryInformationJobObject',W.BOOL,W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD))
        self.close_native=api('CloseHandle',W.BOOL,W.HANDLE)
        self.process_id=api('GetProcessId',W.DWORD,W.HANDLE)
        self.times=api('GetProcessTimes',W.BOOL,W.HANDLE,*([C.POINTER(W.FILETIME)]*4))
        self.handle=self.create(None,None);self.assigned=False;self.closed=False
        if not self.handle:raise OSError(C.get_last_error(),'Create Root-only headless Job')
        try:
            limits=layout.ExtendedLimits()
            limits.BasicLimitInformation.LimitFlags=0x2000|0x8|0x200
            limits.BasicLimitInformation.ActiveProcessLimit=16
            limits.JobMemoryLimit=4*1024*1024*1024
            if not self.configure(self.handle,9,C.byref(limits),C.sizeof(limits)):
                raise OSError(C.get_last_error(),'Configure Root16-process4GiB Job')
            observed=layout.ExtendedLimits();length=W.DWORD()
            if not self.query_native(self.handle,9,C.byref(observed),C.sizeof(observed),C.byref(length)):
                raise OSError(C.get_last_error(),'Read Root Job limits')
            flags=observed.BasicLimitInformation.LimitFlags
            if length.value!=C.sizeof(observed) or flags!=(0x2000|0x8|0x200) or observed.BasicLimitInformation.ActiveProcessLimit!=16 or observed.JobMemoryLimit!=4*1024*1024*1024:
                raise RuntimeError('Root Job limits or no-breakaway contract differs')
        except BaseException:
            self.close();raise
    def identity(self,process):
        pid=self.process_id(process._handle);values=[W.FILETIME() for _ in range(4)]
        if not pid or not self.times(process._handle,*(C.byref(x) for x in values)):
            raise OSError(C.get_last_error(),'Read retained wrapper process identity')
        born=(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
        if not born or int(pid)!=process.pid:raise RuntimeError('Retained process identity differs')
        return {'pid':int(pid),'created_100ns':str(born)}
    def assign(self,process):
        if not self.assign_native(self.handle,process._handle):raise OSError(C.get_last_error(),'Assign gated wrapper to Root Job')
        self.assigned=True;contained=W.BOOL()
        if not self.contains_native(process._handle,self.handle,C.byref(contained)) or not contained.value:
            raise RuntimeError('Specific Root Job containment not observed')
        if self.accounting()['active']!=1:raise RuntimeError('Only trusted gated wrapper may exist before START')
    def accounting(self):
        value=Accounting();length=W.DWORD()
        if not self.query_native(self.handle,1,C.byref(value),C.sizeof(value),C.byref(length)):
            raise OSError(C.get_last_error(),'Query owned Root Job active processes')
        if length.value!=C.sizeof(value):raise RuntimeError('Unexpected Job accounting ABI length')
        return {'active':int(value.ActiveProcesses),'total':int(value.TotalProcesses),
                'terminated_by_limit':int(value.TotalTerminatedProcesses)}
    def terminate(self):
        if not self.closed and self.assigned and not self.terminate_native(self.handle,0xC000013A):
            raise OSError(C.get_last_error(),'Terminate only Root-owned descendants')
    def close(self):
        if self.closed:return
        if self.handle and not self.close_native(self.handle):raise OSError(C.get_last_error(),'Close Root-only Job')
        self.handle=None;self.closed=True
