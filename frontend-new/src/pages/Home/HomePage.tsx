import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import leaderService from '@/services/api/leaderService'
import LeaderCard from '@/components/features/LeaderCard'
import { useUIStore } from '@/stores/uiStore'

export const HomePage: React.FC = () => {
  const { openLeaderModal, openVideoModal } = useUIStore()

  const { data: leaders, isLoading, error } = useQuery({
    queryKey: ['leaders'],
    queryFn: leaderService.getAll,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-soviet-red mx-auto mb-4" />
          <p className="text-gray-600">Загрузка данных...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <p>Ошибка загрузки данных</p>
          <p className="text-sm mt-2">{(error as Error).message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-soviet-gradient py-20 px-4">
        <div className="container mx-auto text-center text-white">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-display text-5xl md:text-6xl font-bold mb-4"
          >
            Лица СССР
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl md:text-2xl opacity-90"
          >
            Интеллектуальная историческая платформа
          </motion.p>
        </div>
      </section>

      {/* Leaders Grid */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {leaders?.map((leader, index) => (
            <motion.div
              key={leader.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <LeaderCard
                leader={leader}
                onDetailsClick={openLeaderModal}
                onVideoClick={openVideoModal}
              />
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default HomePage
