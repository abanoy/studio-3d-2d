"""Keep the actual owned fixture writer's identity stable across restart readers.

Test only: SYNCHRONIZE handles to PIDs read under a fresh fixture directory; no
process enumeration/input/termination. Windows may reuse a PID once all handles
close: https://learn.microsoft.com/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_information
"""
import ctypes,json,os,threading
from ctypes import wintypes as W

class WriterHandleGuard:
    def __init__(self,root):
        if os.name!='nt':raise RuntimeError('Owned writer guard requires Windows')
        self.root=root;self.handles={};self.error=None;self.closed=False;self.stop=threading.Event()
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];self.kernel.OpenProcess.restype=W.HANDLE
        self.kernel.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];self.kernel.WaitForSingleObject.restype=W.DWORD
        self.kernel.CloseHandle.argtypes=[W.HANDLE];self.kernel.CloseHandle.restype=W.BOOL
        self.thread=threading.Thread(target=self.watch,daemon=True);self.thread.start()
    def watch(self):
        try:
            while not self.stop.wait(.05):
                for path in self.root.glob('*/session.json'):
                    try:
                        if path.stat().st_size>1024:continue
                        pid=json.loads(path.read_text(encoding='utf-8')).get('pid')
                    except (OSError,ValueError):continue
                    if type(pid) is not int or not 1<=pid<=2147483647 or pid in self.handles:continue
                    if len(self.handles)>=4:raise RuntimeError('Too many fixture writers')
                    handle=self.kernel.OpenProcess(0x00100000,False,pid)
                    if not handle:raise OSError(ctypes.get_last_error(),'Open owned fixture writer')
                    self.handles[pid]=handle
        except BaseException as error:self.error=error
    def writer_finished(self,pid):
        self.stop.set();self.thread.join(3)
        assert not self.thread.is_alive() and self.error is None,self.error
        assert set(self.handles)=={pid},('Actual fixture writer handle must be retained',list(self.handles),pid)
        self.assert_exited()
        return {'pid':pid,'synchronize_handle_retained':True,'writer_exit_verified':True}
    def assert_exited(self):
        assert self.handles and all(self.kernel.WaitForSingleObject(h,0)==0 for h in self.handles.values()),'Fixture writer must actually be stopped'
    def close(self):
        if self.closed:return
        self.stop.set();self.thread.join(3)
        if self.thread.is_alive():raise RuntimeError('Fixture writer monitor did not stop')
        for handle in self.handles.values():
            if not self.kernel.CloseHandle(handle):raise OSError(ctypes.get_last_error(),'Close owned fixture handle')
        self.handles.clear();self.closed=True
