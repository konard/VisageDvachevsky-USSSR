import apiClient from './client'
import { User, AuthTokens, LoginCredentials, RegisterData } from '@/types/user'

export const authService = {
  // Register new user
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', data)
    return response.data
  },

  // Login user
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await apiClient.post<AuthTokens>('/auth/login', credentials)
    const { access_token, refresh_token } = response.data

    // Store tokens
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)

    return response.data
  },

  // Logout user
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      // Clear tokens regardless of API response
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  },

  // Get current user
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  },

  // Refresh access token
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await apiClient.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken,
    })

    const { access_token } = response.data
    localStorage.setItem('access_token', access_token)

    return response.data
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  },

  // Get access token
  getAccessToken(): string | null {
    return localStorage.getItem('access_token')
  },
}

export default authService
