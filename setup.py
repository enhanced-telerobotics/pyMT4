from setuptools import setup, find_packages

VERSION = "0.1.1"
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
        'scipy'
    ],
    extras_require={'server': ['Flask>=2.2', 'waitress>=3.0.2']},
    entry_points={'console_scripts': ['pymt4-server=pyMT4.server:main']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.8',
)
