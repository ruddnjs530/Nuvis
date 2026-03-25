import type { Options } from 'ky';

export interface APIClientParams {
  method?: 'get' | 'post' | 'put' | 'delete' | 'patch';
  url: string;
  options?: Options;
  type?: 'json' | 'text' | 'blob' | 'arrayBuffer' | 'formData';
  apiPrefix?: string;
}

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
