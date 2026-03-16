#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    port_arg = DeclareLaunchArgument("port", default_value="/dev/ttyUSB0")
    baud_arg = DeclareLaunchArgument("baud", default_value="115200")
    cmd_vel_topic_arg = DeclareLaunchArgument("cmd_vel_topic", default_value="/cmd_vel")
    odom_topic_arg = DeclareLaunchArgument("odom_topic", default_value="/odom")
    publish_tf_arg = DeclareLaunchArgument("publish_tf", default_value="true")
    enable_stall_compensation_arg = DeclareLaunchArgument("enable_stall_compensation", default_value="false")
    min_effective_linear_mps_arg = DeclareLaunchArgument("min_effective_linear_mps", default_value="0.0")
    min_effective_angular_rad_s_arg = DeclareLaunchArgument("min_effective_angular_rad_s", default_value="0.0")
    zero_cmd_epsilon_arg = DeclareLaunchArgument("zero_cmd_epsilon", default_value="0.0001")
    default_params = PathJoinSubstitution(
        [FindPackageShare("ros2_serial_diff_drive_bridge"), "config", "ros2_serial_diff_drive_bridge.params.yaml"]
    )
    params_arg = DeclareLaunchArgument("params_file", default_value=default_params)

    run_bridge = Node(
        package="ros2_serial_diff_drive_bridge",
        executable="serial_diff_drive_bridge",
        name="serial_diff_drive_bridge",
        output="screen",
        parameters=[
            LaunchConfiguration("params_file"),
            {
                "port": LaunchConfiguration("port"),
                "baud": LaunchConfiguration("baud"),
                "cmd_vel_topic": LaunchConfiguration("cmd_vel_topic"),
                "odom_topic": LaunchConfiguration("odom_topic"),
                "publish_tf": ParameterValue(LaunchConfiguration("publish_tf"), value_type=bool),
                "enable_stall_compensation": ParameterValue(
                    LaunchConfiguration("enable_stall_compensation"), value_type=bool
                ),
                "min_effective_linear_mps": ParameterValue(
                    LaunchConfiguration("min_effective_linear_mps"), value_type=float
                ),
                "min_effective_angular_rad_s": ParameterValue(
                    LaunchConfiguration("min_effective_angular_rad_s"), value_type=float
                ),
                "zero_cmd_epsilon": ParameterValue(LaunchConfiguration("zero_cmd_epsilon"), value_type=float),
            },
        ],
    )

    return LaunchDescription([
        port_arg,
        baud_arg,
        cmd_vel_topic_arg,
        odom_topic_arg,
        publish_tf_arg,
        enable_stall_compensation_arg,
        min_effective_linear_mps_arg,
        min_effective_angular_rad_s_arg,
        zero_cmd_epsilon_arg,
        params_arg,
        run_bridge,
    ])
