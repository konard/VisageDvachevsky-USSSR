import { create } from 'zustand'
import { User } from '@/types/user'
import authService from '@/services/api/authService'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User | null) => void
  setIsAuthenticated: (isAuthenticated: boolean) => void
  setIsLoading: (isLoading: boolean) => void
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
  checkAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => set({ user }),
  setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  setIsLoading: (isLoading) => set({ isLoading }),

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      await authService.login({ email, password })
      const user = await authService.getCurrentUser()
      set({ user, isAuthenticated: true })
    } finally {
      set({ isLoading: false })
    }
  },

  logout: async () => {
    set({ isLoading: true })
    try {
      await authService.logout()
    } finally {
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },

  fetchCurrentUser: async () => {
    if (!authService.isAuthenticated()) {
      set({ isLoading: false })
      return
    }

    set({ isLoading: true })
    try {
      const user = await authService.getCurrentUser()
      set({ user, isAuthenticated: true })
    } catch (error) {
      set({ user: null, isAuthenticated: false })
    } finally {
      set({ isLoading: false })
    }
  },

  checkAuth: () => {
    const isAuthenticated = authService.isAuthenticated()
    set({ isAuthenticated })
  },
}))

export default useAuthStore
