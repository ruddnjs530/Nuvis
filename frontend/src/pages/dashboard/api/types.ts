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

export interface RobotPose {
  x: number;
  y: number;
  yaw: number;
}

export interface RobotStatusResponse {
  robotId: string;
  mode: number;
  taskState: number;
  activeTaskId: string;
  batteryPct: number;
  isCharging: boolean;
  safetyState: number;
  lastErrorCode: number;
  pose: RobotPose;
  stamp: string;
}
