"use client"

import { useEffect, useState } from "react"
import { API_URL } from "@/lib/api"

export function LlmStatusBanner() {
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/health/llm`)
      .then((r) => r.json())
      .then((d) => { if (!d.available) setUnavailable(true) })
      .catch(() => {})
  }, [])

  if (!unavailable) return null

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-6 py-2 text-sm text-amber-800 flex items-center gap-2">
      <span>⚠</span>
      <span>
        Ollama est inaccessible — l&apos;extraction d&apos;exigences ne fonctionnera pas.
        Démarrez Ollama pour activer l&apos;analyse IA.
      </span>
    </div>
  )
}
