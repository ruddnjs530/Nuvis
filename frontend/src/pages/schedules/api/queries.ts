import type { CreateScheduleRequest, UpdateScheduleRequest } from './types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { scheduleApi } from './api';

const QUERY_KEY = ['schedules'] as const;

export function useSchedulesQuery() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: scheduleApi.getAll,
    refetchInterval: 10_000,
  });
}

export function useCreateScheduleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateScheduleRequest) => scheduleApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useUpdateScheduleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scheduleId, data }: { scheduleId: number; data: UpdateScheduleRequest }) =>
      scheduleApi.update(scheduleId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useDeleteScheduleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scheduleId: number) => scheduleApi.delete(scheduleId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useAiScheduleSuggestionsMutation() {
  return useMutation({
    mutationFn: () => scheduleApi.getAiSuggestions(),
  });
}
