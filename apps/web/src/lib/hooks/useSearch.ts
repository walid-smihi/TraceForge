"use client"

import { useState } from "react"

import { api } from "@/lib/api"
import type { SearchResult } from "@/lib/types"

export function useSearch(projectId: string) {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async (query: string) => {
    if (!query.trim()) {
      setResults([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<SearchResult[]>(
        `/api/v1/projects/${projectId}/search?q=${encodeURIComponent(query.trim())}`
      )
      setResults(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Recherche indisponible")
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const clear = () => {
    setResults([])
    setError(null)
  }

  return { results, loading, error, search, clear }
}
