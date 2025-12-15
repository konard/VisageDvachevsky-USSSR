export enum UserRole {
  ANONYMOUS = 'anonymous',
  USER = 'user',
  EDITOR = 'editor',
  ADMIN = 'admin',
}

export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  password_confirm: string
}

export interface UserInteraction {
  id: number
  user_id: string
  leader_id: number
  interaction_type: 'bookmark' | 'like' | 'view'
  created_at: string
}

export interface Comment {
  id: number
  user_id: string
  leader_id: number
  content: string
  user: {
    username: string
  }
  created_at: string
  updated_at: string
}
