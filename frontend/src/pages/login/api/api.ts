import type { LoginRequest, LoginResponse } from './types';
import type { ApiResponse } from '~/lib/api/types';
import { api } from '~/lib/api/client';

export const authApi = {
  login: (data: LoginRequest) =>
    api<ApiResponse<LoginResponse>>({
      method: 'post',
      url: 'auth/login',
      options: { json: data },
    }),
};
