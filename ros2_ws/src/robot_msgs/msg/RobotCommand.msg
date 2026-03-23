string command_id
builtin_interfaces/Time issued_at
uint8 command_type
string target_zone
geometry_msgs/PoseStamped target_pose
uint8 module_type
bool module_power
uint8 module_level
uint32 max_exec_sec

uint8 COMMAND_MOVE=0
uint8 COMMAND_MODULE=1
uint8 COMMAND_STOP=2
uint8 COMMAND_CANCEL=3
uint8 COMMAND_RETURN=4

uint8 MODULE_NONE=0
uint8 MODULE_AIR_PURIFIER=1
uint8 MODULE_HUMIDIFIER=2
uint8 MODULE_DEHUMIDIFIER=3
