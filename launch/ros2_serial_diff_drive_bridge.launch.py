#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    port_arg = DeclareLaunchArgument("port", default_value="/dev/ttyUSB0")
    baud_arg = DeclareLaunchArgument("baud", default_value="115200")
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
            {"port": LaunchConfiguration("port"), "baud": LaunchConfiguration("baud")},
        ],
    )

    return LaunchDescription([port_arg, baud_arg, params_arg, run_bridge])
