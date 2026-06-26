"use client"

import { useState } from "react"
import { CreateProjectDialog } from "@/components/projects/CreateProjectDialog"
import { ProjectCard } from "@/components/projects/ProjectCard"
import { Button } from "@/components/ui/button"
import { API_URL } from "@/lib/api"
import { useProjects } from "@/lib/hooks/useProjects"

export default function HomePage() {
  const { projects, loading, error, createProject, deleteProject } = useProjects()
  const [showCreate, setShowCreate] = useState(false)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-destructive text-sm">{error}</p>
        <p className="text-muted-foreground text-xs">Make sure the backend is reachable at {API_URL}</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {projects.length} project{projects.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ New Project</Button>
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-4 border rounded-lg bg-muted/30">
          <p className="text-muted-foreground">No projects yet</p>
          <Button variant="secondary" onClick={() => setShowCreate(true)}>
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={deleteProject}
            />
          ))}
        </div>
      )}

      <CreateProjectDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={createProject}
      />
    </div>
  )
}
