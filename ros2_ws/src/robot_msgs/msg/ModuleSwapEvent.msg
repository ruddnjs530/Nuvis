builtin_interfaces/Time stamp
string task_id
string command_id
uint8 from_module_type
uint8 to_module_type
uint8 state
bool success
string message

uint8 STATE_REQUESTED=0
uint8 STATE_MOVING_TO_HQ=1
uint8 STATE_ARRIVED_HQ=2
uint8 STATE_SWAPPING=3
uint8 STATE_COMPLETED=4
uint8 STATE_FAILED=5
