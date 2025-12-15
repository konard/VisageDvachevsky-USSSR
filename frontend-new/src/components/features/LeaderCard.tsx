import React from 'react'
import { motion } from 'framer-motion'
import { Leader } from '@/types/leader'
import { FaPlay, FaInfoCircle } from 'react-icons/fa'
import Button from '@/components/ui/Button'

interface LeaderCardProps {
  leader: Leader
  onDetailsClick: (leaderId: number) => void
  onVideoClick: (leaderId: number) => void
}

export const LeaderCard: React.FC<LeaderCardProps> = ({
  leader,
  onDetailsClick,
  onVideoClick,
}) => {
  const yearsLived = leader.death_year
    ? `${leader.birth_year}–${leader.death_year}`
    : `${leader.birth_year}–`

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
      className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl-soviet transition-all duration-300"
    >
      {/* Card Header with Gradient */}
      <div className="bg-soviet-gradient p-6 text-white">
        <h3 className="font-display text-2xl font-bold mb-2">{leader.name_ru}</h3>
        <p className="text-sm opacity-90">{leader.name_en}</p>
        <p className="text-sm opacity-80 mt-1">{yearsLived}</p>
      </div>

      {/* Card Body */}
      <div className="p-6">
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            <span className="font-semibold">Место рождения:</span> {leader.birth_place}
          </p>
          {leader.death_place && (
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-semibold">Место смерти:</span> {leader.death_place}
            </p>
          )}
          <p className="text-sm text-gray-700 font-medium mt-3">{leader.position}</p>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600 line-clamp-3">{leader.achievements}</p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            variant="primary"
            size="sm"
            fullWidth
            onClick={() => onDetailsClick(leader.id)}
            className="flex items-center justify-center gap-2"
          >
            <FaInfoCircle />
            Подробнее
          </Button>
          <Button
            variant="secondary"
            size="sm"
            fullWidth
            onClick={() => onVideoClick(leader.id)}
            className="flex items-center justify-center gap-2"
          >
            <FaPlay />
            Видео
          </Button>
        </div>
      </div>

      {/* Decorative Footer */}
      <div className="bg-gradient-to-r from-soviet-gold to-yellow-400 h-1" />
    </motion.div>
  )
}

export default LeaderCard
