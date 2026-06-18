"use client"

import { useCallback, useEffect, useState } from "react"

import { api } from "@/lib/api"
import type { GraphData, ProjectMetrics } from "@/lib/types"

export function useGraph(projectId: string) {
  const [graph, setGraph] = useState<GraphData | null>(null)
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    try {
      const [g, m] = await Promise.all([
        api.get<GraphData>(`/api/v1/projects/${projectId}/graph`),
        api.get<ProjectMetrics>(`/api/v1/projects/${projectId}/metrics`),
      ])
      setGraph(g)
      setMetrics(m)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load graph")
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    refetch()
  }, [refetch])

  return { graph, metrics, loading, error, refetch }
}
