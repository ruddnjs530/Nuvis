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
  isAvailable: boolean;
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
  poseX: number;
  poseY: number;
  poseYaw: number;
  stamp: string;
  attachedModule: AttachedModule;
}
