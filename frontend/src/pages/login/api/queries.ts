import type { LoginRequest } from './types';
import { useMutation } from '@tanstack/react-query';
import { authApi } from './api';

export function useLoginMutation() {
  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
  });
}
