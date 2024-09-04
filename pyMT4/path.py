import winreg
import warnings

# Attempt to read the MTHome path from the registry
try:
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