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

### Features

- Pythonic interface to the MicronTracker 4 library.
- Simplifies the use of MicronTracker functionalities in Python applications.
- Automatically locates the dynamic library based on system registry settings.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Support

For any issues, please open an issue on the [GitHub repository](https://github.com/enhanced-telerobotics/pyMT4/issues).
