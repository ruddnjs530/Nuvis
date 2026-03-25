import type { CreateEventRequest, UpdateEventRequest } from './types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { eventApi } from './api';

export const EVENT_QUERY_KEYS = {
  all: ['events'] as const,
};

export function useEventsQuery() {
  return useQuery({
    queryKey: EVENT_QUERY_KEYS.all,
    queryFn: eventApi.getEvents,
  });
}

export function useCreateEventMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateEventRequest) => eventApi.createEvent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVENT_QUERY_KEYS.all });
    },
  });
}

export function useUpdateEventMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ eventId, data }: { eventId: number; data: UpdateEventRequest }) =>
      eventApi.updateEvent(eventId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVENT_QUERY_KEYS.all });
    },
  });
}

export function useDeleteEventMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (eventId: number) => eventApi.deleteEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVENT_QUERY_KEYS.all });
    },
  });
}
