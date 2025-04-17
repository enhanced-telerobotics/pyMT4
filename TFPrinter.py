import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener

class TFPrinter(Node):
    def __init__(self):
        super().__init__('tf_printer')
        self.tf_buffer = Buffer()
        self.listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(1.0, self.print_frames)

    def print_frames(self):
        all_frames = self.tf_buffer.all_frames_as_yaml()
        self.get_logger().info("\n" + all_frames)

def main():
    rclpy.init()
    node = TFPrinter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()
