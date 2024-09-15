from setuptools import setup, find_packages

VERSION = "0.1.0"
DESCRIPTION = "Python binding for MicronTracker 4"

setup(
    name='pyMT4',
    version=VERSION,
    description=DESCRIPTION,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Shuyuan Yang',
    author_email='sxy841@case.edu',
    url='https://github.com/enhanced-telerobotics/pyMT4',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'numpy',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.8',
)
