"use client"

import { api } from "@/lib/api"
import type { AnalysisJob, ImpactReport } from "@/lib/types"

export function useImpact(projectId: string) {
  const analyzeImpact = async (
    requirementId: string,
    modificationDescription: string
  ): Promise<AnalysisJob> => {
    return api.post<AnalysisJob>(`/api/v1/projects/${projectId}/impact/analyze`, {
      requirement_id: requirementId,
      modification_description: modificationDescription,
    })
  }

  const getReport = async (jobId: string): Promise<ImpactReport> => {
    const job = await api.get<AnalysisJob>(`/api/v1/jobs/${jobId}`)
    return job.result_data as unknown as ImpactReport
  }

  const exportUrl = (jobId: string, format: "md" | "pdf"): string => {
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
    return `${base}/api/v1/projects/${projectId}/export/impact/${jobId}?format=${format}`
  }

  return { analyzeImpact, getReport, exportUrl }
}
