import type { ProjectMetrics } from "@/lib/types"

interface Props {
  metrics: ProjectMetrics
}

function coverageColor(pct: number): string {
  if (pct >= 80) return "text-green-600"
  if (pct >= 50) return "text-yellow-600"
  return "text-red-600"
}

export function MetricsBar({ metrics }: Props) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div className="border rounded-lg p-3">
        <p className={`text-2xl font-bold ${coverageColor(metrics.coverage_percent)}`}>
          {metrics.coverage_percent}%
        </p>
        <p className="text-xs text-muted-foreground">Couverture exigences</p>
      </div>
      <div className="border rounded-lg p-3">
        <p className="text-2xl font-bold">{metrics.requirements_unlinked}</p>
        <p className="text-xs text-muted-foreground">Exigences non liées</p>
      </div>
      <div className="border rounded-lg p-3">
        <p className="text-2xl font-bold text-orange-600">{metrics.requirements_ambiguous}</p>
        <p className="text-xs text-muted-foreground">Exigences ambiguës</p>
      </div>
      <div className="border rounded-lg p-3">
        <p className="text-2xl font-bold">{metrics.links_validated}/{metrics.links_total}</p>
        <p className="text-xs text-muted-foreground">Liens validés</p>
      </div>
    </div>
  )
}
