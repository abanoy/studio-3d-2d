"""Pixel layout boundary between decoded Source VTFs and Blender images."""


def blender_rgba(decoded, width, height):
    """VTF decode rows are top-down; Blender's Image.pixels starts at the bottom.

    Reverse rows once, retaining each pixel's RGBA channels and image columns.
    No change to Source UVs, colors, native files or the shared model contract.
    The decoder supplies a NumPy array inside the isolated Blender worker.
    """
    if decoded.shape != (height, width, 4):
        raise ValueError('Unexpected decoded Source RGBA dimensions')
    return decoded[::-1].copy().ravel()
