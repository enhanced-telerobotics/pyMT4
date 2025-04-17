from pyMT4 import MTC
import rclpy
import tf2_ros
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
import numpy as np
import transforms3d.quaternions as tq

operator = 'KW'

class MicronTrackerNode(Node):
    def __init__(self):
        super().__init__(f'{operator}MTnode')
        self.mtc = MTC()
        self.marker_dict = ['gripper_base', 'object']
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.timer = self.create_timer(1.0 / 60.0, self.timer_callback)
        print("Micron Tracker Node Initialized")

    def timer_callback(self):
        mt_data = self.mtc.get_poses()
        if self.marker_dict[0] in mt_data:
            rot = mt_data[self.marker_dict[0]]['rot']
            pose = mt_data[self.marker_dict[0]]['pos']
            pose = - rot.T @ pose
            trans_matrix = np.eye(4)
            trans_matrix[:3,:3] = rot.T
            trans_matrix[:3, 3] = pose
            trans_g_mt = self.get_trans(trans_matrix, f'{operator}gripperbase', f'{operator}MT')
            self.tf_broadcaster.sendTransform([trans_g_mt])
            print('Mt_Gripper Captured')
            
        if self.marker_dict[1] in mt_data:
            rot = mt_data[self.marker_dict[1]]['rot']
            pose = mt_data[self.marker_dict[1]]['pos']
            trans_matrix = np.eye(4)
            trans_matrix[:3,:3] = rot
            trans_matrix[:3, 3] = pose
            trans_mt_ob = self.get_trans(trans_matrix, f'{operator}MT', f'{operator}{self.marker_dict[1]}')
            self.tf_broadcaster.sendTransform([trans_mt_ob])
            print('Mt_Object Captured')
        
    def get_trans(self,pose, frame_id, child_frame_id):
        trans = TransformStamped()
        trans.header.stamp = self.get_clock().now().to_msg()
        trans.header.frame_id = frame_id # Parent frame
        trans.child_frame_id = child_frame_id   # Child frame

        # Set translation
        trans.transform.translation.x = pose[0,3]
        trans.transform.translation.y = pose[1,3]
        trans.transform.translation.z = pose[2,3]

        # Set rotation (identity quaternion)
        rotation_matrix = pose[:3, :3]
        q = self.rotation_matrix_to_quaternion(rotation_matrix)
        trans.transform.rotation.x = q[0]
        trans.transform.rotation.y = q[1]
        trans.transform.rotation.z = q[2]
        trans.transform.rotation.w = q[3]

        return trans

    def rotation_matrix_to_quaternion(self, R):
        
        q = tq.mat2quat(R)  # Returns quaternion in (w, x, y, z) order
        return q[1], q[2], q[3], q[0]

def main(args=None):
    rclpy.init(args=args)
    node = MicronTrackerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()