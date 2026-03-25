import type { LoginRequest, LoginResponse } from './types';
import type { ApiResponse } from '~/lib/api/types';
import { api } from '~/lib/api/client';

export const authApi = {
  login: (data: LoginRequest) =>
    api<ApiResponse<LoginResponse>>({
      method: 'post',
      url: 'auth/login', // 백엔드 라우트에 맞게 수정 가능
      options: { json: data },
    }).then(res => res.data),
};
