import type { KyResponse } from 'ky';

export class APIError extends Error {
  status: number;
  response: KyResponse | null;

  constructor({
    message = 'Unknown Error',
    status = 520,
    response = null,
  }: {
    message?: string;
    status?: number;
    response?: KyResponse | null;
  }) {
    super(message);

    this.status = status;
    this.response = response;

    Object.setPrototypeOf(this, new.target.prototype);
  }
}
