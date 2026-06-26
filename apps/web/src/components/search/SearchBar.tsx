"use client"

import { FormEvent, useState } from "react"

import { useSearch } from "@/lib/hooks/useSearch"

interface Props {
  projectId: string
}

const TYPE_LABELS: Record<string, string> = {
  requirement: "Exigence",
  code_file: "Fichier",
}

function scoreColor(score: number): string {
  if (score >= 0.7) return "bg-green-500"
  if (score >= 0.5) return "bg-yellow-500"
  return "bg-orange-400"
}

export function SearchBar({ projectId }: Props) {
  const { results, loading, error, search, clear } = useSearch(projectId)
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setOpen(true)
    await search(query)
  }

  const handleClose = () => {
    setOpen(false)
    setQuery("")
    clear()
  }

  return (
    <div className="relative w-full sm:w-72">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Recherche sémantique…"
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
        />
      </form>

      {open && (
        <div className="absolute right-0 mt-1 w-96 border rounded-lg bg-background shadow-lg z-20 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between px-3 py-2 border-b">
            <span className="text-xs text-muted-foreground">
              {loading ? "Recherche…" : `${results.length} résultat${results.length !== 1 ? "s" : ""}`}
            </span>
            <button className="text-xs text-muted-foreground hover:text-foreground" onClick={handleClose}>
              Fermer
            </button>
          </div>

          {error && <p className="text-sm text-destructive p-3">{error}</p>}

          {!loading && !error && results.length === 0 && (
            <p className="text-sm text-muted-foreground p-3">Aucun résultat pertinent.</p>
          )}

          <div className="flex flex-col">
            {results.map((r) => (
              <div key={`${r.type}-${r.id}`} className="px-3 py-2 border-b last:border-b-0">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground shrink-0">
                      {TYPE_LABELS[r.type]}
                    </span>
                    <code className="text-xs font-mono truncate">{r.code}</code>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div className="w-10 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${scoreColor(r.score)}`}
                        style={{ width: `${Math.round(r.score * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{Math.round(r.score * 100)}%</span>
                  </div>
                </div>
                <p className="text-sm font-medium">{r.title}</p>
                {r.summary && <p className="text-xs text-muted-foreground line-clamp-2">{r.summary}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
