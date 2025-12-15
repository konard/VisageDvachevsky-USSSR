export interface Leader {
  id: number
  name_ru: string
  name_en: string
  birth_year: number
  birth_place: string
  death_year: number | null
  death_place: string | null
  position: string
  achievements: string
  biography?: string
  video_id: number
  portrait_url?: string
  created_at?: string
  updated_at?: string
}

export interface Fact {
  id: number
  leader_id: number
  fact_text: string
  category?: string
  is_verified: boolean
  created_at: string
}

export interface LeaderWithFacts extends Leader {
  facts: Fact[]
}

export interface LeaderStats {
  total_views: number
  total_likes: number
  total_bookmarks: number
  total_comments: number
}

export interface LeaderComparisonData {
  leader1: Leader
  leader2: Leader
  comparison: {
    years_ruled_diff: number
    age_diff: number
    birth_era_diff: number
  }
}
