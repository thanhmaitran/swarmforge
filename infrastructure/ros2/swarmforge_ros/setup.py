from glob import glob

from setuptools import find_packages, setup

package_name = "swarmforge_ros"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="SwarmForge maintainers",
    maintainer_email="maintainer@example.com",
    description="ROS 2 middleware bridge for the SwarmForge fleet simulator",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "fleet_node = swarmforge_ros.fleet_node:main",
            "robot_node = swarmforge_ros.robot_node:main",
            "task_node = swarmforge_ros.task_node:main",
            "communication_node = swarmforge_ros.communication_node:main",
        ],
    },
)
