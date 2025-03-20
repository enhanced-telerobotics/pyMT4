import warnings
import sys
import os

if sys.platform == "win32":
    # Attempt to read the MTHome path from the registry
    try:
        import winreg

        # Open the registry key where MTHome is expected
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        )

        # Query the value for 'MTHome'
        MTHome, regtype = winreg.QueryValueEx(key, "MTHome")

        # Close the registry key
        winreg.CloseKey(key)

    except FileNotFoundError:
        # Warn if MTHome is not found in the registry
        warnings.warn("MTHome not found in the registry.", RuntimeWarning)
        MTHome = None

    except OSError as e:
        # Warn if there's an error accessing the registry
        warnings.warn(f"Error accessing the registry: {e}", RuntimeWarning)
        MTHome = None
elif sys.platform == "linux":
    MTHome = os.getenv("MTHome")
    if MTHome is None:
        warnings.warn("MTHome environment variable is not set.", RuntimeWarning)
else:
    warnings.warn("This script is designed to run only on Windows or Linux.", RuntimeWarning)
    MTHome = None