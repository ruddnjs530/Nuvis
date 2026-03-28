export type ActionModuleType = 'AIR_PURIFIER' | 'HUMIDIFIER';

export interface Schedule {
  scheduleId: number;
  userId?: number;
  roomId: number;
  actionModuleType: ActionModuleType;
  actionModulePower: boolean; // true = 켜기, false = 끄기
  actionModuleLevel: number; // 1 ~ 3
  startTime: string; // ISO 8601: "1970-01-01T14:30:00.000Z"
  durationMinutes: number;
  isActive: boolean;
}

export type CreateScheduleRequest = Omit<Schedule, 'scheduleId' | 'userId' | 'actionModulePower' | 'actionModuleLevel'>;
export type UpdateScheduleRequest = CreateScheduleRequest;

export interface AiDeviceResponse {
  recommended_schedule?: {
    time: string;
    actionModuleType: string;
    action: string;
  };
  analysis_details?: {
    top_lifestyle_pattern: string;
    [key: string]: any;
  };
  reason?: string;
  message?: string;
}

export interface AiResponse {
  status: string;
  user_id: number;
  data: Record<string, AiDeviceResponse>;
}
