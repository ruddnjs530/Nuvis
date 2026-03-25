import type { RobotStatusResponse, RoomDataResponse } from './types';
import type { ApiResponse } from '~/lib/api/types';
import { api } from '~/lib/api/client';

export const dashboardApi = {
  getRoomData: () =>
    api<ApiResponse<RoomDataResponse[]>>({
      method: 'get',
      url: 'room/data',
    }).then(res => res.data),

  getRobotStatus: () =>
    api<ApiResponse<RobotStatusResponse>>({
      method: 'get',
      url: 'robot/status',
    }).then(res => res.data),
};
