from setuptools import setup


package_name = "ros2_serial_diff_drive_bridge"


setup(
    name=package_name,
    version="0.1.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/ros2_serial_diff_drive_bridge.launch.py"]),
        (f"share/{package_name}/config", ["config/ros2_serial_diff_drive_bridge.params.yaml"]),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    maintainer="NinjaGirlGmr",
    maintainer_email="NinjaGirlGmr@users.noreply.github.com",
    description="ROS 2 serial diff-drive bridge for the RobotMotorDriver CMD_VEL/STATE protocol",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "serial_diff_drive_bridge = ros2_serial_diff_drive_bridge.bridge_node:main",
        ],
    },
)
