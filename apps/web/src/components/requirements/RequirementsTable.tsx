"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { Requirement } from "@/lib/types"

interface Props {
  requirements: Requirement[]
  onEdit: (req: Requirement) => void
  onDelete: (id: string) => void
}

const TYPE_COLORS: Record<string, string> = {
  functional: "bg-blue-100 text-blue-700",
  security: "bg-red-100 text-red-700",
  performance: "bg-orange-100 text-orange-700",
  availability: "bg-purple-100 text-purple-700",
  compliance: "bg-yellow-100 text-yellow-700",
  interface: "bg-teal-100 text-teal-700",
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-500 text-white",
  high: "bg-orange-400 text-white",
  medium: "bg-yellow-400 text-white",
  low: "bg-green-400 text-white",
}

const REQ_TYPES = ["functional", "security", "performance", "availability", "compliance", "interface"]
const PRIORITIES = ["critical", "high", "medium", "low"]

export function RequirementsTable({ requirements, onEdit, onDelete }: Props) {
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState("")
  const [priorityFilter, setPriorityFilter] = useState("")
  const [ambiguousOnly, setAmbiguousOnly] = useState(false)

  const filtered = requirements.filter((r) => {
    if (typeFilter && r.req_type !== typeFilter) return false
    if (priorityFilter && r.priority !== priorityFilter) return false
    if (ambiguousOnly && !r.is_ambiguous) return false
    if (search) {
      const s = search.toLowerCase()
      return r.title.toLowerCase().includes(s) || r.code.toLowerCase().includes(s) || (r.description ?? "").toLowerCase().includes(s)
    }
    return true
  })

  if (requirements.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground text-sm border rounded-lg bg-muted/20">
        Aucune exigence — extrayez depuis un document ou créez-en une manuellement
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <div className="flex-1 min-w-48">
          <Input
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">Tous les types</option>
          {REQ_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">Toutes priorités</option>
          {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <Button
          variant={ambiguousOnly ? "primary" : "secondary"}
          size="sm"
          onClick={() => setAmbiguousOnly(!ambiguousOnly)}
        >
          ⚠ Ambiguës {ambiguousOnly ? "✓" : ""}
        </Button>
        <span className="text-xs text-muted-foreground ml-auto">
          {filtered.length} / {requirements.length}
        </span>
      </div>

      {/* Table */}
      <div className="rounded-lg border overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-muted-foreground w-24">Code</th>
              <th className="text-left px-3 py-2 font-medium text-muted-foreground">Titre</th>
              <th className="text-left px-3 py-2 font-medium text-muted-foreground w-28">Type</th>
              <th className="text-left px-3 py-2 font-medium text-muted-foreground w-24">Priorité</th>
              <th className="text-left px-3 py-2 font-medium text-muted-foreground w-20">Statut</th>
              <th className="w-16"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((req) => (
              <tr key={req.id} className="border-t hover:bg-muted/20 transition-colors">
                <td className="px-3 py-2.5 font-mono text-xs font-medium">{req.code}</td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <span className="line-clamp-1">{req.title}</span>
                    {req.is_ambiguous && (
                      <span title={req.ambiguity_reason ?? ""} className="text-orange-500 shrink-0 cursor-help">⚠</span>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[req.req_type] ?? "bg-muted"}`}>
                    {req.req_type}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_COLORS[req.priority] ?? "bg-muted"}`}>
                    {req.priority}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-xs text-muted-foreground">{req.status}</td>
                <td className="px-3 py-2.5">
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-xs" onClick={() => onEdit(req)}>✎</Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-xs text-muted-foreground hover:text-destructive" onClick={() => onDelete(req.id)}>✕</Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="py-8 text-center text-muted-foreground text-sm">
            Aucun résultat pour ces filtres
          </div>
        )}
      </div>
    </div>
  )
}
