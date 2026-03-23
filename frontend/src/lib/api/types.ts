import type { Options } from 'ky';

export interface APIClientParams {
  method?: Options['method'];
  url: string;
  options?: Options;
  type?: 'json' | 'text' | 'formData' | 'arrayBuffer' | 'blob';
  apiPrefix?: ApiPrefix;
}

type ApiPrefix = 'api/v1';

export type TokenProvider = () => string | null | undefined;

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface PageResponse<T> {
  content: T[];
  currentPage: number;
  totalElements: number;
  totalPages: number;
  size: number;
  hasPrev: boolean;
  hasNext: boolean;
}
