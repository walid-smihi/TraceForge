"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

interface Props {
  open: boolean
  onClose: () => void
  onSave: (name: string, localPath: string) => Promise<void>
}

export function RepositoryForm({ open, onClose, onSave }: Props) {
  const [name, setName] = useState("")
  const [localPath, setLocalPath] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !localPath.trim()) return
    setLoading(true)
    setError(null)
    try {
      await onSave(name.trim(), localPath.trim())
      setName("")
      setLocalPath("")
      onClose()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erreur lors de l'ajout"
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Connecter un dépôt local">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium">Nom du dépôt</label>
          <Input
            placeholder="ex: backend-api"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium">Chemin absolu</label>
          <Input
            placeholder="ex: /home/walid/mon-projet"
            value={localPath}
            onChange={(e) => setLocalPath(e.target.value)}
            required
          />
          <p className="text-xs text-muted-foreground">
            Chemin sur votre machine vers le dossier racine du projet.
          </p>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={loading}>
            Scanner
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
