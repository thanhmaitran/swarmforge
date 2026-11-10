"""Generate Gazebo (SDF 1.9, Harmonic) robot models and warehouse worlds from SwarmForge's own maps.

    python scripts/utilities/generate_gazebo_assets.py

Worlds are generated from the same warehouse layouts the core simulator uses, so Mode A (algorithm
simulation) and Mode B (physics simulation) describe the same environment. Robot models are generated
from :mod:`swarmforge.agents.robot_profile` (chassis, two driven wheels, caster, DiffDrive plugin).
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from swarmforge.agents.robot_profile import FAST, HEAVY_DUTY, STANDARD, RobotProfile
from swarmforge.config import load_config
from swarmforge.environment.map_loader import build_warehouse
from swarmforge.environment.warehouse import Warehouse

ROOT = Path(__file__).resolve().parents[2] / "infrastructure" / "gazebo"
MODELS = {"standard_robot": (STANDARD, "0.2 0.4 0.9 1"), "heavy_robot": (HEAVY_DUTY, "0.85 0.2 0.2 1"),
          "fast_robot": (FAST, "0.2 0.7 0.3 1")}


def inertia_box(mass: float, x: float, y: float, z: float) -> str:
    ixx, iyy, izz = mass / 12 * (y * y + z * z), mass / 12 * (x * x + z * z), mass / 12 * (x * x + y * y)
    return f"<ixx>{ixx:.5f}</ixx><iyy>{iyy:.5f}</iyy><izz>{izz:.5f}</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>"


def robot_sdf(name: str, p: RobotProfile, color: str) -> str:
    L, W, H = 0.5, 0.36, 0.12  # chassis
    mass = 20.0 + p.payload_capacity * 0.05
    wr, wb = p.wheel_radius * 2.0, p.wheel_base  # visual wheels are larger than the kinematic radius
    wheel_r = 0.08
    return f'''<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{name}">
    <link name="chassis">
      <pose>0 0 {wheel_r + H / 2:.3f} 0 0 0</pose>
      <inertial><mass>{mass:.2f}</mass><inertia>{inertia_box(mass, L, W, H)}</inertia></inertial>
      <visual name="body"><geometry><box><size>{L} {W} {H}</size></box></geometry>
        <material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual>
      <collision name="body"><geometry><box><size>{L} {W} {H}</size></box></geometry></collision>
    </link>
    <link name="left_wheel">
      <pose>0 {wb / 2 + 0.03:.3f} {wheel_r} -1.5708 0 0</pose>
      <inertial><mass>1.0</mass><inertia><ixx>0.002</ixx><iyy>0.002</iyy><izz>0.004</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <visual name="v"><geometry><cylinder><radius>{wheel_r}</radius><length>0.04</length></cylinder></geometry></visual>
      <collision name="c"><geometry><cylinder><radius>{wheel_r}</radius><length>0.04</length></cylinder></geometry></collision>
    </link>
    <link name="right_wheel">
      <pose>0 {-(wb / 2 + 0.03):.3f} {wheel_r} -1.5708 0 0</pose>
      <inertial><mass>1.0</mass><inertia><ixx>0.002</ixx><iyy>0.002</iyy><izz>0.004</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <visual name="v"><geometry><cylinder><radius>{wheel_r}</radius><length>0.04</length></cylinder></geometry></visual>
      <collision name="c"><geometry><cylinder><radius>{wheel_r}</radius><length>0.04</length></cylinder></geometry></collision>
    </link>
    <link name="caster">
      <pose>-0.2 0 0.04 0 0 0</pose>
      <inertial><mass>0.3</mass><inertia><ixx>0.0003</ixx><iyy>0.0003</iyy><izz>0.0003</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <collision name="c"><geometry><sphere><radius>0.04</radius></sphere></geometry>
        <surface><friction><ode><mu>0</mu><mu2>0</mu2></ode></friction></surface></collision>
      <visual name="v"><geometry><sphere><radius>0.04</radius></sphere></geometry></visual>
    </link>
    <joint name="left_wheel_joint" type="revolute"><parent>chassis</parent><child>left_wheel</child>
      <axis><xyz>0 0 1</xyz><limit><lower>-1e16</lower><upper>1e16</upper></limit></axis></joint>
    <joint name="right_wheel_joint" type="revolute"><parent>chassis</parent><child>right_wheel</child>
      <axis><xyz>0 0 1</xyz><limit><lower>-1e16</lower><upper>1e16</upper></limit></axis></joint>
    <joint name="caster_joint" type="ball"><parent>chassis</parent><child>caster</child></joint>
    <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>{wb + 0.06:.3f}</wheel_separation>
      <wheel_radius>{wheel_r}</wheel_radius>
      <max_linear_velocity>{p.max_speed}</max_linear_velocity>
      <max_angular_velocity>{p.max_angular_velocity}</max_angular_velocity>
      <max_linear_acceleration>{p.max_acceleration}</max_linear_acceleration>
      <topic>/model/{name}/cmd_vel</topic>
      <odom_topic>/model/{name}/odometry</odom_topic>
      <frame_id>{name}/odom</frame_id>
      <child_frame_id>{name}/chassis</child_frame_id>
    </plugin>
    <plugin filename="gz-sim-pose-publisher-system" name="gz::sim::systems::PosePublisher">
      <publish_model_pose>true</publish_model_pose>
    </plugin>
  </model>
</sdf>
'''


def model_config(name: str, p: RobotProfile) -> str:
    return f'''<?xml version="1.0"?>
<model>
  <name>{name}</name>
  <version>1.0</version>
  <sdf version="1.9">model.sdf</sdf>
  <description>{escape(p.profile_name)} differential-drive robot (SwarmForge simulation profile)</description>
</model>
'''


def box(name: str, x: float, y: float, sx: float, sy: float, sz: float, color: str, static: bool = True, z: float | None = None) -> str:
    z = sz / 2 if z is None else z
    return (f'    <model name="{name}"><static>{str(static).lower()}</static><pose>{x:.3f} {y:.3f} {z:.3f} 0 0 0</pose>'
            f'<link name="l"><visual name="v"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry>'
            f'<material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual>'
            f'<collision name="c"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry></collision></link></model>\n')


def zone(name: str, x: float, y: float, res: float, color: str) -> str:
    return (f'    <model name="{name}"><static>true</static><pose>{x:.3f} {y:.3f} 0.005 0 0 0</pose><link name="l">'
            f'<visual name="v"><geometry><box><size>{res * 0.9} {res * 0.9} 0.01</size></box></geometry>'
            f'<material><ambient>{color}</ambient><diffuse>{color}</diffuse></material></visual></link></model>\n')


def world_sdf(name: str, wh: Warehouse) -> str:
    res = wh.resolution
    W, H = wh.width * res, wh.height * res
    body = [f'    <model name="floor"><static>true</static><pose>{W / 2:.3f} {H / 2:.3f} -0.025 0 0 0</pose><link name="l">'
            f'<visual name="v"><geometry><box><size>{W} {H} 0.05</size></box></geometry>'
            f'<material><ambient>0.8 0.8 0.8 1</ambient><diffuse>0.8 0.8 0.8 1</diffuse></material></visual>'
            f'<collision name="c"><geometry><box><size>{W} {H} 0.05</size></box></geometry></collision></link></model>\n']
    t = 0.2
    body += [box("wall_n", W / 2, -t / 2, W + 2 * t, t, 1.0, "0.4 0.4 0.4 1"),
             box("wall_s", W / 2, H + t / 2, W + 2 * t, t, 1.0, "0.4 0.4 0.4 1"),
             box("wall_w", -t / 2, H / 2, t, H, 1.0, "0.4 0.4 0.4 1"),
             box("wall_e", W + t / 2, H / 2, t, H, 1.0, "0.4 0.4 0.4 1")]
    for i, (cx, cy) in enumerate(sorted(wh.static_obstacles)):
        x, y = wh.grid_to_world((cx, cy))
        body.append(box(f"shelf_{i}", x, y, res, res, 1.2, "0.55 0.35 0.15 1"))
    for kind, cells, color in (("pickup", wh.pickup_zones, "0.6 0.8 1 1"), ("delivery", wh.delivery_zones, "0.6 1 0.6 1"),
                               ("charger", wh.charging_stations, "1 0.8 0.3 1")):
        for i, c in enumerate(cells):
            x, y = wh.grid_to_world(c)
            body.append(zone(f"{kind}_{i}", x, y, res, color))
    return f'''<?xml version="1.0"?>
<sdf version="1.9">
  <world name="{name}">
    <physics name="1ms" type="ignored"><max_step_size>0.004</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>{W / 2:.1f} {H / 2:.1f} 20 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse><direction>-0.3 0.3 -1</direction></light>
{"".join(body)}  </world>
</sdf>
'''


def main() -> None:
    for name, (profile, color) in MODELS.items():
        d = ROOT / "models" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "model.sdf").write_text(robot_sdf(name, profile, color))
        (d / "model.config").write_text(model_config(name, profile))
    (ROOT / "worlds").mkdir(parents=True, exist_ok=True)
    for scen in ("warehouse_small", "warehouse_medium", "warehouse_large"):
        wh = build_warehouse(load_config(scen).environment)
        (ROOT / "worlds" / f"{scen}.sdf").write_text(world_sdf(scen, wh))
        print(f"{scen}: {len(wh.static_obstacles)} shelf cells")
    print(f"assets written under {ROOT}")


if __name__ == "__main__":
    main()
