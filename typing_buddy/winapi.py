"""winapi.py - Windows Win32 and UI Automation helpers with non-Windows fallbacks."""
import logging
import os
import sys

logger = logging.getLogger("typing_buddy.winapi")

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    import ctypes
    import winreg
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Constants
    WM_KEYDOWN = 0x0100
    WM_SYSKEYDOWN = 0x0104
    LLKHF_INJECTED = 0x10
    GWL_STYLE = -16
    GWL_EXSTYLE = -20
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_NOACTIVATE = 0x08000000
    ES_PASSWORD = 0x0020
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    ERROR_ALREADY_EXISTS = 183
    MONITOR_DEFAULTTONEAREST = 2
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    THREAD_PRIORITY_BELOW_NORMAL = -1

    kernel32.GetCurrentThread.restype = wintypes.HANDLE
    kernel32.SetThreadPriority.argtypes = [wintypes.HANDLE, ctypes.c_int]
    kernel32.SetThreadPriority.restype = wintypes.BOOL

    # Structures
    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    # UI Automation setup (lazy/cached per thread)
    _uia_initialized = False
    _uia_object = None
    _logged_uia_error = False

    def _get_uia():
        global _uia_initialized, _uia_object, _logged_uia_error
        if _uia_object is not None:
            return _uia_object
        try:
            import comtypes.client
            comtypes.CoInitialize()
            UIAutomationClient = comtypes.client.GetModule("UIAutomationCore.dll")
            _uia_object = comtypes.client.CreateObject(
                UIAutomationClient.CUIAutomation,
                interface=UIAutomationClient.IUIAutomation
            )
            return _uia_object
        except Exception as e:
            if not _logged_uia_error:
                logger.warning("UI Automation initialization failed (will use Win32 fallback): %s", e)
                _logged_uia_error = True
            return None


def set_dpi_awareness():
    """Enable per-monitor DPI awareness if on Windows."""
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


def set_current_thread_low_priority():
    """Lower priority of background worker thread (THREAD_PRIORITY_BELOW_NORMAL)."""
    if not IS_WINDOWS:
        return
    try:
        h = kernel32.GetCurrentThread()
        kernel32.SetThreadPriority(h, THREAD_PRIORITY_BELOW_NORMAL)
    except Exception as e:
        logger.debug("Failed to set thread priority: %s", e)


def caret_pos():
    """Screen position under the text caret, or None if the app hides it."""
    if not IS_WINDOWS:
        return None
    try:
        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(info)
        if not user32.GetGUIThreadInfo(0, ctypes.byref(info)) or not info.hwndCaret:
            return None
        pt = wintypes.POINT(info.rcCaret.left, info.rcCaret.bottom)
        user32.ClientToScreen(info.hwndCaret, ctypes.byref(pt))
        return pt.x, pt.y
    except Exception:
        return None


def get_monitor_work_area(x, y):
    """Return (left, top, right, bottom) work area of the monitor containing (x, y)."""
    if not IS_WINDOWS:
        return 0, 0, 1920, 1080
    try:
        pt = wintypes.POINT(int(x), int(y))
        hmon = user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            return info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom
    except Exception:
        pass
    try:
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        return 0, 0, w, h
    except Exception:
        return 0, 0, 1920, 1080


def get_foreground_hwnd():
    if not IS_WINDOWS:
        return 0
    return user32.GetForegroundWindow()


def get_foreground_process_name():
    """Return the executable name (e.g. 'notepad.exe') of current foreground window."""
    if not IS_WINDOWS:
        return None
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None
        hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hproc:
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(hproc)
    except Exception as e:
        logger.debug("Error getting foreground process name: %s", e)
    return None


def get_foreground_window_title():
    """Return the title of current foreground window in lowercase."""
    if not IS_WINDOWS:
        return ""
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value.lower()
    except Exception:
        return ""


def is_password_focused():
    """Check if the currently focused field is a password field.

    Uses UI Automation property IsPassword with a Win32 ES_PASSWORD fallback.
    """
    if not IS_WINDOWS:
        return False

    # 1. Primary method: UI Automation
    uia = _get_uia()
    if uia:
        try:
            elem = uia.GetFocusedElement()
            if elem and bool(elem.CurrentIsPassword):
                return True
        except Exception as e:
            logger.debug("UIA GetFocusedElement error: %s", e)

    # 2. Classic Win32 fallback: GetGUIThreadInfo hwndFocus ES_PASSWORD style
    try:
        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(info)
        if user32.GetGUIThreadInfo(0, ctypes.byref(info)) and info.hwndFocus:
            style = user32.GetWindowLongW(info.hwndFocus, GWL_STYLE)
            if bool(style & ES_PASSWORD):
                return True
    except Exception as e:
        logger.debug("Win32 ES_PASSWORD check error: %s", e)

    return False


def check_sensitive_state(blocked_apps, blocked_title_words):
    """Determine if suggestions should be paused due to password/sensitive context."""
    if not IS_WINDOWS:
        return False, ""

    try:
        if is_password_focused():
            return True, "password_field"

        proc_name = get_foreground_process_name()
        if proc_name and blocked_apps:
            for blocked in blocked_apps:
                if blocked.lower() == proc_name:
                    return True, f"blocked_app:{proc_name}"

        if blocked_title_words:
            title = get_foreground_window_title()
            if title:
                for word in blocked_title_words:
                    if word and word.lower() in title:
                        return True, f"blocked_title:{word}"

    except Exception as e:
        logger.error("Error in check_sensitive_state: %s", e)

    return False, ""


def set_window_no_focus_steal(hwnd):
    """Apply WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST to hwnd."""
    if not IS_WINDOWS:
        return
    try:
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST)
    except Exception as e:
        logger.warning("Failed to set window ex_style: %s", e)


def create_single_instance_mutex(name="Local\\TypingBuddy_SingleInstance_Mutex"):
    """Create a named mutex to ensure single instance. Returns (handle, is_already_running)."""
    if not IS_WINDOWS:
        return None, False
    try:
        mutex = kernel32.CreateMutexW(None, False, name)
        err = kernel32.GetLastError()
        if err == ERROR_ALREADY_EXISTS:
            return mutex, True
        return mutex, False
    except Exception as e:
        logger.warning("Mutex creation error: %s", e)
        return None, False


def clean_legacy_run_registry_entries():
    """Remove any legacy registry Run entries to prevent dual-start."""
    if not IS_WINDOWS:
        return
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    legacy_names = ["Typing Buddy", "Typing Suggest", "TypingSuggest", "WindowsTypingPredictor"]
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            for name in legacy_names:
                try:
                    winreg.DeleteValue(key, name)
                    logger.info("Cleaned legacy Run registry entry: %s", name)
                except FileNotFoundError:
                    pass
    except Exception as e:
        logger.debug("Error cleaning legacy Run registry entries: %s", e)


def get_startup_shortcut_path():
    """Return path to Typing Buddy shortcut in user's Startup folder."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "Typing Buddy.lnk")
    return os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "Typing Buddy.lnk")


def is_start_with_windows_enabled():
    """Check if Startup folder shortcut exists."""
    clean_legacy_run_registry_entries()
    return os.path.exists(get_startup_shortcut_path())


def toggle_start_with_windows(enable):
    """Toggle startup shortcut in Startup folder and ensure registry is clean."""
    clean_legacy_run_registry_entries()
    shortcut_path = get_startup_shortcut_path()
    try:
        if enable:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(project_root, "tools", "create_shortcuts.ps1")
            if os.path.exists(script_path):
                import subprocess
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-Startup"],
                    check=True,
                    capture_output=True,
                    creationflags=flags
                )
                logger.info("Created Startup shortcut via create_shortcuts.ps1")
                return True
        else:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                logger.info("Removed Startup shortcut: %s", shortcut_path)
            # Also check and remove legacy Typing Suggest.lnk
            legacy_lnk = os.path.join(os.path.dirname(shortcut_path), "Typing Suggest.lnk")
            if os.path.exists(legacy_lnk):
                os.remove(legacy_lnk)
            return True
    except Exception as e:
        logger.error("Failed to toggle start with Windows: %s", e)
        return False
    return False


def get_clipboard_text():
    """Retrieve text from Windows clipboard, or None if not text or error."""
    if not IS_WINDOWS:
        return None
    try:
        if not user32.OpenClipboard(0):
            return None
        try:
            h_clip = user32.GetClipboardData(CF_UNICODETEXT)
            if not h_clip:
                return None
            p_text = kernel32.GlobalLock(h_clip)
            if not p_text:
                return None
            val = ctypes.c_wchar_p(p_text).value
            kernel32.GlobalUnlock(h_clip)
            return val
        finally:
            user32.CloseClipboard()
    except Exception as e:
        logger.debug("Error reading clipboard: %s", e)
        return None


def set_clipboard_text(text: str) -> bool:
    """Set text onto Windows clipboard."""
    if not IS_WINDOWS or text is None:
        return False
    try:
        if not user32.OpenClipboard(0):
            return False
        try:
            user32.EmptyClipboard()
            buf = ctypes.create_unicode_buffer(text)
            size = ctypes.sizeof(buf)
            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not h_mem:
                return False
            p_mem = kernel32.GlobalLock(h_mem)
            ctypes.memmove(p_mem, buf, size)
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            return True
        finally:
            user32.CloseClipboard()
    except Exception as e:
        logger.debug("Error setting clipboard: %s", e)
        return False
