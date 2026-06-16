"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { Project } from "@/lib/types"

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProjects = async () => {
    try {
      setLoading(true)
      const data = await api.get<Project[]>("/api/v1/projects")
      setProjects(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load projects")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const createProject = async (name: string, description?: string, domain?: string) => {
    const project = await api.post<Project>("/api/v1/projects", { name, description, domain })
    setProjects((prev) => [project, ...prev])
    return project
  }

  const deleteProject = async (id: string) => {
    await api.delete(`/api/v1/projects/${id}`)
    setProjects((prev) => prev.filter((p) => p.id !== id))
  }

  return { projects, loading, error, createProject, deleteProject, refetch: fetchProjects }
}
