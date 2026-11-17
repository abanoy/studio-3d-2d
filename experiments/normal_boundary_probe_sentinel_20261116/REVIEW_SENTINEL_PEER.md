# Hidden placement sentinel: independent source review

**Source GO. No Win32 API, Blender, engine, process inventory or Git operation
was executed by this review. Actual desktop placement remains a root runtime
observation.**

`CreateWindowExW` has the correct twelve-argument signature with pointer-sized
HWND/menu/instance values. The predefined Unicode STATIC class is created with
no parent or menu, zero width/height, WS_POPUP and WS_DISABLED, and the
EX_NOACTIVATE/TOOLWINDOW styles. WS_VISIBLE and WS_CHILD are excluded and checked.
`GetWindowLongW` is correct for the two32-bit style fields on Win64; returned
signed values are normalized to32bits. No ShowWindow, activation, focus or
SetThreadDesktop call exists in the new API inventory.

The retained HWND must belong to the current process and the current creating
thread before use and before destruction. Geometry, visibility, enabled state
and styles are checked. The context manager destroys its owned HWND in a finally
block even if the original capture raises. A missing/reassigned window or failed
cleanup raises and therefore remains a failed process. Placement policy is
appended to the public capture only after successful context cleanup.

The unchanged outer private-desktop tool still provides the placement evidence:
it enumerates the actual private desktop and matches windows to the launched
child PID. The sentinel does not name or select a desktop, modify that monitor,
add a fake headless flag, or issue an isolation receipt. A missed enumeration or
wrong desktop still fails closed. The receipt's window-observed field means an
owned HWND was observed; it is not evidence of Blender GUI/render operation.
Root must retain exit0, the unchanged outer isolation/closure receipt and the
successful sentinel cleanup policy; the original capture marker alone is not
an isolation pass.

The final wrapper also requires the actual `bpy.app.background` value to be the
boolean True before it enters the window context. Interactive or missing/false
background state therefore fails before any sentinel API executes. The public
background-verified flag is assigned only after successful finally cleanup.

Independent AST/hash checks confirmed all six original capture functions are
identical, all five core analysis/staging files are exact predecessor copies,
the API inventory contains only the ten declared create/check/destroy calls,
cleanup is in finally, and tools/private_desktop.py remains exact to the52f
full-run source manifest. Capture source hash is
07c5d24538b11da7d8f4464b6a1e48dd3bbd6f15525c60c7e5cc4b9619e83576.

No numerical capture, original raw fidelity gate, comparison threshold or source
input was changed or qualified by this source review.
