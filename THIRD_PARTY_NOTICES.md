# Third-party notices

## Godot Engine 4.6 (external runtime)

Copyright (c) 2014-present Godot Engine contributors.
Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Source: https://godotengine.org/license/. Matching engine dependency notices must
also accompany any future bundled runtime. This source tree does not bundle it.

## Jolt Physics (built into the external runtime)

The external Godot runtime's built-in Jolt Physics is now used for live3D physics.
Copyright2021 Jorrit Rouwe; MIT. Its permission/warranty terms are the MIT terms
reproduced above, with that copyright retained. Exact pinned upstream notice:
https://raw.githubusercontent.com/godotengine/godot/4.6-stable/thirdparty/jolt_physics/LICENSE
No additional Jolt binary/source is bundled here. Future engine packaging must
retain the engine's full dependency notices.

## FFmpeg/ffprobe (external processes)

FFmpeg is copyright its contributors. License and codec options depend on the
separately installed build; tested builds include GPL-enabled libx264. No FFmpeg
executable, DLL or codec library is bundled.
See https://ffmpeg.org/legal.html and the exact installed binary's -L/-buildconf
information before redistribution. This notice does not relicense that binary.

## Python (external interpreter)

Python is copyright the Python Software Foundation and contributors; licensed under
the PSF license and applicable included notices. https://docs.python.org/3/license.html.
No interpreter or third-party Python packages are bundled.

## Optional Blender / MMD Tools preparation (external)

Blender5.1.2: Blender Foundation and contributors, GPL-3.0-or-later plus its included
dependency notices (installed license/license.md). https://www.blender.org/.
MMD Tools4.5.11: MMD & Blender Team, UuuNyaa, powroupi, sugiany and contributors,
GPL-3.0-or-later. https://github.com/MMD-Blender/blender_mmd_tools.
These separately installed tools are used in an isolated preparation process.
No binaries/add-on code/assets are included in this source tree. See docs/licenses.md
before any future distribution of third-party components.


## Optional SourceIO preparation cache

SourceIO5.5.5 revision fe24260b97ac03b899d9b5d4f0fd7b34772f3647,
https://github.com/REDxEYE/SourceIO. Original wrapper uses it in an external
factory-started Blender worker. No SourceIO source/native binaries are committed.
The local progress directory includes its ignored cache with original notices.
Root license follows; included/transitive notices also require review before any
public packaging.

MIT License

Copyright (c) 2020 REDxEYE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
