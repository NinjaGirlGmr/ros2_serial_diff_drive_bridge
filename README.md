# ros2_serial_diff_drive_bridge

ROS 2 Python package that bridges `geometry_msgs/msg/Twist` (`/cmd_vel`) to the RobotMotorDriver firmware serial protocol and publishes `JointState` + `Odometry` from firmware `STATE,...` telemetry.

## Features
- Subscribe to `/cmd_vel`
- Send serial `CMD_VEL,<linear_mps>,<angular_rad_s>`
- Parse serial `STATE,...`
- Publish `/joint_states`
- Publish `/odom`
- Optional `odom -> base_link` TF

## Install (inside a ROS 2 workspace)
Place this folder in your ROS 2 workspace `src/` and build:

```bash
cd ~/your_ws
mkdir -p src
cp -R /path/to/RobotMotorDriver/ros2_serial_diff_drive_bridge src/
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select ros2_serial_diff_drive_bridge
source install/setup.bash
```

If `pyserial` is not already available in your ROS Python environment:

```bash
pip install pyserial
```

CI workflow:
- GitHub Actions config is included at `.github/workflows/ci.yml`
- It runs Python syntax checks and packaging metadata smoke checks

## Run
Direct node:

```bash
ros2 run ros2_serial_diff_drive_bridge serial_diff_drive_bridge --ros-args -p port:=/dev/ttyUSB0 -p baud:=115200
```

Launch file:

```bash
ros2 launch ros2_serial_diff_drive_bridge ros2_serial_diff_drive_bridge.launch.py port:=/dev/ttyUSB0
```

Custom params:

```bash
ros2 launch ros2_serial_diff_drive_bridge ros2_serial_diff_drive_bridge.launch.py \
  port:=/dev/ttyUSB0 \
  params_file:=/absolute/path/to/ros2_serial_diff_drive_bridge.params.yaml
```

## Topics
- Subscribes: `/cmd_vel` (`geometry_msgs/msg/Twist`)
- Publishes: `/joint_states` (`sensor_msgs/msg/JointState`)
- Publishes: `/odom` (`nav_msgs/msg/Odometry`)
- Publishes: `/robot_serial_state` (`std_msgs/msg/String`) raw serial lines

## Notes
- The firmware must be flashed with the `CMD_VEL` / `STATE` protocol updates from this repo.
- Firmware `maxWheelLinearSpeedMps` should be tuned for good speed tracking.

## Optional Stall Compensation Parameters
- `enable_stall_compensation` (`bool`, default `false`): when enabled, non-zero command magnitudes are raised to minimum effective values.
- `min_effective_linear_mps` (`float`, default `0.0`): minimum absolute non-zero linear command.
- `min_effective_angular_rad_s` (`float`, default `0.0`): minimum absolute non-zero angular command.
- `zero_cmd_epsilon` (`float`, default `1e-4`): commands with magnitude <= epsilon are treated as exact zero.
