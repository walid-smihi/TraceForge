"use client"

import { useCallback, useEffect, useState } from "react"

import { api } from "@/lib/api"
import type { DetectedConflict } from "@/lib/types"

export function useConflicts(projectId: string) {
  const [conflicts, setConflicts] = useState<DetectedConflict[]>([])
  const [loading, setLoading] = useState(true)

  const refetch = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<DetectedConflict[]>(`/api/v1/projects/${projectId}/conflicts`)
      setConflicts(data)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    refetch()
  }, [refetch])

  const detectConflicts = async (): Promise<DetectedConflict[]> => {
    const data = await api.post<DetectedConflict[]>(
      `/api/v1/projects/${projectId}/conflicts/detect`,
      {}
    )
    setConflicts(data)
    return data
  }

  const updateConflict = async (
    conflictId: string,
    status: string
  ): Promise<DetectedConflict> => {
    const updated = await api.patch<DetectedConflict>(
      `/api/v1/projects/${projectId}/conflicts/${conflictId}`,
      { status }
    )
    setConflicts((prev) => prev.map((c) => (c.id === conflictId ? updated : c)))
    return updated
  }

  return { conflicts, loading, detectConflicts, updateConflict, refetch }
}
