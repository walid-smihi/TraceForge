"use client"

import { FormEvent, useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

interface Props {
  open: boolean
  onClose: () => void
  onCreate: (name: string, description?: string, domain?: string) => Promise<void>
}

export function CreateProjectDialog({ open, onClose, onCreate }: Props) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [domain, setDomain] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError(null)
    try {
      await onCreate(name.trim(), description.trim() || undefined, domain.trim() || undefined)
      setName("")
      setDescription("")
      setDomain("")
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="New Project">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Name"
          placeholder="My project"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
        />
        <Input
          label="Description (optional)"
          placeholder="What is this project about?"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Input
          label="Domain (optional)"
          placeholder="e.g. finance, healthcare"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading} disabled={!name.trim()}>
            Create
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
