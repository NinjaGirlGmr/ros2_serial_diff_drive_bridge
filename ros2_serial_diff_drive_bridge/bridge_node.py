#!/usr/bin/env python3

import math
import threading
from dataclasses import dataclass
from typing import Optional

import rclpy
from geometry_msgs.msg import Quaternion, TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster

try:
    import serial  # pyserial
    from serial import SerialException
except Exception as exc:  # pragma: no cover
    serial = None
    SerialException = Exception
    _SERIAL_IMPORT_ERROR = exc
else:
    _SERIAL_IMPORT_ERROR = None


@dataclass
class RobotState:
    fw_millis: int
    left_pos_rad: float
    left_vel_rad_s: float
    right_pos_rad: float
    right_vel_rad_s: float
    linear_mps: float
    angular_rad_s: float
    avg_distance_mm: float


def yaw_to_quaternion(yaw: float) -> Quaternion:
    q = Quaternion()
    half = yaw * 0.5
    q.z = math.sin(half)
    q.w = math.cos(half)
    q.x = 0.0
    q.y = 0.0
    return q


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class SerialDiffDriveBridge(Node):
    def __init__(self) -> None:
        super().__init__("serial_diff_drive_bridge")

        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baud", 115200)
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("joint_state_topic", "/joint_states")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("raw_state_topic", "/robot_serial_state")
        self.declare_parameter("base_frame_id", "base_link")
        self.declare_parameter("odom_frame_id", "odom")
        self.declare_parameter("left_wheel_joint", "left_wheel_joint")
        self.declare_parameter("right_wheel_joint", "right_wheel_joint")
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("cmd_repeat_hz", 20.0)
        self.declare_parameter("cmd_timeout_sec", 0.5)
        self.declare_parameter("max_linear_mps", 1.5)
        self.declare_parameter("max_angular_rad_s", 6.0)
        self.declare_parameter("serial_poll_hz", 200.0)

        self.port = self.get_parameter("port").get_parameter_value().string_value
        self.baud = self.get_parameter("baud").get_parameter_value().integer_value
        self.cmd_vel_topic = self.get_parameter("cmd_vel_topic").value
        self.joint_state_topic = self.get_parameter("joint_state_topic").value
        self.odom_topic = self.get_parameter("odom_topic").value
        self.raw_state_topic = self.get_parameter("raw_state_topic").value
        self.base_frame_id = self.get_parameter("base_frame_id").value
        self.odom_frame_id = self.get_parameter("odom_frame_id").value
        self.left_wheel_joint = self.get_parameter("left_wheel_joint").value
        self.right_wheel_joint = self.get_parameter("right_wheel_joint").value
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.cmd_repeat_hz = float(self.get_parameter("cmd_repeat_hz").value)
        self.cmd_timeout_sec = float(self.get_parameter("cmd_timeout_sec").value)
        self.max_linear_mps = float(self.get_parameter("max_linear_mps").value)
        self.max_angular_rad_s = float(self.get_parameter("max_angular_rad_s").value)
        self.serial_poll_hz = float(self.get_parameter("serial_poll_hz").value)

        if serial is None:
            raise RuntimeError(f"pyserial import failed: {_SERIAL_IMPORT_ERROR}")

        self.serial_lock = threading.Lock()
        self.ser = serial.Serial(self.port, self.baud, timeout=0.0, write_timeout=0.1)
        self.get_logger().info(f"Opened serial port {self.port} @ {self.baud}")

        self.cmd_linear = 0.0
        self.cmd_angular = 0.0
        self.last_cmd_time = self.get_clock().now()

        self.prev_fw_millis: Optional[int] = None
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.joint_pub = self.create_publisher(JointState, self.joint_state_topic, 20)
        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 20)
        self.raw_state_pub = self.create_publisher(String, self.raw_state_topic, 50)
        self.tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None
        self.cmd_sub = self.create_subscription(Twist, self.cmd_vel_topic, self.on_cmd_vel, 20)

        serial_period = 1.0 / self.serial_poll_hz if self.serial_poll_hz > 0.0 else 0.005
        cmd_period = 1.0 / self.cmd_repeat_hz if self.cmd_repeat_hz > 0.0 else 0.05
        self.serial_timer = self.create_timer(serial_period, self.poll_serial)
        self.cmd_timer = self.create_timer(cmd_period, self.send_cmd_timer)

    def destroy_node(self) -> bool:
        try:
            with self.serial_lock:
                if getattr(self, "ser", None) is not None and self.ser.is_open:
                    try:
                        self.ser.write(b"STOP\n")
                    except Exception:
                        pass
                    self.ser.close()
        finally:
            pass
        return super().destroy_node()

    def on_cmd_vel(self, msg: Twist) -> None:
        self.cmd_linear = clamp(float(msg.linear.x), -self.max_linear_mps, self.max_linear_mps)
        self.cmd_angular = clamp(float(msg.angular.z), -self.max_angular_rad_s, self.max_angular_rad_s)
        self.last_cmd_time = self.get_clock().now()

    def send_cmd_timer(self) -> None:
        now = self.get_clock().now()
        age = (now - self.last_cmd_time).nanoseconds / 1e9

        linear = self.cmd_linear
        angular = self.cmd_angular
        if age > self.cmd_timeout_sec:
            linear = 0.0
            angular = 0.0

        line = f"CMD_VEL,{linear:.6f},{angular:.6f}\n"
        try:
            with self.serial_lock:
                self.ser.write(line.encode("ascii"))
        except SerialException as exc:
            self.get_logger().error(f"Serial write failed: {exc}")

    def poll_serial(self) -> None:
        # Drain a bounded number of lines per tick so other callbacks still run.
        for _ in range(20):
            try:
                with self.serial_lock:
                    raw = self.ser.readline()
            except SerialException as exc:
                self.get_logger().error(f"Serial read failed: {exc}")
                return

            if not raw:
                return

            line = raw.decode("ascii", errors="ignore").strip()
            if not line:
                continue

            self.raw_state_pub.publish(String(data=line))
            state = self.parse_state_line(line)
            if state is None:
                continue

            self.publish_from_state(state)

    def parse_state_line(self, line: str) -> Optional[RobotState]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 9 or parts[0] != "STATE":
            return None

        try:
            return RobotState(
                fw_millis=int(parts[1]),
                left_pos_rad=float(parts[2]),
                left_vel_rad_s=float(parts[3]),
                right_pos_rad=float(parts[4]),
                right_vel_rad_s=float(parts[5]),
                linear_mps=float(parts[6]),
                angular_rad_s=float(parts[7]),
                avg_distance_mm=float(parts[8]),
            )
        except ValueError:
            self.get_logger().warn(f"Malformed STATE line: {line}")
            return None

    def publish_from_state(self, state: RobotState) -> None:
        stamp = self.get_clock().now().to_msg()

        if self.prev_fw_millis is not None:
            dt = (state.fw_millis - self.prev_fw_millis) / 1000.0
            if 0.0 < dt < 1.0:
                self.integrate_odom(state.linear_mps, state.angular_rad_s, dt)
        self.prev_fw_millis = state.fw_millis

        joint = JointState()
        joint.header.stamp = stamp
        joint.name = [self.left_wheel_joint, self.right_wheel_joint]
        joint.position = [state.left_pos_rad, state.right_pos_rad]
        joint.velocity = [state.left_vel_rad_s, state.right_vel_rad_s]
        self.joint_pub.publish(joint)

        q = yaw_to_quaternion(self.yaw)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.base_frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q
        odom.twist.twist.linear.x = state.linear_mps
        odom.twist.twist.angular.z = state.angular_rad_s
        self.odom_pub.publish(odom)

        if self.tf_broadcaster is not None:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = stamp
            tf_msg.header.frame_id = self.odom_frame_id
            tf_msg.child_frame_id = self.base_frame_id
            tf_msg.transform.translation.x = self.x
            tf_msg.transform.translation.y = self.y
            tf_msg.transform.translation.z = 0.0
            tf_msg.transform.rotation = q
            self.tf_broadcaster.sendTransform(tf_msg)

    def integrate_odom(self, linear_mps: float, angular_rad_s: float, dt: float) -> None:
        if abs(angular_rad_s) < 1e-6:
            self.x += linear_mps * dt * math.cos(self.yaw)
            self.y += linear_mps * dt * math.sin(self.yaw)
            return

        yaw_mid = self.yaw + 0.5 * angular_rad_s * dt
        self.x += linear_mps * dt * math.cos(yaw_mid)
        self.y += linear_mps * dt * math.sin(yaw_mid)
        self.yaw += angular_rad_s * dt
        self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = SerialDiffDriveBridge()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
