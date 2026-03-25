import type { APIClientParams } from './types';
import ky, { HTTPError } from 'ky';
import { useAuthStore } from '~/store/auth-store';
import { APIError } from './error';

export const instance = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      },
    ],
    afterResponse: [
      (_request, _options, response) => {
        if (response.status === 401) {
          useAuthStore.getState().logout();
          window.location.href = '/login';
        }
      },
    ],
  },
});

export async function api<T>({
  method = 'get',
  url,
  options,
  type = 'json',
  apiPrefix = 'api/v1',
}: APIClientParams): Promise<T> {
  const normalizedUrl = url.startsWith('/') ? url.slice(1) : url;
  const requestUrl = apiPrefix ? `${apiPrefix}/${normalizedUrl}` : normalizedUrl;

  try {
    const response = await instance<T>(requestUrl, {
      method,
      ...options,
    });
    return await (response[type] as () => Promise<T>)();
  }
  catch (error) {
    if (error instanceof HTTPError) {
      throw new APIError({
        status: error.response?.status ?? 520,
        message: error.message,
        response: error.response,
      });
    }

    throw new APIError({
      message: (error as Error).message ?? 'Unknown Error',
    });
  }
}
