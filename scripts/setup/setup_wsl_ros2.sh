#!/usr/bin/env bash
# ROS 2 Jazzy + Gazebo Harmonic on Ubuntu 24.04 (WSL2). Follow the official ROS 2 Jazzy installation guide first
# (apt sources / keys), then run this script. Not executed in the authoring environment.
set -euo pipefail
sudo apt update && sudo apt upgrade -y
sudo apt install -y ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-rviz2 ros-jazzy-robot-state-publisher \
    ros-jazzy-xacro ros-jazzy-tf2-ros python3-colcon-common-extensions
grep -q "ros/jazzy/setup.bash" ~/.bashrc || echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
mkdir -p ~/swarmforge_ws/src
ln -sfn "$(pwd)/infrastructure/ros2/swarmforge_ros" ~/swarmforge_ws/src/swarmforge_ros
cd ~/swarmforge_ws
colcon build --symlink-install
source install/setup.bash
pip install --break-system-packages -e "$OLDPWD"   # makes `swarmforge` importable for the ROS nodes
ros2 pkg list | grep swarmforge
echo "Try: ros2 launch swarmforge_ros fleet.launch.py   |   gz sim -r infrastructure/gazebo/worlds/warehouse_small.sdf"
