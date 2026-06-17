"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useJobProgress } from "@/lib/hooks/useJobProgress"

interface Props {
  jobId: string
  label?: string
  onComplete?: () => void
  onCancel?: () => void
}

const statusLabel: Record<string, string> = {
  pending: "En attente",
  running: "En cours",
  completed: "Terminé",
  failed: "Échec",
  cancelled: "Annulé",
}

const statusColor: Record<string, string> = {
  pending: "text-muted-foreground",
  running: "text-blue-600",
  completed: "text-green-600",
  failed: "text-destructive",
  cancelled: "text-muted-foreground",
}

export function JobProgress({ jobId, label, onComplete, onCancel }: Props) {
  const [cancelling, setCancelling] = useState(false)
  const job = useJobProgress(jobId, onComplete)

  const handleCancel = async () => {
    setCancelling(true)
    try {
      await api.post(`/api/v1/jobs/${jobId}/cancel`, {})
      onCancel?.()
    } catch (e) {
      console.error("Cancel failed", e)
    } finally {
      setCancelling(false)
    }
  }

  if (!job) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="h-3 w-3 animate-spin border border-muted-foreground border-t-transparent rounded-full" />
        Chargement…
      </div>
    )
  }

  const isActive = job.status === "pending" || job.status === "running"
  const barColor =
    job.status === "failed" || job.status === "cancelled"
      ? "bg-destructive"
      : job.status === "completed"
      ? "bg-green-500"
      : "bg-blue-500"

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className={statusColor[job.status] ?? "text-foreground"}>
          {statusLabel[job.status] ?? job.status}
          {label && <span className="text-muted-foreground ml-1">— {label}</span>}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-xs">{job.progress}%</span>
          {isActive && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs text-muted-foreground hover:text-destructive"
              loading={cancelling}
              onClick={handleCancel}
            >
              Annuler
            </Button>
          )}
        </div>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full transition-all duration-500 rounded-full ${barColor}`}
          style={{ width: `${job.progress}%` }}
        />
      </div>
      {isActive && (
        <p className="text-xs text-muted-foreground">
          {job.job_type === "extract_requirements"
            ? "Analyse des chunks par le LLM…"
            : "Extraction du texte en cours…"}
        </p>
      )}
      {(job.status === "failed" || job.status === "cancelled") && job.error_message && (
        <p className="text-xs text-destructive">{job.error_message}</p>
      )}
    </div>
  )
}
