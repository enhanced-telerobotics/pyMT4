"""Start stereo tracking with configurable camera and exposure settings."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    settings = (
        ('frame_type', 'Alternating', str),
        ('decimation', 'Dec41', str),
        ('bit_depth', 'Bpp12', str),
        ('publish_images', 'true', bool),
        ('auto_exposure', 'false', bool),
        ('exposure', '5.0', float),
        ('ref_frame', '', str),
        ('jpeg_quality', '90', int),
        ('tracking_diagnostics', 'false', bool),
    )
    arguments = [DeclareLaunchArgument(name, default_value=default)
                 for name, default, _ in settings]
    parameters = {name: ParameterValue(LaunchConfiguration(name), value_type=value_type)
                  for name, _, value_type in settings}
    return LaunchDescription(arguments + [
        Node(package='pyMT4', executable='tf_publisher', name='mt4_publisher',
             parameters=[parameters], output='screen'),
    ])
