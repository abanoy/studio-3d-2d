"""Read-only WinAPI process/desktop identity. Creates no desktop or window."""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
import hashlib
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True


class FileTime(C.Structure):
    _fields_ = [("low", W.DWORD), ("high", W.DWORD)]


class ProcessEntry(C.Structure):
    _fields_ = [("dwSize", W.DWORD), ("cntUsage", W.DWORD), ("th32ProcessID", W.DWORD),
                ("th32DefaultHeapID", C.c_size_t), ("th32ModuleID", W.DWORD), ("cntThreads", W.DWORD),
                ("th32ParentProcessID", W.DWORD), ("pcPriClassBase", W.LONG), ("dwFlags", W.DWORD),
                ("szExeFile", W.WCHAR * 260)]


def api(library, name, result, *arguments):
    function = getattr(library, name)
    function.restype, function.argtypes = result, arguments
    return function


def require(ok, message):
    if not ok:
        raise OSError(C.get_last_error(), message)


def libraries():
    if os.name != "nt":
        raise RuntimeError("Desktop attestation requires Windows")
    return C.WinDLL("kernel32", use_last_error=True), C.WinDLL("user32", use_last_error=True)


def ticks(value):
    return (int(value.high) << 32) | int(value.low)


def system_filetime():
    kernel, _ = libraries()
    function = api(kernel, "GetSystemTimeAsFileTime", None, C.POINTER(FileTime))
    value = FileTime(); function(C.byref(value))
    return ticks(value)


def process_creation(pid):
    kernel, _ = libraries()
    open_process = api(kernel, "OpenProcess", W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
    close = api(kernel, "CloseHandle", W.BOOL, W.HANDLE)
    times = api(kernel, "GetProcessTimes", W.BOOL, W.HANDLE, *([C.POINTER(FileTime)] * 4))
    handle = open_process(0x1000, False, int(pid))  # Query-limited-information only.
    require(handle, "Open process for creation-time observation")
    try:
        created, exited, kernel_time, user_time = FileTime(), FileTime(), FileTime(), FileTime()
        require(times(handle, C.byref(created), C.byref(exited), C.byref(kernel_time), C.byref(user_time)), "Read process creation time")
        return ticks(created)
    finally:
        require(close(handle), "Close creation-time query handle")


def parent_pid(pid):
    kernel, _ = libraries()
    snapshot = api(kernel, "CreateToolhelp32Snapshot", W.HANDLE, W.DWORD, W.DWORD)
    first = api(kernel, "Process32FirstW", W.BOOL, W.HANDLE, C.POINTER(ProcessEntry))
    next_entry = api(kernel, "Process32NextW", W.BOOL, W.HANDLE, C.POINTER(ProcessEntry))
    close = api(kernel, "CloseHandle", W.BOOL, W.HANDLE)
    handle = snapshot(2, 0)  # Process IDs/ancestry only, not command lines/modules.
    require(handle and handle != C.c_void_p(-1).value, "Read process ancestry snapshot")
    try:
        entry = ProcessEntry(); entry.dwSize = C.sizeof(entry)
        ok = first(handle, C.byref(entry)); count = 0
        while ok:
            count += 1
            if count > 65536:
                raise RuntimeError("Process ancestry snapshot exceeds budget")
            if entry.th32ProcessID == pid:
                return int(entry.th32ParentProcessID)
            ok = next_entry(handle, C.byref(entry))
        raise RuntimeError("Own process absent from ancestry snapshot")
    finally:
        require(close(handle), "Close ancestry snapshot handle")


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def capture_self():
    kernel, user = libraries()
    pid = int(api(kernel, "GetCurrentProcessId", W.DWORD)())
    thread = int(api(kernel, "GetCurrentThreadId", W.DWORD)())
    desktop = api(user, "GetThreadDesktop", W.HANDLE, W.DWORD)(thread)
    station = api(user, "GetProcessWindowStation", W.HANDLE)()
    info = api(user, "GetUserObjectInformationW", W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD))
    def name(handle):
        require(handle, "Observe own desktop/window-station handle")
        buffer, needed = C.create_unicode_buffer(512), W.DWORD()
        require(info(handle, 2, buffer, C.sizeof(buffer), C.byref(needed)), "Read own user-object name")
        require(bool(buffer.value) and needed.value <= C.sizeof(buffer), "Invalid own user-object name")
        return buffer.value
    executable = C.create_unicode_buffer(32768)
    count = api(kernel, "GetModuleFileNameW", W.DWORD, W.HMODULE, W.LPWSTR, W.DWORD)(None, executable, len(executable))
    require(0 < count < len(executable), "Read own executable path")
    parent = parent_pid(pid)
    # Desktop/station handles are borrowed: never close or switch them.
    return {"api": "WinAPI self observation", "pid": pid, "thread_id": thread, "parent_pid": parent,
            "creation_filetime": process_creation(pid), "parent_creation_filetime": process_creation(parent),
            "observed_filetime": system_filetime(), "desktop": name(desktop), "window_station": name(station),
            "executable": executable.value, "executable_sha256": file_sha(executable.value),
            "observation_created_windows": False, "observation_switched_desktop": False,
            "observation_scope": "Current thread desktop and process window station; prior windows/other threads are not enumerated."}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-probe-output", type=Path, required=True)
    options = parser.parse_args()
    # This explicit probe is observation only and is not private-placement proof.
    from stage_resources import TASK, no_reparse, save
    target = options.self_probe_output.absolute()
    no_reparse(target)
    if target.parent != TASK or target.exists():
        parser.error("Choose a fresh direct output file under the owned task folder")
    result = {"format": "has_readonly_own_desktop_probe_1", "self_probe_only": True,
              "private_desktop_or_blender_launched": False, "observer_source_sha256": file_sha(Path(__file__)),
              "observation": capture_self()}
    save(target, result)
    print(json.dumps(result), flush=True)
