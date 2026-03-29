export type ActionModuleType = 'AIR_PURIFIER' | 'HUMIDIFIER';

export interface Schedule {
  scheduleId: number;
  userId?: number;
  roomId: number;
  actionModuleType: ActionModuleType;
  actionModulePower: boolean;
  actionModuleLevel: number;
  startTime: string; // ISO 8601
  durationMinutes: number;
  isActive: boolean;
}

export type CreateScheduleRequest = Omit<Schedule, 'scheduleId' | 'userId' | 'actionModulePower' | 'actionModuleLevel'>;
export type UpdateScheduleRequest = CreateScheduleRequest;

export interface AiDeviceResponse {
  recommendedSchedule?: {
    time: string;
    actionModuleType: string;
    action: string;
  };
  analysisDetails?: {
    topLifestylePattern: string;
    [key: string]: any;
  };
  reason?: string;
  message?: string;
}

export interface AiRoomData {
  roomId: number;
  recordsAnalyzed: number;
  suggestions: Record<string, AiDeviceResponse>;
}

export interface AiResponse {
  status: string;
  userId: number;
  roomCount?: number;
  roomIds?: number[];
  data: Record<string, AiRoomData>;
}
