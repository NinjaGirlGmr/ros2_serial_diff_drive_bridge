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
            },
        ],
    )

    return LaunchDescription([
        port_arg,
        baud_arg,
        cmd_vel_topic_arg,
        odom_topic_arg,
        publish_tf_arg,
        params_arg,
        run_bridge,
    ])
