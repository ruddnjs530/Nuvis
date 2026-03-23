builtin_interfaces/Time stamp
string robot_id
uint8 mode
uint8 task_state
string active_task_id
geometry_msgs/PoseStamped pose
float32 battery_pct
bool is_charging
uint8 safety_state
uint32 last_error_code

uint8 MODE_IDLE=0
uint8 MODE_MANUAL=1
uint8 MODE_AUTONOMOUS=2
uint8 MODE_DOCKING=3
uint8 MODE_ERROR=4

uint8 TASK_NONE=0
uint8 TASK_RECEIVED=1
uint8 TASK_VALIDATING=2
uint8 TASK_ACCEPTED=3
uint8 TASK_MOVING=4
uint8 TASK_ARRIVED=5
uint8 TASK_EXECUTING_MODULE=6
uint8 TASK_RETURNING=7
uint8 TASK_COMPLETED=8
uint8 TASK_FAILED=9
uint8 TASK_CANCELED=10

uint8 SAFETY_NORMAL=0
uint8 SAFETY_WARN=1
uint8 SAFETY_ESTOP=2
