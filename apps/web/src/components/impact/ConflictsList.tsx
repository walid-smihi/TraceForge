"use client"

import { useState } from "react"

import { Button } from "@/components/ui/button"
import { ErrorBanner } from "@/components/ui/error-banner"
import type { DetectedConflict } from "@/lib/types"

interface Props {
  conflicts: DetectedConflict[]
  loading: boolean
  error?: string | null
  onDetect: () => Promise<DetectedConflict[]>
  onResolve: (id: string) => Promise<unknown>
  onRetry?: () => void
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  warning: "bg-orange-100 text-orange-700",
  info: "bg-blue-100 text-blue-700",
}

export function ConflictsList({ conflicts, loading, error, onDetect, onResolve, onRetry }: Props) {
  const [actionError, setActionError] = useState<string | null>(null)
  const [detecting, setDetecting] = useState(false)
  const [lastDetectMessage, setLastDetectMessage] = useState<string | null>(null)
  const open = conflicts.filter((c) => c.status === "open")

  const handleDetect = async () => {
    setActionError(null)
    setLastDetectMessage(null)
    setDetecting(true)
    try {
      const result = await onDetect()
      const openCount = result.filter((c) => c.status === "open").length
      setLastDetectMessage(
        openCount > 0
          ? `Détection terminée — ${openCount} conflit${openCount !== 1 ? "s" : ""} ouvert${openCount !== 1 ? "s" : ""}.`
          : "Détection terminée — aucun conflit trouvé."
      )
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "La détection a échoué")
    } finally {
      setDetecting(false)
    }
  }

  const handleResolve = async (id: string) => {
    setActionError(null)
    try {
      await onResolve(id)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Impossible de résoudre ce conflit")
    }
  }

  return (
    <div className="border rounded-lg p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">
          Conflits détectés {open.length > 0 && <span className="text-red-600">({open.length} ouverts)</span>}
        </p>
        <Button size="sm" variant="secondary" onClick={handleDetect} disabled={loading || detecting}>
          {detecting ? "Détection…" : "Relancer la détection"}
        </Button>
      </div>

      {actionError && <ErrorBanner message={actionError} />}
      {lastDetectMessage && !actionError && (
        <p className="text-xs text-muted-foreground">{lastDetectMessage}</p>
      )}

      {error ? (
        <ErrorBanner message={error} onRetry={onRetry} />
      ) : open.length === 0 ? (
        <p className="text-sm text-muted-foreground">Aucun conflit ouvert.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {open.map((c) => (
            <div key={c.id} className="border rounded-md p-3 flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {c.rule_id && (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${SEVERITY_COLORS[c.severity] ?? ""}`}>
                      {c.rule_id}
                    </span>
                  )}
                  <span className="text-sm font-medium">{c.title}</span>
                </div>
                {c.description && <p className="text-xs text-muted-foreground">{c.description}</p>}
              </div>
              <Button size="sm" variant="ghost" onClick={() => handleResolve(c.id)}>
                Marquer résolu
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
