import type { LoginRequest, LoginResponse } from './types';
import { api } from '~/lib/api/client';

export const authApi = {
  login: (data: LoginRequest) =>
    api<LoginResponse>({
      method: 'post',
      url: 'auth/login',
      options: { json: data },
    }),
};
