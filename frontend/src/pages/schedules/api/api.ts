import type { AiResponse, CreateScheduleRequest, Schedule, UpdateScheduleRequest } from './types';
import type { ApiResponse } from '~/lib/api/types';
import { api } from '~/lib/api/client';

export const scheduleApi = {
  getAll: () =>
    api<ApiResponse<Schedule[]>>({ method: 'get', url: 'schedule' }).then(res => res.data),

  create: (data: CreateScheduleRequest) =>
    api<ApiResponse<Schedule>>({ method: 'post', url: 'schedule', options: { json: data } }),

  update: (scheduleId: number, data: UpdateScheduleRequest) =>
    api<ApiResponse<Schedule>>({ method: 'put', url: `schedule/${scheduleId}`, options: { json: data } }),

  delete: (scheduleId: number) =>
    api<void>({ method: 'delete', url: `schedule/${scheduleId}` }),

  getAiSuggestions: () =>
    api<AiResponse>({ method: 'get', url: 'schedule/ai-suggestions' }),
};
