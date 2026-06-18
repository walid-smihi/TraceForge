"use client"

import { FormEvent, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import type { Requirement } from "@/lib/types"

const REQ_TYPES = ["functional", "security", "performance", "availability", "compliance", "interface"]
const PRIORITIES = ["critical", "high", "medium", "low"]

interface Props {
  open: boolean
  onClose: () => void
  onSave: (data: { title: string; description?: string | undefined; req_type: string; priority: string }) => Promise<void>
  initial?: Requirement | null
}

export function RequirementForm({ open, onClose, onSave, initial }: Props) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [reqType, setReqType] = useState("functional")
  const [priority, setPriority] = useState("medium")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (initial) {
      setTitle(initial.title)
      setDescription(initial.description ?? "")
      setReqType(initial.req_type)
      setPriority(initial.priority)
    } else {
      setTitle("")
      setDescription("")
      setReqType("functional")
      setPriority("medium")
    }
    setError(null)
  }, [initial, open])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true)
    setError(null)
    try {
      await onSave({ title: title.trim(), description: description.trim() || undefined, req_type: reqType, priority })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title={initial ? "Modifier l'exigence" : "Nouvelle exigence"}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input label="Titre" value={title} onChange={(e) => setTitle(e.target.value)} required autoFocus />
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            placeholder="Description de l'exigence..."
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium">Type</label>
            <select value={reqType} onChange={(e) => setReqType(e.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
              {REQ_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium">Priorité</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
              {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
          <Button type="submit" loading={loading} disabled={!title.trim()}>{initial ? "Modifier" : "Créer"}</Button>
        </div>
      </form>
    </Dialog>
  )
}
