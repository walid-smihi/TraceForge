"use client"

import { useState } from "react"

import { JobProgress } from "@/components/jobs/JobProgress"
import { Button } from "@/components/ui/button"
import { useImpact } from "@/lib/hooks/useImpact"
import type { ImpactReport, Requirement } from "@/lib/types"

interface Props {
  projectId: string
  requirements: Requirement[]
}

export function ImpactView({ projectId, requirements }: Props) {
  const { analyzeImpact, getReport, exportUrl } = useImpact(projectId)
  const [requirementId, setRequirementId] = useState("")
  const [modification, setModification] = useState("")
  const [jobId, setJobId] = useState<string | null>(null)
  const [report, setReport] = useState<ImpactReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const handleAnalyze = async () => {
    if (!requirementId || !modification.trim()) return
    setError(null)
    setReport(null)
    setAnalyzing(true)
    try {
      const job = await analyzeImpact(requirementId, modification.trim())
      setJobId(job.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur")
      setAnalyzing(false)
    }
  }

  const handleJobComplete = async () => {
    setAnalyzing(false)
    if (!jobId) return
    try {
      const data = await getReport(jobId)
      setReport(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Impossible de charger le rapport")
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="border rounded-lg p-4 flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Exigence à modifier</label>
          <select
            value={requirementId}
            onChange={(e) => setRequirementId(e.target.value)}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">— Choisir une exigence —</option>
            {requirements.map((r) => (
              <option key={r.id} value={r.id}>
                {r.code} — {r.title}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Modification envisagée</label>
          <textarea
            value={modification}
            onChange={(e) => setModification(e.target.value)}
            rows={3}
            placeholder="Décrivez la modification envisagée sur cette exigence…"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none"
          />
        </div>
        <Button
          size="sm"
          className="self-start"
          disabled={!requirementId || !modification.trim() || analyzing}
          onClick={handleAnalyze}
        >
          {analyzing ? "Analyse en cours…" : "Analyser l'impact"}
        </Button>

        {jobId && analyzing && (
          <JobProgress jobId={jobId} onComplete={handleJobComplete} onCancel={() => setAnalyzing(false)} />
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      {report && (
        <div className="border rounded-lg p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              Rapport d&apos;impact — {report.requirement.code}
            </h3>
            <div className="flex items-center gap-2">
              <a
                href={exportUrl(jobId!, "md")}
                className="text-xs text-muted-foreground hover:underline"
              >
                Export Markdown
              </a>
              <a
                href={exportUrl(jobId!, "pdf")}
                className="text-xs text-muted-foreground hover:underline"
              >
                Export PDF
              </a>
            </div>
          </div>

          {report.summary && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Résumé</p>
              <p className="text-sm">{report.summary}</p>
            </div>
          )}

          <Section title={`Fichiers directement impactés (${report.direct_files.length})`}>
            {report.direct_files.map((f) => (
              <li key={f.path}>
                <code className="font-mono">{f.path}</code>
                {f.summary && <span className="text-muted-foreground"> — {f.summary}</span>}
              </li>
            ))}
          </Section>

          <Section title={`Tests directement impactés (${report.direct_tests.length})`}>
            {report.direct_tests.map((f) => (
              <li key={f.path}>
                <code className="font-mono">{f.path}</code>
              </li>
            ))}
          </Section>

          <Section
            title={`Exigences indirectement impactées (${report.indirect_requirements.length})`}
          >
            {report.indirect_requirements.map((r) => (
              <li key={r.code}>
                {r.code} — {r.title}
              </li>
            ))}
          </Section>

          <Section title={`Conflits ouverts (${report.conflicts.length})`}>
            {report.conflicts.map((c, i) => (
              <li key={i} className="text-orange-600">
                <span className="font-medium">{c.rule_id}</span> — {c.title}
              </li>
            ))}
          </Section>
        </div>
      )}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const items = Array.isArray(children) ? children : [children]
  const hasItems = items.some(Boolean)
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground mb-1">{title}</p>
      {hasItems ? (
        <ul className="text-sm list-disc pl-5 flex flex-col gap-0.5">{children}</ul>
      ) : (
        <p className="text-sm text-muted-foreground">Aucun.</p>
      )}
    </div>
  )
}
