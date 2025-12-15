import React, { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import HomePage from '@/pages/Home/HomePage'
import { useAuthStore } from '@/stores/authStore'
import '@/styles/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  const { fetchCurrentUser } = useAuthStore()

  useEffect(() => {
    // Check authentication on app load
    fetchCurrentUser()
  }, [fetchCurrentUser])

  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        <HomePage />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#333',
              color: '#fff',
            },
            success: {
              iconTheme: {
                primary: '#FFD700',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#CC0000',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </QueryClientProvider>
  )
}

export default App
