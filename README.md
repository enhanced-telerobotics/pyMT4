# pyMT4

`pyMT4` provides basic functions to interact with the MicronTracker 4 library using a more Python-friendly approach. This package serves as a bridge between Python and the MicronTracker 4 C++ library, making it easier to integrate MicronTracker functionalities into Python projects.

## Getting Started

### Requirements

- This package requires the dynamic library from the MicronTracker 4 official installation.
- The default library path is determined based on the registry key settings. 
- Currently, the package supports Windows only.

### Installation

You can install `pyMT4` directly from the GitHub repository using pip:

```bash
pip install git+https://github.com/enhanced-telerobotics/pyMT4.git
```

Alternatively, you can install it locally in editable mode by navigating to the directory containing `pyMT4` and running:

```bash
cd /path/to/pyMT4
pip install -e .
```

### Usage

To use the `pyMT4` package, simply import the `MTC` class from the package:

```python
from pyMT4 import MTC

# Example usage
mtc = MTC()
mtc.get_poses()
```

Tips: 
- Marker template registration has to be done separately by the C# demo. 
- Check camera connection and image frame before using this package. 

### HTTP server

Install the optional server dependencies and start the server:

```powershell
python -m pip install -e ".[server]"
python -m pyMT4.server --host 0.0.0.0 --port 18080
```

The installed `pymt4-server` command and `python run_server.py` also start the server.
The default address is `0.0.0.0:18080`; use `--host 127.0.0.1` for local access.
Run one server process per tracker. The server uses Waitress, initializes the
device once, serializes device access, and closes it when stopped with Ctrl+C.
Use `--warmup-frames 10` to configure startup frame acquisition.

```powershell
curl.exe "http://localhost:18080/api/get_pose?rot=true"
```

`GET /api/get_pose` returns marker names mapped to pose data, with NumPy arrays
converted to JSON arrays. `rot` defaults to `false`; use `true` to include
rotation matrices. Invalid `rot` values return HTTP 400. Acquisition failures
return HTTP 503 and are logged on the server. Responses disable caching.
The endpoint has no authentication or TLS and is intended for a trusted network.

### Features

- Pythonic interface to the MicronTracker 4 library.
- Simplifies the use of MicronTracker functionalities in Python applications.
- Automatically locates the dynamic library based on system registry settings.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Support

For any issues, please open an issue on the [GitHub repository](https://github.com/enhanced-telerobotics/pyMT4/issues).
