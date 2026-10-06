import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import Distribution, setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.editable_wheel import editable_wheel
from setuptools.errors import CompileError


class SDKEditableWheel(editable_wheel):
    def run(self):
        if sys.platform == 'linux':
            raise CompileError("Linux SDK libraries require a regular installation. "
                               "Run python -m pip install . without -e.")
        super().run()


class SDKDistribution(Distribution):
    def has_ext_modules(self):
        # The generated companion is native code: never emit a universal wheel.
        return sys.platform == "linux"


class BuildSDK(build_py):
    def run(self):
        if sys.platform == "linux" and self.editable_mode:
            raise CompileError("Use pip install . instead of pip install -e . "
                               "to install SDK libraries outside the source checkout.")
        super().run()
        if sys.platform != "linux":
            return
        archive_override = os.environ.get("PYMT4_ZXING_ARCHIVE")
        candidates = [Path(archive_override)] if archive_override else [
            Path('/usr/lib/libZXing.a'), Path('/usr/local/lib/libZXing.a')]
        archive = next((path for path in candidates if path.is_file()), None)
        if archive is None:
            raise CompileError("MicronTracker libZXing.a not found. Install the Linux SDK "
                               "first or set PYMT4_ZXING_ARCHIVE to its archive path.")
        compiler = shlex.split(os.environ.get('CXX', 'g++'))
        if not compiler or not shutil.which(compiler[0]):
            raise CompileError("A C++ compiler is required; install g++ or set CXX.")
        output = Path(self.build_lib) / 'pyMT4' / 'libZXing.so'
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(compiler + ['-shared', '-o', str(output),
                           '-Wl,--whole-archive', str(archive),
                           '-Wl,--no-whole-archive'], check=True)
        except (OSError, subprocess.CalledProcessError) as error:
            raise CompileError(f"Could not build the ZXing SDK companion: {error}") from error

    def get_outputs(self, include_bytecode=1):
        outputs = super().get_outputs(include_bytecode)
        if sys.platform == "linux":
            outputs.append(os.path.join(self.build_lib, 'pyMT4', 'libZXing.so'))
        return outputs


VERSION = "0.1.2"
DESCRIPTION = "Python binding for MicronTracker 4"

setup(
    name='pyMT4',
    version=VERSION,
    description=DESCRIPTION,
    long_description=Path(__file__).with_name('README.md').read_text(),
    long_description_content_type='text/markdown',
    author='Shuyuan Yang',
    author_email='sxy841@case.edu',
    url='https://github.com/enhanced-telerobotics/pyMT4',
    license='MIT',
    packages=find_packages(),
    cmdclass={'build_py': BuildSDK, 'editable_wheel': SDKEditableWheel},
    distclass=SDKDistribution,
    install_requires=[
        'numpy',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.8',
)
