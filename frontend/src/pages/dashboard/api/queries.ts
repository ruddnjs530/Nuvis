import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from './api';

export function useRoomDataQuery() {
  return useQuery({
    queryKey: ['dashboard', 'room-data'],
    queryFn: dashboardApi.getRoomData,
    refetchInterval: 5000, // 폴링하여 최신 상태 유지
  });
}

export function useRobotStatusQuery() {
  return useQuery({
    queryKey: ['dashboard', 'robot-status'],
    queryFn: dashboardApi.getRobotStatus,
    refetchInterval: 1000,
  });
}
