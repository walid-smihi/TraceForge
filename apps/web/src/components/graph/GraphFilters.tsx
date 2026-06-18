import type { TraceLinkStatus } from "@/lib/types"

export interface FilterState {
  showRequirements: boolean
  showCodeFiles: boolean
  statuses: Set<TraceLinkStatus>
  hideTests: boolean
}

interface Props {
  filters: FilterState
  onChange: (filters: FilterState) => void
}

const STATUS_OPTIONS: { value: TraceLinkStatus; label: string }[] = [
  { value: "validated", label: "Validés" },
  { value: "suggested", label: "Suggérés" },
  { value: "rejected", label: "Rejetés" },
]

export function GraphFilters({ filters, onChange }: Props) {
  const toggleStatus = (status: TraceLinkStatus) => {
    const next = new Set(filters.statuses)
    if (next.has(status)) next.delete(status)
    else next.add(status)
    onChange({ ...filters, statuses: next })
  }

  return (
    <div className="flex items-center gap-4 flex-wrap text-sm">
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.showRequirements}
            onChange={(e) => onChange({ ...filters, showRequirements: e.target.checked })}
          />
          Exigences
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.showCodeFiles}
            onChange={(e) => onChange({ ...filters, showCodeFiles: e.target.checked })}
          />
          Fichiers de code
        </label>
      </div>

      <div className="h-4 w-px bg-border" />

      <div className="flex items-center gap-3">
        {STATUS_OPTIONS.map((opt) => (
          <label key={opt.value} className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.statuses.has(opt.value)}
              onChange={() => toggleStatus(opt.value)}
            />
            {opt.label}
          </label>
        ))}
      </div>

      <div className="h-4 w-px bg-border" />

      <label className="flex items-center gap-1.5 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.hideTests}
          onChange={(e) => onChange({ ...filters, hideTests: e.target.checked })}
        />
        Masquer les fichiers de test
      </label>
    </div>
  )
}
