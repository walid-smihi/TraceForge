"use client"

import { use, useEffect, useState } from "react"
import Link from "next/link"
import { DocumentList } from "@/components/documents/DocumentList"
import { DocumentUpload } from "@/components/documents/DocumentUpload"
import { api } from "@/lib/api"
import { useDocuments } from "@/lib/hooks/useDocuments"
import type { Project } from "@/lib/types"

interface Props {
  params: Promise<{ id: string }>
}

export default function ProjectPage({ params }: Props) {
  const { id } = use(params)
  const [project, setProject] = useState<Project | null>(null)
  const [projectError, setProjectError] = useState<string | null>(null)
  // Map documentId → jobId for progress tracking
  const [docJobMap, setDocJobMap] = useState<Record<string, string>>({})

  const { documents, loading, uploadDocument, deleteDocument, refetch } = useDocuments(id)

  useEffect(() => {
    api
      .get<Project>(`/api/v1/projects/${id}`)
      .then(setProject)
      .catch(() => setProjectError("Project not found"))
  }, [id])

  const handleUpload = async (file: File) => {
    const job = await uploadDocument(file)
    const documentId = job.input_data?.document_id
    if (documentId) {
      setDocJobMap((prev) => ({ ...prev, [documentId]: job.id }))
    }
    return job
  }

  const handleJobComplete = () => {
    refetch()
  }

  if (projectError) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8 text-center">
        <p className="text-destructive">{projectError}</p>
        <Link href="/" className="text-sm text-muted-foreground underline mt-2 inline-block">
          ← Back to projects
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <Link href="/" className="text-sm text-muted-foreground hover:underline">
          ← Projects
        </Link>
        <div className="mt-3">
          <h1 className="text-2xl font-bold">{project?.name ?? "…"}</h1>
          {project?.domain && (
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full mt-1 inline-block">
              {project.domain}
            </span>
          )}
          {project?.description && (
            <p className="text-sm text-muted-foreground mt-2">{project.description}</p>
          )}
        </div>
      </div>

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">Documents</h2>
        <DocumentUpload onUpload={handleUpload} />
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="h-6 w-6 animate-spin border-2 border-primary border-t-transparent rounded-full" />
          </div>
        ) : (
          <DocumentList
            documents={documents}
            docJobMap={docJobMap}
            onDelete={deleteDocument}
            onJobComplete={handleJobComplete}
          />
        )}
      </section>
    </div>
  )
}
