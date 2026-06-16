"use client"

import { useJobProgress } from "@/lib/hooks/useJobProgress"

interface Props {
  jobId: string
  onComplete?: () => void
}

const statusLabel: Record<string, string> = {
  pending: "Queued",
  running: "Processing",
  completed: "Done",
  failed: "Failed",
}

const statusColor: Record<string, string> = {
  pending: "text-muted-foreground",
  running: "text-blue-600",
  completed: "text-green-600",
  failed: "text-destructive",
}

export function JobProgress({ jobId, onComplete }: Props) {
  const job = useJobProgress(jobId, onComplete)

  if (!job) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="h-3 w-3 animate-spin border border-muted-foreground border-t-transparent rounded-full" />
        Loading…
      </div>
    )
  }

  const isRunning = job.status === "pending" || job.status === "running"

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className={statusColor[job.status] ?? "text-foreground"}>
          {statusLabel[job.status] ?? job.status}
        </span>
        <span className="text-muted-foreground">{job.progress}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full transition-all duration-500 rounded-full ${
            job.status === "failed"
              ? "bg-destructive"
              : job.status === "completed"
              ? "bg-green-500"
              : "bg-blue-500"
          }`}
          style={{ width: `${job.progress}%` }}
        />
      </div>
      {isRunning && (
        <p className="text-xs text-muted-foreground">Extracting text and chunking document…</p>
      )}
      {job.status === "failed" && job.error_message && (
        <p className="text-xs text-destructive">{job.error_message}</p>
      )}
    </div>
  )
}
