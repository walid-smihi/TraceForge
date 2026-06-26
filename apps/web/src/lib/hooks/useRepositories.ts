"use client"

import { useCallback, useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { AnalysisJob, CodeFile, Repository } from "@/lib/types"

export function useRepositories(projectId: string) {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    try {
      const data = await api.get<Repository[]>(`/api/v1/projects/${projectId}/repositories`)
      setRepositories(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load repositories")
    }
  }, [projectId])

  useEffect(() => {
    setLoading(true)
    refetch().finally(() => setLoading(false))
  }, [refetch])

  const addRepository = useCallback(
    async (
      name: string,
      source: { localPath?: string; githubUrl?: string }
    ): Promise<AnalysisJob> => {
      const job = await api.post<AnalysisJob>(`/api/v1/projects/${projectId}/repositories`, {
        name,
        local_path: source.localPath,
        github_url: source.githubUrl,
      })
      await refetch()
      return job
    },
    [projectId, refetch]
  )

  const deleteRepository = useCallback(
    async (repoId: string) => {
      await api.delete(`/api/v1/projects/${projectId}/repositories/${repoId}`)
      await refetch()
    },
    [projectId, refetch]
  )

  const getFiles = useCallback(
    async (repoId: string): Promise<CodeFile[]> => {
      return api.get<CodeFile[]>(`/api/v1/projects/${projectId}/repositories/${repoId}/files`)
    },
    [projectId]
  )

  return { repositories, loading, error, addRepository, deleteRepository, getFiles, refetch }
}
