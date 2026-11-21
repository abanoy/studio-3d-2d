"""Run an owned Windows test process on a private, never-activated desktop.

No SwitchDesktop, foreground activation, hooks or user input injection. This is
test infrastructure, not an isolation boundary for untrusted files. A kill-on-close
job owns the child tree, including when the launcher is terminated unexpectedly.
"""
from pathlib import Path
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
import subprocess
import sys
import threading
import time
import uuid


class Startup(C.Structure):
    _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR), ('lpDesktop', W.LPWSTR), ('lpTitle', W.LPWSTR),
                *[(key, W.DWORD) for key in ('dwX', 'dwY', 'dwXSize', 'dwYSize', 'dwXCountChars', 'dwYCountChars', 'dwFillAttribute', 'dwFlags')],
                ('wShowWindow', W.WORD), ('cbReserved2', W.WORD), ('lpReserved2', C.POINTER(W.BYTE)),
                ('hStdInput', W.HANDLE), ('hStdOutput', W.HANDLE), ('hStdError', W.HANDLE)]


class Process(C.Structure):
    _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE), ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]


class BasicLimits(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_longlong), ('PerJobUserTimeLimit', C.c_longlong), ('LimitFlags', W.DWORD),
                ('MinimumWorkingSetSize', C.c_size_t), ('MaximumWorkingSetSize', C.c_size_t), ('ActiveProcessLimit', W.DWORD),
                ('Affinity', C.c_size_t), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]


class Counters(C.Structure):
    _fields_ = [(key, C.c_ulonglong) for key in ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class ExtendedLimits(C.Structure):
    _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', Counters),
                *[(key, C.c_size_t) for key in ('ProcessMemoryLimit', 'JobMemoryLimit', 'PeakProcessMemoryUsed', 'PeakJobMemoryUsed')]]


def run_private(args, receipt_path, timeout=300, cancel_file=None, memory_limit_mib=0):
    if os.name != 'nt': raise RuntimeError('Private desktop testing requires Windows')
    if type(memory_limit_mib) is not int or memory_limit_mib and not 64<=memory_limit_mib<=16384:raise ValueError('Invalid owned job memory limit')
    u = C.WinDLL('user32', use_last_error=True); k = C.WinDLL('kernel32', use_last_error=True)
    def api(lib, name, result, *arguments):
        f = getattr(lib, name); f.restype = result; f.argtypes = arguments; return f
    create_desktop = api(u, 'CreateDesktopW', W.HANDLE, W.LPCWSTR, W.LPCWSTR, C.c_void_p, W.DWORD, W.DWORD, C.c_void_p)
    close_desktop = api(u, 'CloseDesktop', W.BOOL, W.HANDLE)
    thread_desktop = api(u, 'GetThreadDesktop', W.HANDLE, W.DWORD)
    set_thread_desktop = api(u, 'SetThreadDesktop', W.BOOL, W.HANDLE)
    object_information = api(u, 'GetUserObjectInformationW', W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD))
    current_thread = api(k, 'GetCurrentThreadId', W.DWORD)
    foreground = api(u, 'GetForegroundWindow', W.HWND)
    window_pid = api(u, 'GetWindowThreadProcessId', W.DWORD, W.HWND, C.POINTER(W.DWORD))
    callback_type = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    enumerate_windows = api(u, 'EnumDesktopWindows', W.BOOL, W.HANDLE, callback_type, W.LPARAM)
    enumerate_thread_windows = api(u, 'EnumThreadWindows', W.BOOL, W.DWORD, callback_type, W.LPARAM)
    create_process = api(k, 'CreateProcessW', W.BOOL, W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD, C.c_void_p, W.LPCWSTR, C.POINTER(Startup), C.POINTER(Process))
    close_handle = api(k, 'CloseHandle', W.BOOL, W.HANDLE)
    current_process = api(k, 'GetCurrentProcess', W.HANDLE)
    get_standard = api(k, 'GetStdHandle', W.HANDLE, W.DWORD)
    duplicate = api(k, 'DuplicateHandle', W.BOOL, W.HANDLE, W.HANDLE, W.HANDLE, C.POINTER(W.HANDLE), W.DWORD, W.BOOL, W.DWORD)
    create_file = api(k, 'CreateFileW', W.HANDLE, W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE)
    create_job = api(k, 'CreateJobObjectW', W.HANDLE, C.c_void_p, W.LPCWSTR)
    configure_job = api(k, 'SetInformationJobObject', W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD)
    assign_job = api(k, 'AssignProcessToJobObject', W.BOOL, W.HANDLE, W.HANDLE)
    resume = api(k, 'ResumeThread', W.DWORD, W.HANDLE)
    wait = api(k, 'WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
    terminate = api(k, 'TerminateProcess', W.BOOL, W.HANDLE, W.UINT)
    exit_code = api(k, 'GetExitCodeProcess', W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
    def require(ok, action):
        if not ok: raise OSError(C.get_last_error(), action)
    def desktop_name(handle):
        if not handle: return ''
        text = C.create_unicode_buffer(512); needed = W.DWORD()
        return text.value if object_information(handle, 2, text, C.sizeof(text), C.byref(needed)) else ''
    desktop = job = nul = None; process = Process(); duplicates = []
    stop_monitor = threading.Event(); monitor = None
    name = 'HAS_Test_' + uuid.uuid4().hex
    receipt = {'format': 'studio_private_desktop_1', 'desktop': name, 'desktop_switch_requested': False,
               'private_window_seen': False, 'child_desktop_confirmed': False, 'maximum_owned_windows': 0, 'foreground_child_observed': False, 'exit': None}
    start = time.monotonic()
    try:
        original_desktop = thread_desktop(current_thread()); require(original_desktop, 'Read launcher thread desktop')
        # Read/write/window/menu/enumeration rights only: no desktop-switch right.
        desktop = create_desktop(name, None, None, 0, 0x00c7, None); require(desktop, 'Create private test desktop')
        require(set_thread_desktop(original_desktop), 'Restore launcher thread desktop')
        job = create_job(None, None); require(job, 'Create owned test job')
        limits = ExtendedLimits(); limits.BasicLimitInformation.LimitFlags = 0x2000
        if memory_limit_mib:
            limits.BasicLimitInformation.LimitFlags |= 0x200
            limits.JobMemoryLimit = memory_limit_mib * 1024 * 1024
            receipt['job_memory_limit_bytes'] = limits.JobMemoryLimit
        require(configure_job(job, 9, C.byref(limits), C.sizeof(limits)), 'Configure test-tree cleanup')
        nul = create_file('NUL', 0xc0000000, 3, None, 3, 0, None)
        require(nul and nul != C.c_void_p(-1).value, 'Open null input')
        for code in (-10, -11, -12):
            source = get_standard(code & 0xffffffff)
            if code == -10 or not source or source == C.c_void_p(-1).value: source = nul
            handle = W.HANDLE()
            require(duplicate(current_process(), source, current_process(), C.byref(handle), 0, True, 2), 'Duplicate owned standard handle')
            duplicates.append(handle)
        info = Startup(); info.cb = C.sizeof(info); info.lpDesktop = name; info.dwFlags = 0x101; info.wShowWindow = 4
        info.hStdInput, info.hStdOutput, info.hStdError = duplicates
        line = C.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in args]))
        # Suspended until successfully assigned to our cleanup job. Never fall
        # back to launching on the user's desktop if any setup step fails.
        require(create_process(str(args[0]), line, None, None, True, 0x08000004, None, os.getcwd(), C.byref(info), C.byref(process)), 'Create private test process')
        receipt['child_pid'] = process.dwProcessId
        require(assign_job(job, process.hProcess), 'Assign private test tree')
        def watch_desktop():
            try:
                require(set_thread_desktop(desktop), 'Attach owned desktop monitor')
                @callback_type
                def count_window(hwnd, _):
                    pid = W.DWORD(); window_pid(hwnd, C.byref(pid))
                    if pid.value == process.dwProcessId: current_windows.append(int(hwnd))
                    return True
                while not stop_monitor.is_set():
                    child_desktop = desktop_name(thread_desktop(process.dwThreadId))
                    if child_desktop:
                        if child_desktop != name: raise RuntimeError('Child did not attach to its private desktop')
                        receipt['child_desktop_confirmed'] = True
                    current_windows = []
                    C.set_last_error(0)
                    enumerated = enumerate_windows(desktop, count_window, 0)
                    if enumerated and current_windows:
                        # EnumDesktopWindows is authoritative placement evidence;
                        # the engine's Win32 GUI thread may differ from its entry
                        # thread, which GetThreadDesktop cannot always query.
                        receipt['child_desktop_confirmed'] = True
                        receipt['private_window_seen'] = True
                    if not enumerated and C.get_last_error(): receipt['desktop_enumeration_error'] = C.get_last_error()
                    enumerate_thread_windows(process.dwThreadId, count_window, 0)
                    receipt['maximum_owned_windows'] = max(receipt['maximum_owned_windows'], len(set(current_windows)))
                    stop_monitor.wait(.02)
            except BaseException as error: receipt['monitor_error'] = str(error)
        monitor = threading.Thread(target=watch_desktop, daemon=True); monitor.start()
        require(resume(process.hThread) != 0xffffffff, 'Resume private test process')
        while True:
            if cancel_file and Path(cancel_file).exists():
                receipt['cancelled'] = True
                raise InterruptedError('Owned converter cancelled')
            state = wait(process.hProcess, 0)
            if state == 0: break
            if state != 258: raise RuntimeError('Cannot observe owned test process')
            if time.monotonic() - start > timeout: raise TimeoutError('Private test process timed out')
            if receipt.get('monitor_error'): raise RuntimeError(receipt['monitor_error'])
            pid = W.DWORD(); hwnd = foreground()
            if hwnd: window_pid(hwnd, C.byref(pid))
            if pid.value == process.dwProcessId:
                receipt['foreground_child_observed'] = True
                raise RuntimeError('Owned test unexpectedly became foreground')
            time.sleep(.02)
        code = W.DWORD(); require(exit_code(process.hProcess, C.byref(code)), 'Read private test exit')
        if receipt.get('monitor_error'): raise RuntimeError(receipt['monitor_error'])
        receipt['exit'] = code.value
        if code.value == 0 and '--headless' not in args and not receipt['child_desktop_confirmed']:
            raise RuntimeError('No owned graphical window was verified on the private desktop')
    except BaseException as error:
        receipt['error'] = str(error)
        if process.hProcess: terminate(process.hProcess, 2); wait(process.hProcess, 5000)
        receipt['exit'] = 2
    finally:
        stop_monitor.set()
        if monitor: monitor.join(2)
        # Closing this non-inherited job also terminates any remaining children.
        if job: receipt['job_closed'] = bool(close_handle(job))
        if process.hThread: close_handle(process.hThread)
        if process.hProcess: close_handle(process.hProcess)
        for handle in duplicates: close_handle(handle)
        if nul and nul != C.c_void_p(-1).value: close_handle(nul)
        if desktop: receipt['desktop_closed'] = bool(close_desktop(desktop))
        if monitor and monitor.is_alive() or job and not receipt.get('job_closed') or desktop and not receipt.get('desktop_closed'):
            receipt['error'] = 'Private test cleanup did not complete'; receipt['exit'] = 2
        receipt['seconds'] = round(time.monotonic() - start, 3)
        path = Path(receipt_path); path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp'); temporary.write_text(json.dumps(receipt, indent=2), encoding='utf-8'); os.replace(temporary, path)
    return receipt['exit']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--receipt', required=True); parser.add_argument('--timeout', type=float, default=300); parser.add_argument('--cancel-file'); parser.add_argument('--memory-limit-mib',type=int,default=0); parser.add_argument('command', nargs=argparse.REMAINDER)
    options = parser.parse_args(); command = options.command
    if command and command[0] == '--': command = command[1:]
    if not command: parser.error('Missing owned test command')
    raise SystemExit(run_private(command, options.receipt, options.timeout, options.cancel_file, options.memory_limit_mib))
