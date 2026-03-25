export interface LoginRequest {
  email: string;
  pw: string;
}

export interface LoginResponse {
  accessToken: string;
}
