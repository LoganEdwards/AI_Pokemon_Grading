import sys
import os

# ---------- Helper to get resource path for executable ----------
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller exe"""
    try:
        base_path = sys._MEIPASS  # PyInstaller temporary folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
