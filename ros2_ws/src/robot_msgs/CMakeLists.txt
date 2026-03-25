cmake_minimum_required(VERSION 3.8)
project(robot_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

set(msg_files
  "msg/RobotStatus.msg"
  "msg/RobotCommand.msg"
  "msg/ModuleState.msg"
  "msg/SensorState.msg"
  "msg/ErrorReport.msg"
  "msg/Heartbeat.msg"
)

set(srv_files
  "srv/EmergencyStop.srv"
  "srv/CancelTask.srv"
  "srv/SetManualControl.srv"
  "srv/SetModuleState.srv"
  "srv/Relocalize.srv"
)

set(action_files
  "action/ExecuteTask.action"
  "action/NavToGoal.action"
  "action/NavPath.action"
  "action/ReturnHome.action"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${srv_files}
  ${action_files}
  DEPENDENCIES builtin_interfaces geometry_msgs std_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
