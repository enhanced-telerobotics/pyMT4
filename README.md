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

## ROS 2 usage

This branch includes the `tf_publisher` node and ament package registration.
With ROS 2 installed and sourced, build in your ROS workspace using a regular
colcon build (omit `--symlink-install`):

```bash
colcon build --packages-select pyMT4
source install/setup.bash
ros2 run pyMT4 tf_publisher
```

To select a reference marker:

```bash
ros2 run pyMT4 tf_publisher --ros-args -p ref_frame:=BreadBoard
```

The ROS Python environment also needs NumPy and SciPy. Both pip and regular
colcon builds generate the ZXing companion automatically on Linux; the
MicronTracker SDK and C++ compiler must be installed before building.

## Tests

Run the configuration tests without a connected camera:

```bash
python -m unittest discover -s tests
```

## License and support

[MIT License](LICENSE). Report issues on
[GitHub](https://github.com/enhanced-telerobotics/pyMT4/issues).

## Compressed stereo images in ROS 2

Run the publisher:

```bash
ros2 run pyMT4 tf_publisher
```

OpenCV encodes each stereo frame as JPEG and publishes
`sensor_msgs/CompressedImage` using sensor-data QoS on:

- `/mt4_publisher/camera/left/image_raw/compressed`
- `/mt4_publisher/camera/right/image_raw/compressed`

Images share the acquisition timestamp with pose transforms, and publish even
without markers. The camera controls cadence; no rate timer is added.
Image sizes follow camera decimation. The connected MT4 supplies monochrome
pixels replicated across RGB channels. Optical frame IDs are
`MT4_left_optical_frame` and `MT4_right_optical_frame`; calibrated optical
transforms and CameraInfo are not provided.

JPEG quality defaults to 90 (range 1–100):

```bash
ros2 run pyMT4 tf_publisher --ros-args -p jpeg_quality:=80
# Disable images:
ros2 run pyMT4 tf_publisher --ros-args -p publish_images:=false
```

ROS requires `python3-opencv`. For a separate pip environment, install
`opencv-python` alongside the ROS Python dependencies.
The SDK API `camera.get_rgb_images()` returns owned stereo RGB NumPy arrays
after `get_poses()` acquires a frame. It does not grab a second frame.

## Camera streaming mode

The ROS node defaults to `Full`, `Dec11` (1:1), and `Bpp12`.
Set the SDK mode at startup using named ROS parameters:

```bash
ros2 run pyMT4 tf_publisher --ros-args \
  -p frame_type:=Full -p decimation:=Dec11 -p bit_depth:=Bpp12
# Example: alternating frames at 4:1 decimation
ros2 run pyMT4 tf_publisher --ros-args \
  -p frame_type:=Alternating -p decimation:=Dec41 -p bit_depth:=Bpp12
```

Supported values: `frame_type` = `Full`, `ROIs`, `Alternating`;
`decimation` = `Dec11`, `Dec21`, `Dec41`;
`bit_depth` = `Bpp12`, `Bpp14`. Names are case-sensitive.
ROI-only mode may not provide images; use `publish_images:=false` when
selecting it. These are startup settings, not dynamic mode changes.

## Dynamic exposure

Automatic exposure remains the default. For manual control:

```bash
ros2 run pyMT4 tf_publisher --ros-args -p auto_exposure:=false -p exposure:=5.0
```

`exposure` is the SDK gain × shutter-milliseconds value, not shutter time
alone. Its allowed range is queried from the camera and shown in the ROS
parameter descriptor. Use floating-point values such as `5.0`.

While the node is running, open `rqt`, select **Plugins → Configuration →
Dynamic Reconfigure**, and select `/mt4_publisher`. Turn `auto_exposure` off
and adjust `exposure`. ROS 2 `rqt_reconfigure` edits the node parameters;
no restart is required. Changes to `exposure` while auto is enabled select
the value to use when switching to manual.

Equivalent terminal controls:

```bash
ros2 param set /mt4_publisher auto_exposure false
ros2 param set /mt4_publisher exposure 5.0
ros2 param set /mt4_publisher auto_exposure true
```

Manual mode disables camera, marker, and XPoint automatic exposure controls.
Automatic mode enables them again. SDK errors reject parameter updates.

## Camera launch preset

```bash
ros2 launch pyMT4 mt4.launch.py
```

Defaults: `Alternating`, `Dec41`, `Bpp12`, images enabled, manual exposure
with `exposure=5.0`. This launch preset overrides the node's automatic-exposure
default. Override any setting with launch arguments:

```bash
ros2 launch pyMT4 mt4.launch.py auto_exposure:=true
ros2 launch pyMT4 mt4.launch.py exposure:=3.0 publish_images:=false
```

`ref_frame`, `jpeg_quality`, and `tracking_diagnostics` are also exposed.
Exposure parameters remain adjustable through rqt while running.
