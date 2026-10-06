# pyMT4

Python bindings for the MicronTracker 4 SDK on Windows and Linux.

## Installation

Install the official MicronTracker SDK first, then install this package:

```bash
pip install .
```

On Linux, the `mtc` deb package installs `libMTC.so` in `/usr/lib` and
`/usr/local/lib`. The SDK data directory defaults to
`/etc/Claronav/MicronTracker4` when `MTHome` is unset. On Windows, `MTHome`
is read from the system environment registry and the library is loaded from
`Dist64MT4/mtc.dll` within that directory.

For the Linux installation, place the camera's `.calib` files in:

```text
/etc/Claronav/MicronTracker4/CalibrationFiles/
```

Place your registered marker template files in:

```text
/etc/Claronav/MicronTracker4/Markers/
```

Create these directories if necessary. Marker registration must be performed
separately using the SDK demo. Templates must match the physical markers.
After the installer adds your user to `microntrackerusb`, log out and back in
(or reboot) so camera access uses the new group membership. Reboot to apply
any USB memory setting installed in GRUB.

## Linux SDK 4.2.2 dependencies

This SDK's `libMTC.so` omits dependency metadata for GenICam, Jadak, and
ZXing. The wrapper preloads the bundled shared libraries. The deb supplies
ZXing only as a static archive. On Linux, `pip install .` automatically
builds its shared companion and installs it inside the installed Python
package. No `.so` file is needed in the source checkout.

Install the official Linux SDK and `g++` before installing this package.
The build searches `/usr/lib/libZXing.a` and `/usr/local/lib/libZXing.a`.
For custom installations:

```bash
PYMT4_ZXING_ARCHIVE=/path/to/libZXing.a CXX=g++ pip install .
```

Use a regular installation rather than `pip install -e .`; editable Linux
installation is rejected because it would require generated native files in
the checkout. When running from the repo directory, the wrapper can also locate the
companion in the pip-installed package. Reinstall with
`pip install --force-reinstall --no-deps --no-cache-dir .` after replacing
the SDK. Built Linux wheels contain SDK-specific native code; use them on
machines with a matching architecture and SDK.

## Usage

```python
from pyMT4 import MTC

mtc = MTC()
poses = mtc.get_poses()
```

The camera must be connected and its calibration files available. You can
also select custom directories and an explicit shared library:

```python
mtc = MTC(
    mt_home="/etc/Claronav/MicronTracker4",
    library_path="/usr/lib/libMTC.so",
    calibration_dir="/path/to/CalibrationFiles",
    marker_dir="/path/to/Markers",
    cam_index=0,
)
```

`library_path`, `calibration_dir`, and `marker_dir` are optional. By default,
calibration and templates are loaded from `CalibrationFiles` and `Markers`
under `mt_home`. Linux library discovery uses the system loader, then the
installed library paths and the older `Dist64MT4` layout.

## Tests

Run the configuration tests without a connected camera:

```bash
python -m unittest discover -s tests
```

## License and support

[MIT License](LICENSE). Report issues on
[GitHub](https://github.com/enhanced-telerobotics/pyMT4/issues).
