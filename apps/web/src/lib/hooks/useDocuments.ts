"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { AnalysisJob, Document } from "@/lib/types"

export function useDocuments(projectId: string) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const data = await api.get<Document[]>(`/api/v1/projects/${projectId}/documents`)
      setDocuments(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [projectId])

  const uploadDocument = async (file: File): Promise<AnalysisJob> => {
    const formData = new FormData()
    formData.append("file", file)
    const job = await api.upload<AnalysisJob>(
      `/api/v1/projects/${projectId}/documents`,
      formData,
    )
    await fetchDocuments()
    return job
  }

  const deleteDocument = async (documentId: string) => {
    await api.delete(`/api/v1/projects/${projectId}/documents/${documentId}`)
    setDocuments((prev) => prev.filter((d) => d.id !== documentId))
  }

  return { documents, loading, error, uploadDocument, deleteDocument, refetch: fetchDocuments }
}
