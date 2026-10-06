import json
import time
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rcl_interfaces.msg import ParameterDescriptor, FloatingPointRange, SetParametersResult
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
import numpy as np
from scipy.spatial.transform import Rotation as R
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

from pyMT4.mtc import MTC
from pyMT4.structure import mtFrameType, mtDecimation, mtBitDepth


class MT4Publisher(Node):
    def __init__(self):
        super().__init__('mt4_publisher')

        self.camera = None
        try:
            # Declare parameters
            self.declare_parameter('ref_frame', '')
            modes = {}
            for parameter, enum, default in (
                    ('frame_type', mtFrameType, 'Full'),
                    ('decimation', mtDecimation, 'Dec11'),
                    ('bit_depth', mtBitDepth, 'Bpp12')):
                self.declare_parameter(parameter, default)
                value = self.get_parameter(parameter).value
                choices = {member.name: member for member in enum if member.value != 0}
                if value not in choices:
                    raise ValueError(f'{parameter} must be one of {", ".join(choices)}; got {value!r}')
                modes[parameter] = choices[value]
            self.declare_parameter('tracking_diagnostics', False)
            self.tracking_diagnostics = self.get_parameter('tracking_diagnostics').value
            self.tracking_status = self.create_publisher(String, '~/tracking_status', 10)
            self._seen_markers = set()
            self._previous_frame_time = None
            self.declare_parameter('publish_images', True)
            self.declare_parameter('jpeg_quality', 90)
            self.jpeg_quality = self.get_parameter('jpeg_quality').value
            if not 1 <= self.jpeg_quality <= 100:
                raise ValueError('jpeg_quality must be between 1 and 100')

            # Get parameter values
            ref_frame_param = self.get_parameter('ref_frame').get_parameter_value().string_value
            self.ref_frame = ref_frame_param if ref_frame_param else None

            self.camera = MTC()
            self.parent_frame = 'MT4'

            self.camera.set_streaming_mode(**modes)
            self.get_logger().info(
                'Camera mode: ' + ', '.join(f'{key}={value.name}' for key, value in modes.items()))

            minimum, maximum = self.camera.get_exposure_range()
            self.declare_parameter('auto_exposure', True)
            self.declare_parameter('exposure', self.camera.get_exposure(),
                ParameterDescriptor(
                    description='Manual SDK exposure: gain times shutter milliseconds; applied when auto_exposure is false',
                    floating_point_range=[FloatingPointRange(from_value=minimum, to_value=maximum, step=0.0)]))
            self.camera.set_exposure_mode(
                self.get_parameter('auto_exposure').value,
                self.get_parameter('exposure').value)
            self.add_on_set_parameters_callback(self._update_exposure)

            # Set the reference frame if provided
            if self.ref_frame is not None:
                self.camera.set_reference_marker(self.ref_frame)

            # Initialize the transform broadcaster
            self.tf_broadcaster = TransformBroadcaster(self)
            self.image_publishers = {}
            if self.get_parameter('publish_images').value:
                for side in ('left', 'right'):
                    self.image_publishers[side] = self.create_publisher(
                        CompressedImage, f'~/camera/{side}/image_raw/compressed', qos_profile_sensor_data)

            self.get_logger().info('MT4 Publisher node started, publishing transforms to /tf')
        except Exception:
            self.destroy_node()
            raise

    def _update_exposure(self, parameters):
        changes = {parameter.name: parameter.value for parameter in parameters}
        if not {'auto_exposure', 'exposure'} & changes.keys():
            return SetParametersResult(successful=True)
        old_auto = self.get_parameter('auto_exposure').value
        old_exposure = self.get_parameter('exposure').value
        auto = changes.get('auto_exposure', old_auto)
        exposure = changes.get('exposure', old_exposure)
        if not isinstance(auto, bool) or not isinstance(exposure, float):
            return SetParametersResult(successful=False, reason='auto_exposure must be bool and exposure must be float')
        try:
            self.camera.set_exposure_mode(auto, exposure)
        except (RuntimeError, ValueError) as error:
            try:
                self.camera.set_exposure_mode(old_auto, old_exposure)
            except (RuntimeError, ValueError) as rollback_error:
                self.get_logger().error(f'Exposure rollback failed: {rollback_error}')
            return SetParametersResult(successful=False, reason=str(error))
        return SetParametersResult(successful=True)

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
            stamp = self.get_clock().now().to_msg()
            now = time.perf_counter()
            if self.tracking_diagnostics:
                self._seen_markers.update(markers)
                status = dict(self.camera.last_frame_timings)
                status['markers'] = list(markers)
                status['missing_markers'] = sorted(self._seen_markers - markers.keys())
                status['interval_ms'] = None if self._previous_frame_time is None else (now - self._previous_frame_time) * 1000
                self.tracking_status.publish(String(data=json.dumps(status)))
            self._previous_frame_time = now
            transforms = []
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
                        rotation_quaternion, stamp)
                elif child_frame == self.ref_frame:
                    continue  # Skip the reference frame itself
                else:
                    transform = self.pos_rot_to_stamped(
                        self.ref_frame,
                        child_frame,
                        position,
                        rotation_quaternion, stamp)

                # Send the transform
                transforms.append(transform)
            if transforms:
                self.tf_broadcaster.sendTransform(transforms)

            if self.image_publishers:
                try:
                    images = self.camera.get_rgb_images()
                    for (side, publisher), image in zip(self.image_publishers.items(), images):
                        success, encoded = cv2.imencode(
                            '.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                            [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                        if not success:
                            raise RuntimeError(f'JPEG encoding failed for {side} image')
                        message = CompressedImage()
                        message.header.stamp = stamp
                        message.header.frame_id = f'MT4_{side}_optical_frame'
                        message.format = 'rgb8; jpeg compressed bgr8'
                        message.data = encoded.tobytes()
                        publisher.publish(message)
                except RuntimeError as error:
                    self.get_logger().error(f'Error publishing images: {error}', throttle_duration_sec=5.0)

        except Exception as e:
            self.get_logger().error(f'Error publishing transforms: {str(e)}')

    def pos_rot_to_stamped(self,
                           parent_frame: str,
                           child_frame: str,
                           position: np.ndarray,
                           rotation: np.ndarray, stamp=None) -> TransformStamped:
        """Convert position and rotation to TransformStamped message"""
        # Get the current time for the transform
        current_time = stamp if stamp is not None else self.get_clock().now().to_msg()

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
