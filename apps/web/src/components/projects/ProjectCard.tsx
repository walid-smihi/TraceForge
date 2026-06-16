"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import type { Project } from "@/lib/types"

interface Props {
  project: Project
  onDelete: (id: string) => void
}

export function ProjectCard({ project, onDelete }: Props) {
  const created = new Date(project.created_at).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })

  return (
    <div className="rounded-lg border bg-card p-5 flex flex-col gap-3 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1 min-w-0">
          <Link
            href={`/projects/${project.id}`}
            className="font-semibold text-foreground hover:underline truncate"
          >
            {project.name}
          </Link>
          {project.domain && (
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full w-fit">
              {project.domain}
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground hover:text-destructive shrink-0"
          onClick={() => onDelete(project.id)}
        >
          ✕
        </Button>
      </div>
      {project.description && (
        <p className="text-sm text-muted-foreground line-clamp-2">{project.description}</p>
      )}
      <p className="text-xs text-muted-foreground mt-auto">{created}</p>
    </div>
  )
}
