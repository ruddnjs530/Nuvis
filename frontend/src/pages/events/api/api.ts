import type { CreateEventRequest, EventResponse, UpdateEventRequest } from './types';
import type { ApiResponse } from '~/lib/api/types';

import { api } from '~/lib/api/client';

export const eventApi = {
  // 이벤트 목록 조회
  getEvents: () =>
    api<ApiResponse<EventResponse[]>>({
      method: 'get',
      url: 'event',
    }).then(res => res.data),

  // 이벤트 생성
  createEvent: (data: CreateEventRequest) =>
    api<ApiResponse<EventResponse>>({
      method: 'post',
      url: 'event',
      options: { json: data },
    }).then(res => res.data),

  // 이벤트 수정 (일부 속성 업데이트)
  updateEvent: (eventId: number, data: UpdateEventRequest) =>
    api<ApiResponse<EventResponse>>({
      method: 'put',
      url: `event/${eventId}`,
      options: { json: data },
    }).then(res => res.data),

  // 이벤트 삭제
  deleteEvent: (eventId: number) =>
    api<ApiResponse<EventResponse>>({
      method: 'delete',
      url: `event/${eventId}`,
    }).then(res => res.data),
};
