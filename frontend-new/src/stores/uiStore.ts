import { create } from 'zustand'

interface UIState {
  // Modal states
  isLeaderModalOpen: boolean
  isVideoModalOpen: boolean
  isAuthModalOpen: boolean
  selectedLeaderId: number | null

  // UI preferences
  theme: 'light' | 'dark'
  sidebarOpen: boolean

  // Loading states
  isGlobalLoading: boolean

  // Actions
  openLeaderModal: (leaderId: number) => void
  closeLeaderModal: () => void
  openVideoModal: (leaderId: number) => void
  closeVideoModal: () => void
  openAuthModal: () => void
  closeAuthModal: () => void
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  setGlobalLoading: (isLoading: boolean) => void
}

export const useUIStore = create<UIState>((set) => ({
  // Initial states
  isLeaderModalOpen: false,
  isVideoModalOpen: false,
  isAuthModalOpen: false,
  selectedLeaderId: null,
  theme: 'light',
  sidebarOpen: false,
  isGlobalLoading: false,

  // Actions
  openLeaderModal: (leaderId) => set({ isLeaderModalOpen: true, selectedLeaderId: leaderId }),
  closeLeaderModal: () => set({ isLeaderModalOpen: false, selectedLeaderId: null }),

  openVideoModal: (leaderId) => set({ isVideoModalOpen: true, selectedLeaderId: leaderId }),
  closeVideoModal: () => set({ isVideoModalOpen: false, selectedLeaderId: null }),

  openAuthModal: () => set({ isAuthModalOpen: true }),
  closeAuthModal: () => set({ isAuthModalOpen: false }),

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
  setGlobalLoading: (isLoading) => set({ isGlobalLoading: isLoading }),
}))

export default useUIStore
