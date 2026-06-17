import { useCallback, useEffect, useState } from "react"

import { api } from "@/lib/api"
import type { AnalysisJob, TraceLink } from "@/lib/types"

export function useTraceLinks(projectId: string) {
  const [links, setLinks] = useState<TraceLink[]>([])
  const [loading, setLoading] = useState(false)

  const refetch = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<TraceLink[]>(`/api/v1/projects/${projectId}/trace-links`)
      setLinks(data)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    refetch()
  }, [refetch])

  const generateLinks = async (): Promise<AnalysisJob> => {
    return api.post<AnalysisJob>(`/api/v1/projects/${projectId}/trace-links/generate`, {})
  }

  const updateLink = async (linkId: string, status: string): Promise<TraceLink> => {
    const updated = await api.patch<TraceLink>(
      `/api/v1/projects/${projectId}/trace-links/${linkId}`,
      { status }
    )
    setLinks((prev) => prev.map((l) => (l.id === linkId ? updated : l)))
    return updated
  }

  const deleteLink = async (linkId: string): Promise<void> => {
    await api.delete(`/api/v1/projects/${projectId}/trace-links/${linkId}`)
    setLinks((prev) => prev.filter((l) => l.id !== linkId))
  }

  return { links, loading, generateLinks, updateLink, deleteLink, refetch }
}
