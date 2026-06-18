"use client"

import { useCallback, useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { AnalysisJob, Requirement } from "@/lib/types"

interface Filters {
  req_type?: string
  priority?: string
  status?: string
  is_ambiguous?: boolean
  search?: string
}

export function useRequirements(projectId: string, filters: Filters = {}) {
  const [requirements, setRequirements] = useState<Requirement[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRequirements = useCallback(async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filters.req_type) params.set("req_type", filters.req_type)
      if (filters.priority) params.set("priority", filters.priority)
      if (filters.status) params.set("status", filters.status)
      if (filters.is_ambiguous !== undefined) params.set("is_ambiguous", String(filters.is_ambiguous))
      if (filters.search) params.set("search", filters.search)
      const qs = params.toString() ? `?${params}` : ""
      const data = await api.get<Requirement[]>(`/api/v1/projects/${projectId}/requirements${qs}`)
      setRequirements(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load requirements")
    } finally {
      setLoading(false)
    }
  }, [projectId, JSON.stringify(filters)])

  useEffect(() => { fetchRequirements() }, [fetchRequirements])

  const extractRequirements = async (documentId: string): Promise<AnalysisJob> => {
    const job = await api.post<AnalysisJob>(
      `/api/v1/projects/${projectId}/requirements/extract?document_id=${documentId}`,
      {}
    )
    return job
  }

  const createRequirement = async (data: { title: string; description?: string | undefined; req_type?: string; priority?: string }) => {
    const req = await api.post<Requirement>(`/api/v1/projects/${projectId}/requirements`, data)
    setRequirements((prev) => [...prev, req])
    return req
  }

  const updateRequirement = async (
    id: string,
    data: { title?: string; description?: string | undefined; req_type?: string; priority?: string; status?: string }
  ) => {
    const req = await api.patch<Requirement>(`/api/v1/projects/${projectId}/requirements/${id}`, data)
    setRequirements((prev) => prev.map((r) => (r.id === id ? req : r)))
    return req
  }

  const deleteRequirement = async (id: string) => {
    await api.delete(`/api/v1/projects/${projectId}/requirements/${id}`)
    setRequirements((prev) => prev.filter((r) => r.id !== id))
  }

  return { requirements, loading, error, extractRequirements, createRequirement, updateRequirement, deleteRequirement, refetch: fetchRequirements }
}
