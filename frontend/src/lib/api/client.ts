import type { APIClientParams, TokenProvider } from './types';
import ky, { HTTPError } from 'ky';
import { APIError } from './error';

let getToken: TokenProvider = () => null;

export function setTokenProvider(provider: TokenProvider) {
  getToken = provider;
}

export const instance = ky.create({
  prefixUrl: import.meta.env.VITE_API_URL,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = getToken();
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
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
