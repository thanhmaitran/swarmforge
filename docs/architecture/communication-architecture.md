# Communication architecture

## In-simulator network (always available)

Messages: `STATE_UPDATE`, `HEARTBEAT` (robot -> fleet), `ASSIGN` (fleet -> robot), `ACK` (robot -> fleet).
Each message gets `delivery_time = created_at + delta` (constant + optional jitter), may be dropped by a seeded
Bernoulli process, and expires after `message_ttl`. Every message ends with exactly one outcome
(`delivered`, `delayed`, `dropped`, `expired`); `MessageBus.is_balanced()` asserts `sent = finished + in_flight`.

Reliability: an `ASSIGN` is retransmitted every `ack_timeout` until acknowledged; duplicate assignments are
idempotent. A robot with no message for `state_timeout` seconds is declared unreachable and its un-started tasks
are reassigned. Out-of-order state updates are ignored (sequence numbers).

Failure kinds: `failure` (robot stops, its cell becomes an obstacle, cargo is reclaimed after the timeout) and
`disconnect` (robot is silent; it stops unless it already carries cargo - a fail-safe assumption).

## ROS 2 topics (Mode B)

| Topic | Type | Rate | QoS |
|---|---|---|---|
| `/swarmforge/fleet/status` | `std_msgs/String` (JSON) | 1 Hz | reliable, depth 10 |
| `/swarmforge/tasks/new` | `std_msgs/String` (JSON) | event | reliable, depth 10 |
| `/swarmforge/robot_NN/pose` | `geometry_msgs/PoseStamped`, frame `map` | 10 Hz | best effort, depth 5 |
| `/swarmforge/robot_NN/velocity` | `geometry_msgs/Twist` | 10 Hz | best effort |
| `/swarmforge/robot_NN/state` | `std_msgs/String` (JSON) | 2 Hz | reliable |
| `/model/robot_NN/cmd_vel` | `geometry_msgs/Twist` | 20 Hz | default |

Registration or task requests would be better expressed as ROS services/actions in a future version; the current
bridge uses a JSON topic for simplicity. Conventions: frame `map`, metres, yaw about +z.
