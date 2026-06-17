"use client"

import { useEffect, useRef, useState } from "react"
import { api } from "@/lib/api"
import type { AnalysisJob } from "@/lib/types"

export function useJobProgress(jobId: string | null, onComplete?: () => void) {
  const [job, setJob] = useState<AnalysisJob | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!jobId) return

    const poll = async () => {
      try {
        const data = await api.get<AnalysisJob>(`/api/v1/jobs/${jobId}`)
        setJob(data)
        if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
          clearInterval(intervalRef.current!)
          if (data.status === "completed") onComplete?.()
        }
      } catch {
        clearInterval(intervalRef.current!)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 2000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [jobId])

  return job
}
