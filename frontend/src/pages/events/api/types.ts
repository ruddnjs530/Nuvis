export type ConditionType = 'FINE_DUST' | 'HUMIDITY' | 'TEMPERATURE' | string;
export type ConditionOperator = 'GT' | 'LT' | 'EQ' | string;
export type ActionModuleType = 'AIR_PURIFIER' | 'HUMIDIFIER' | 'AC' | string;

export interface EventResponse {
  eventId: number;
  userId: number;
  roomId: number;
  conditionType: ConditionType;
  conditionOperator: ConditionOperator;
  thresholdValue: number;
  actionModuleType: ActionModuleType;
  isActive: boolean;
}

export interface CreateEventRequest {
  roomId: number;
  conditionType: ConditionType;
  conditionOperator: ConditionOperator;
  thresholdValue: number;
  actionModuleType: ActionModuleType;
  isActive: boolean;
}

export type UpdateEventRequest = Partial<CreateEventRequest>;
