"use client"

import { JobProgress } from "@/components/jobs/JobProgress"
import { Button } from "@/components/ui/button"
import type { AnalysisJob, TraceLink } from "@/lib/types"

interface Props {
  projectId: string
  links: TraceLink[]
  loading: boolean
  linkJobId: string | null
  onGenerate: () => Promise<AnalysisJob>
  onJobStart: (jobId: string) => void
  onJobComplete: () => void
  onAccept: (linkId: string) => void
  onReject: (linkId: string) => void
  onDelete: (linkId: string) => void
}

const LANG_COLORS: Record<string, string> = {
  Python: "bg-blue-100 text-blue-700",
  TypeScript: "bg-indigo-100 text-indigo-700",
  JavaScript: "bg-yellow-100 text-yellow-700",
  Go: "bg-cyan-100 text-cyan-700",
  Rust: "bg-orange-100 text-orange-700",
  Java: "bg-red-100 text-red-700",
  SQL: "bg-purple-100 text-purple-700",
}

function confidenceColor(score: number): string {
  if (score >= 0.75) return "bg-green-500"
  if (score >= 0.55) return "bg-yellow-500"
  return "bg-orange-400"
}

function statusBadge(status: string) {
  switch (status) {
    case "validated":
      return <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">✓ validé</span>
    case "rejected":
      return <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">✗ rejeté</span>
    default:
      return <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">suggéré</span>
  }
}

export function TraceLinksView({
  links,
  loading,
  linkJobId,
  onGenerate,
  onJobStart,
  onJobComplete,
  onAccept,
  onReject,
  onDelete,
}: Props) {
  const handleGenerate = async () => {
    const job = await onGenerate()
    onJobStart(job.id)
  }

  // Group links by requirement
  const grouped = links.reduce<Record<string, TraceLink[]>>((acc, link) => {
    const key = link.source_id
    if (!acc[key]) acc[key] = []
    acc[key].push(link)
    return acc
  }, {})

  const reqGroups = Object.entries(grouped)
    .filter(([, groupLinks]) => groupLinks.length > 0)
    .map(([, groupLinks]) => ({
      code: groupLinks[0]?.requirement_code ?? "—",
      title: groupLinks[0]?.requirement_title ?? "Exigence inconnue",
      links: groupLinks.sort((a, b) => (b.confidence_score ?? 0) - (a.confidence_score ?? 0)),
    })).sort((a, b) => a.code.localeCompare(b.code))

  const suggested = links.filter((l) => l.status === "suggested").length
  const validated = links.filter((l) => l.status === "validated").length
  const rejected = links.filter((l) => l.status === "rejected").length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {links.length > 0 && (
            <>
              <span>{links.length} lien{links.length !== 1 ? "s" : ""}</span>
              {suggested > 0 && <span className="text-blue-600">{suggested} à réviser</span>}
              {validated > 0 && <span className="text-green-600">{validated} validé{validated !== 1 ? "s" : ""}</span>}
              {rejected > 0 && <span className="text-red-600">{rejected} rejeté{rejected !== 1 ? "s" : ""}</span>}
            </>
          )}
        </div>
        <Button size="sm" onClick={handleGenerate} disabled={!!linkJobId}>
          {linkJobId ? "Génération…" : "Générer les liens"}
        </Button>
      </div>

      {linkJobId && (
        <div className="border rounded-lg p-4 bg-blue-50">
          <p className="text-sm font-medium mb-2">Calcul des liens de traçabilité…</p>
          <JobProgress
            jobId={linkJobId}
            onComplete={onJobComplete}
            onCancel={() => onJobComplete()}
          />
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="h-6 w-6 animate-spin border-2 border-primary border-t-transparent rounded-full" />
        </div>
      ) : links.length === 0 ? (
        <div className="text-center py-12 border rounded-lg border-dashed">
          <p className="text-muted-foreground text-sm">Aucun lien de traçabilité.</p>
          <p className="text-muted-foreground text-xs mt-1">
            Cliquez sur &quot;Générer les liens&quot; pour relier automatiquement vos exigences au code.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {reqGroups.map(({ code, title, links: reqLinks }) => (
            <div key={code} className="border rounded-lg p-4">
              <div className="mb-3">
                <span className="text-xs font-mono text-muted-foreground">{code}</span>
                <p className="text-sm font-medium">{title}</p>
              </div>
              <div className="flex flex-col gap-2">
                {reqLinks.map((link) => (
                  <div
                    key={link.id}
                    className={`border rounded-md p-3 ${
                      link.status === "rejected" ? "opacity-50" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <code className="text-xs text-foreground font-mono truncate max-w-[320px]">
                            {link.file_path}
                          </code>
                          {link.file_language && (
                            <span className={`text-xs px-1.5 py-0.5 rounded ${LANG_COLORS[link.file_language] ?? "bg-muted text-muted-foreground"}`}>
                              {link.file_language}
                            </span>
                          )}
                          {statusBadge(link.status)}
                        </div>
                        {link.file_summary && (
                          <p className="text-xs text-muted-foreground line-clamp-2">{link.file_summary}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {link.confidence_score !== null && (
                          <div className="flex items-center gap-1.5">
                            <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${confidenceColor(link.confidence_score)}`}
                                style={{ width: `${Math.round(link.confidence_score * 100)}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground w-8 text-right">
                              {Math.round(link.confidence_score * 100)}%
                            </span>
                          </div>
                        )}
                        {link.status !== "validated" && link.status !== "rejected" && (
                          <>
                            <button
                              className="text-xs text-green-700 hover:text-green-900 font-medium"
                              onClick={() => onAccept(link.id)}
                            >
                              ✓
                            </button>
                            <button
                              className="text-xs text-red-600 hover:text-red-800 font-medium"
                              onClick={() => onReject(link.id)}
                            >
                              ✗
                            </button>
                          </>
                        )}
                        {(link.status === "validated" || link.status === "rejected") && (
                          <button
                            className="text-xs text-muted-foreground hover:text-foreground"
                            onClick={() => onDelete(link.id)}
                            title="Supprimer"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
