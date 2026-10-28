"""Capture only the test application's client area, even if another window covers it."""


def capture(root, path):
    """Use Windows PrintWindow so desktop content never enters the test screenshot."""
    import ctypes
    from ctypes import wintypes
    import struct
    from PIL import Image

    user = ctypes.windll.user32
    gdi = ctypes.windll.gdi32
    handle = ctypes.c_void_p
    user.GetDC.argtypes = [handle]
    user.GetDC.restype = handle
    user.ReleaseDC.argtypes = [handle, handle]
    user.PrintWindow.argtypes = [handle, handle, wintypes.UINT]
    gdi.CreateCompatibleDC.argtypes = [handle]
    gdi.CreateCompatibleDC.restype = handle
    gdi.CreateCompatibleBitmap.argtypes = [handle, ctypes.c_int, ctypes.c_int]
    gdi.CreateCompatibleBitmap.restype = handle
    gdi.SelectObject.argtypes = [handle, handle]
    gdi.SelectObject.restype = handle
    gdi.DeleteObject.argtypes = [handle]
    gdi.DeleteDC.argtypes = [handle]
    gdi.GetDIBits.argtypes = [handle, handle, wintypes.UINT, wintypes.UINT, handle, handle, wintypes.UINT]
    hwnd = root.winfo_id()
    width, height = root.winfo_width(), root.winfo_height()
    dc = user.GetDC(hwnd)
    memory = gdi.CreateCompatibleDC(dc)
    bitmap = gdi.CreateCompatibleBitmap(dc, width, height)
    old = gdi.SelectObject(memory, bitmap)
    try:
        if not user.PrintWindow(hwnd, memory, 3):
            raise RuntimeError('Cannot capture the test window.')
        gdi.SelectObject(memory, old)
        info = ctypes.create_string_buffer(struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 32, 0, width*height*4, 0, 0, 0, 0))
        pixels = ctypes.create_string_buffer(width*height*4)
        if gdi.GetDIBits(memory, bitmap, 0, height, pixels, info, 0) != height:
            raise RuntimeError('Cannot read the test-window bitmap.')
        Image.frombytes('RGB', (width, height), pixels.raw, 'raw', 'BGRX').save(path)
    finally:
        gdi.SelectObject(memory, old)
        gdi.DeleteObject(bitmap)
        gdi.DeleteDC(memory)
        user.ReleaseDC(hwnd, dc)
