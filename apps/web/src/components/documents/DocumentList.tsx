"use client"

import { useState } from "react"
import { JobProgress } from "@/components/jobs/JobProgress"
import { Button } from "@/components/ui/button"
import type { Document } from "@/lib/types"

interface Props {
  documents: Document[]
  docJobMap: Record<string, string>
  onDelete: (id: string) => void
  onJobComplete: () => void
}

const statusBadge: Record<string, string> = {
  uploaded: "bg-muted text-muted-foreground",
  processing: "bg-blue-100 text-blue-700",
  processed: "bg-green-100 text-green-700",
  error: "bg-red-100 text-red-700",
}

function formatSize(bytes: number | null): string {
  if (!bytes) return "—"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function DocumentList({ documents, docJobMap, onDelete, onJobComplete }: Props) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await onDelete(id)
    } finally {
      setDeletingId(null)
    }
  }

  if (documents.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground text-sm border rounded-lg bg-muted/20">
        No documents yet — upload one above
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {documents.map((doc) => {
        const jobId = docJobMap[doc.id]
        const showProgress = jobId && (doc.status === "uploaded" || doc.status === "processing")

        return (
          <div key={doc.id} className="border rounded-lg p-4 flex flex-col gap-2 bg-card">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-medium text-sm truncate">{doc.name}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${statusBadge[doc.status] ?? "bg-muted"}`}
                >
                  {doc.status}
                </span>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-muted-foreground">{formatSize(doc.file_size_bytes)}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive h-7 w-7 p-0"
                  loading={deletingId === doc.id}
                  onClick={() => handleDelete(doc.id)}
                >
                  ✕
                </Button>
              </div>
            </div>
            {showProgress && (
              <JobProgress jobId={jobId} onComplete={onJobComplete} />
            )}
          </div>
        )
      })}
    </div>
  )
}
