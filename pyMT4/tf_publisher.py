import rclpy
import argparse
from rclpy.node import Node
import numpy as np
from scipy.spatial.transform import Rotation as R
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

from pyMT4.mtc import MTC


class MT4Publisher(Node):
    def __init__(self, publish_rate=30.0):
        super().__init__('mt4_publisher')

        self.camera = MTC()
        self.parent_frame = 'MT4'

        # Initialize the transform broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Create a timer to publish transforms at a regular rate (e.g., 30 Hz)
        self.timer = self.create_timer(
            1.0/publish_rate, self.publish_transforms)

        self.get_logger().info('MT4 Publisher node started, publishing transforms to /tf')

    def publish_transforms(self):
        """Publish transforms for all detected markers"""
        try:
            markers = self.camera.get_poses(rot=True)

            if not markers:
                self.get_logger().debug('No markers detected')
                return

            for child_frame, pose in markers.items():
                # Convert from mm to m
                position = pose['pos'] / 1000
                # Convert rotation matrix to quaternion
                rotation = pose['rot']
                rotation_quaternion = R.from_matrix(rotation).as_quat()

                # Broadcast the transform
                transform = self.pos_rot_to_stamped(
                    child_frame, position, rotation_quaternion)

                # Send the transform
                self.tf_broadcaster.sendTransform(transform)

        except Exception as e:
            self.get_logger().error(f'Error publishing transforms: {str(e)}')

    def pos_rot_to_stamped(self,
                           child_frame: str,
                           position: np.ndarray,
                           rotation: np.ndarray) -> TransformStamped:
        """Convert position and rotation to TransformStamped message"""
        # Get the current time for the transform
        current_time = self.get_clock().now().to_msg()

        # Create transform message
        transform = TransformStamped()
        transform.header.stamp = current_time
        transform.header.frame_id = self.parent_frame
        transform.child_frame_id = child_frame

        # Set translation
        transform.transform.translation.x = float(position[0])
        transform.transform.translation.y = float(position[1])
        transform.transform.translation.z = float(position[2])

        # Set rotation (scipy returns quaternion as [x, y, z, w])
        transform.transform.rotation.x = float(rotation[0])
        transform.transform.rotation.y = float(rotation[1])
        transform.transform.rotation.z = float(rotation[2])
        transform.transform.rotation.w = float(rotation[3])

        return transform


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MT4 Publisher Node')
    parser.add_argument('-p', '--publish-rate', type=float, default=30.0,
                        help='Rate at which to publish transforms (Hz)')
    args = parser.parse_args()

    try:
        rclpy.init()
        mt4_publisher = MT4Publisher(args.publish_rate)
        rclpy.spin(mt4_publisher)
    except KeyboardInterrupt:
        mt4_publisher.get_logger().info('Shutting down MT4 Publisher...')
    finally:
        mt4_publisher.destroy_node()
        rclpy.shutdown()
