# Shapes window and pose handles

Select a model and open **Shapes / expressions…** to edit its retained shape controls.
Drag a window edge or corner to resize it. The shape list grows with the window;
filtering, selection, preview and Apply/reset commands remain available. Advanced
controls can scroll in a short window, and Close remains accessible.

Studio remembers the resized Shapes window during the current session. If the main
window becomes smaller, Shapes fits into the available space; reopening it after
enlarging the main window restores the remembered size. Resizing it again replaces
that session preference. Restarting Studio uses the initial size again.

Open **Settings → Pose handle size** to choose **75%, 100%, 125%, 150% or 200%**.
The default is **150%**. This personal setting changes both the visible rotation
handles and their grabbing area. It is saved separately from Interface scale, so
changing interface size keeps the chosen handle size consistent in screen pixels.
It does not resize the model or change the camera or movie resolution.

Large handles can cross the edge of a small view. The visible arc remains usable;
parts clipped outside the scene cannot start a drag. Choose a smaller handle size
or give the scene more room when needed.

See [camera and timeline gestures](camera_interactions.md) for camera keys and lens
controls. The shape Amount field keeps its existing raw units and saved values.
The handle percentage does not convert existing shape keys.
