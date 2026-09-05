export interface User {
  id: string;
  username: string;
  display_name?: string;
  avatar_url?: string;
  github_user_id: number;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthResponse {
  status: string;
  message: string;
  access_token: string;
  user: User;
}

export interface AuthorizeResponse {
  authorization_url: string;
  state: string;
}
