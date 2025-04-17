import rclpy
import tf2_ros
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
import numpy as np
import transforms3d.quaternions as tq
from scipy.spatial.transform import Rotation as R

operator = 'KW'

class TransformReceiverNode(Node):
    def __init__(self):
        super().__init__(f'{operator}TransformReceivernode')
        
        self.marker_dict = [f'{operator}gripperbase', f'{operator}MT', f'{operator}object']
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(1.0/40, self.timer_callback)
        print("Transform Listener Initialized")

    def timer_callback(self):
        t_GB_MT = self.tf_buffer.lookup_transform(self.marker_dict[1], self.marker_dict[0], rclpy.time.Time())
        t_MT_OBJ = self.tf_buffer.lookup_transform(self.marker_dict[2], self.marker_dict[1], rclpy.time.Time())
        t1 = self.transform_generator(t_GB_MT)
        t2 = self.transform_generator(t_MT_OBJ)
        t_GB_Obj = np.dot(t1, t2)
        print(f't_GB_OBJ: {t_GB_Obj}')

    def transform_generator(self, trans_msg):
        t = trans_msg.transform.translation
        translation = np.array([t.x, t.y, t.z])

        # Extract quaternion and convert to rotation matrix
        q = trans_msg.transform.rotation
        rotation = R.from_quat([q.x, q.y, q.z, q.w]).as_matrix()  # Convert quaternion to 3×3 rotation matrix
        
        # Construct 4×4 homogeneous transformation matrix
        transformation_matrix = np.eye(4)  # Initialize as identity
        transformation_matrix[:3, :3] = rotation
        transformation_matrix[:3, 3] = translation
        return transformation_matrix

def main(args=None):
    rclpy.init(args=args)
    node = TransformReceiverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()