import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { toast } from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error: AxiosError) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean
        }

        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: refreshToken,
              })

              const { access_token } = response.data
              localStorage.setItem('access_token', access_token)

              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access_token}`
              }

              return this.client(originalRequest)
            }
          } catch (refreshError) {
            // Refresh token failed, logout user
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        // Handle other errors
        if (error.response) {
          const message = (error.response.data as { detail?: string })?.detail ||
                         'An error occurred'
          toast.error(message)
        } else if (error.request) {
          toast.error('Network error. Please check your connection.')
        } else {
          toast.error('An unexpected error occurred.')
        }

        return Promise.reject(error)
      }
    )
  }

  public getClient(): AxiosInstance {
    return this.client
  }
}

export const apiClient = new APIClient().getClient()
export default apiClient
