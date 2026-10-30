"""test_mutex.py - Unit test for single instance mutex guard."""
import sys

from typing_buddy.winapi import create_single_instance_mutex


def test_single_instance_mutex():
    if not sys.platform.startswith("win"):
        return

    name = "Local\\TypingBuddy_TestMutex_Unique123"
    mutex1, already_running1 = create_single_instance_mutex(name)
    assert already_running1 is False
    assert mutex1 is not None

    # Try creating second mutex with same name
    mutex2, already_running2 = create_single_instance_mutex(name)
    assert already_running2 is True

    # Clean up handles
    import ctypes
    kernel32 = ctypes.windll.kernel32
    if mutex1:
        kernel32.CloseHandle(mutex1)
    if mutex2:
        kernel32.CloseHandle(mutex2)
