import rclpy
from rclpy.node import Node
import numpy as np
from scipy.spatial.transform import Rotation as R
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

from pyMT4.mtc import MTC


class MT4Publisher(Node):
    def __init__(self):
        super().__init__('mt4_publisher')

        self.camera = None
        try:
            # Declare parameters
            self.declare_parameter('ref_frame', '')

            # Get parameter values
            ref_frame_param = self.get_parameter('ref_frame').get_parameter_value().string_value
            self.ref_frame = ref_frame_param if ref_frame_param else None

            self.camera = MTC()
            self.parent_frame = 'MT4'

            # Use the camera default mode; SDK-specific ROI modes are not forced.

            # Set the reference frame if provided
            if self.ref_frame is not None:
                self.camera.set_reference_marker(self.ref_frame)

            # Initialize the transform broadcaster
            self.tf_broadcaster = TransformBroadcaster(self)

            self.get_logger().info('MT4 Publisher node started, publishing transforms to /tf')
        except Exception:
            self.destroy_node()
            raise

    def destroy_node(self):
        try:
            if self.camera is not None:
                self.camera.close()
                self.camera = None
        finally:
            super().destroy_node()

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

                # Format the message
                # If the ref_frame is specified, use it as the parent frame
                # otherwise use the camera as the parent frame
                if self.ref_frame is None:
                    transform = self.pos_rot_to_stamped(
                        self.parent_frame,
                        child_frame,
                        position,
                        rotation_quaternion)
                elif child_frame == self.ref_frame:
                    continue  # Skip the reference frame itself
                else:
                    transform = self.pos_rot_to_stamped(
                        self.ref_frame,
                        child_frame,
                        position,
                        rotation_quaternion)

                # Send the transform
                self.tf_broadcaster.sendTransform(transform)

        except Exception as e:
            self.get_logger().error(f'Error publishing transforms: {str(e)}')

    def pos_rot_to_stamped(self,
                           parent_frame: str,
                           child_frame: str,
                           position: np.ndarray,
                           rotation: np.ndarray) -> TransformStamped:
        """Convert position and rotation to TransformStamped message"""
        # Get the current time for the transform
        current_time = self.get_clock().now().to_msg()

        # Create transform message
        transform = TransformStamped()
        transform.header.stamp = current_time
        transform.header.frame_id = parent_frame
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


def main():
    mt4_publisher = None
    rclpy.init()
    try:
        mt4_publisher = MT4Publisher()
        while rclpy.ok():
            rclpy.spin_once(mt4_publisher, timeout_sec=0.0)
            if rclpy.ok():
                # Camera acquisition determines the cadence; publish each available pose.
                mt4_publisher.publish_transforms()
    except KeyboardInterrupt:
        if mt4_publisher is not None and rclpy.ok():
            mt4_publisher.get_logger().info('Shutting down MT4 Publisher...')
    finally:
        try:
            if mt4_publisher is not None:
                mt4_publisher.destroy_node()
        finally:
            rclpy.try_shutdown()


if __name__ == '__main__':
    main()
