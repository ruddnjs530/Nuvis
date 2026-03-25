export interface RoomCondition {
  temperature: number;
  humidity: number;
  fineDust: number;
  updatedAt: string;
}

export interface RoomDataResponse {
  roomId: number;
  name: string;
  condition: RoomCondition | null;
}

export interface AttachedModule {
  type: number;
  name: string;
  is_available: boolean;
}

export interface RobotStatusResponse {
  robot_id: string;
  mode: number;
  task_state: number;
  active_task_id: string;
  battery_pct: number;
  is_charging: boolean;
  safety_state: number;
  last_error_code: number;
  pose_x: number;
  pose_y: number;
  pose_yaw: number;
  stamp: string;
  attached_module: AttachedModule;
}
