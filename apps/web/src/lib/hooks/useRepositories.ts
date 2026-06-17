"use client"

import { useCallback, useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { AnalysisJob, CodeFile, Repository } from "@/lib/types"

export function useRepositories(projectId: string) {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)

  const refetch = useCallback(async () => {
    try {
      const data = await api.get<Repository[]>(`/api/v1/projects/${projectId}/repositories`)
      setRepositories(data)
    } catch {
      // ignore
    }
  }, [projectId])

  useEffect(() => {
    setLoading(true)
    refetch().finally(() => setLoading(false))
  }, [refetch])

  const addRepository = useCallback(
    async (name: string, localPath: string): Promise<AnalysisJob> => {
      const job = await api.post<AnalysisJob>(
        `/api/v1/projects/${projectId}/repositories`,
        { name, local_path: localPath }
      )
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

  return { repositories, loading, addRepository, deleteRepository, getFiles, refetch }
}
