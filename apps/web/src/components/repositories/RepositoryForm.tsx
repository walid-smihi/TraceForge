"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

interface Props {
  open: boolean
  onClose: () => void
  onSave: (name: string, source: { localPath?: string; githubUrl?: string }) => Promise<void>
}

type SourceMode = "local" | "github"

export function RepositoryForm({ open, onClose, onSave }: Props) {
  const [mode, setMode] = useState<SourceMode>("local")
  const [name, setName] = useState("")
  const [localPath, setLocalPath] = useState("")
  const [githubUrl, setGithubUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const value = mode === "local" ? localPath : githubUrl

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !value.trim()) return
    setLoading(true)
    setError(null)
    try {
      await onSave(
        name.trim(),
        mode === "local" ? { localPath: value.trim() } : { githubUrl: value.trim() }
      )
      setName("")
      setLocalPath("")
      setGithubUrl("")
      onClose()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erreur lors de l'ajout"
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Connecter un dépôt">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex gap-1 border-b">
          {(["local", "github"] as SourceMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 text-sm font-medium border-b-2 transition-colors ${
                mode === m
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {m === "local" ? "Dossier local" : "URL GitHub"}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium">Nom du dépôt</label>
          <Input
            placeholder="ex: backend-api"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        {mode === "local" ? (
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
        ) : (
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">URL GitHub</label>
            <Input
              placeholder="https://github.com/owner/repo"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">
              Dépôt public uniquement — il sera cloné automatiquement (clone superficiel).
            </p>
          </div>
        )}

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
