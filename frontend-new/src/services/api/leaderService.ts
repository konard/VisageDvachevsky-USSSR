import apiClient from './client'
import { Leader, Fact, LeaderWithFacts } from '@/types/leader'

export const leaderService = {
  // Get all leaders
  async getAll(): Promise<Leader[]> {
    const response = await apiClient.get<Leader[]>('/leaders')
    return response.data
  },

  // Get leader by ID
  async getById(id: number): Promise<Leader> {
    const response = await apiClient.get<Leader>(`/leaders/${id}`)
    return response.data
  },

  // Get leader with facts
  async getWithFacts(id: number): Promise<LeaderWithFacts> {
    const [leader, factsResponse] = await Promise.all([
      this.getById(id),
      this.getFacts(id),
    ])
    return {
      ...leader,
      facts: factsResponse,
    }
  },

  // Get AI-generated facts for a leader
  async getFacts(leaderId: number): Promise<Fact[]> {
    const response = await apiClient.get<{ facts: Fact[] }>(`/leaders/${leaderId}/facts`)
    return response.data.facts
  },

  // Search leaders
  async search(query: string): Promise<Leader[]> {
    const response = await apiClient.get<{ results: Leader[] }>('/leaders/search', {
      params: { q: query },
    })
    return response.data.results
  },

  // Create new leader (admin only)
  async create(leader: Omit<Leader, 'id' | 'created_at' | 'updated_at'>): Promise<Leader> {
    const response = await apiClient.post<Leader>('/leaders', leader)
    return response.data
  },

  // Update leader (admin/editor only)
  async update(id: number, leader: Partial<Leader>): Promise<Leader> {
    const response = await apiClient.put<Leader>(`/leaders/${id}`, leader)
    return response.data
  },

  // Delete leader (admin only)
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/leaders/${id}`)
  },

  // Get video URL for leader
  getVideoUrl(videoId: number): string {
    return `${apiClient.defaults.baseURL?.replace('/api/v1', '')}/videos/${videoId}.mp4`
  },
}

export default leaderService
