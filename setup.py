from setuptools import find_packages, setup

package_name = 'pyMT4'

setup(
    name=package_name,
    version='0.1.2',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'numpy',
        'scipy',
    ],
    zip_safe=True,
    author='Shuyuan Yang',
    author_email='sxy841@case.edu',
    url='https://github.com/enhanced-telerobotics/pyMT4',
    license='MIT',
    description='Python binding for MicronTracker 4',
    entry_points={
        'console_scripts': [
            'tf_publisher = pyMT4.tf_publisher:main',
        ],
    },
)
