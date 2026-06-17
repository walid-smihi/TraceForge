"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { DocumentList } from "@/components/documents/DocumentList"
import { DocumentUpload } from "@/components/documents/DocumentUpload"
import { JobProgress } from "@/components/jobs/JobProgress"
import { RequirementForm } from "@/components/requirements/RequirementForm"
import { RequirementsTable } from "@/components/requirements/RequirementsTable"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useDocuments } from "@/lib/hooks/useDocuments"
import { useRequirements } from "@/lib/hooks/useRequirements"
import type { AnalysisJob, Document, Project, Requirement } from "@/lib/types"

interface Props {
  params: { id: string }
}

type Tab = "documents" | "requirements"

export default function ProjectPage({ params }: Props) {
  const { id } = params
  const [project, setProject] = useState<Project | null>(null)
  const [projectError, setProjectError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>("documents")
  const [docJobMap, setDocJobMap] = useState<Record<string, string>>({})
  const [extractJobId, setExtractJobId] = useState<string | null>(null)
  const [showReqForm, setShowReqForm] = useState(false)
  const [editingReq, setEditingReq] = useState<Requirement | null>(null)

  const { documents, loading: docsLoading, uploadDocument, deleteDocument, refetch: refetchDocs } = useDocuments(id)
  const { requirements, loading: reqsLoading, extractRequirements, createRequirement, updateRequirement, deleteRequirement, refetch: refetchReqs } = useRequirements(id)

  useEffect(() => {
    api.get<Project>(`/api/v1/projects/${id}`)
      .then(setProject)
      .catch(() => setProjectError("Projet introuvable"))
  }, [id])

  const handleUpload = async (file: File) => {
    const job = await uploadDocument(file)
    const documentId = job.input_data?.document_id
    if (documentId) setDocJobMap((prev) => ({ ...prev, [documentId]: job.id }))
    return job
  }

  const processedDocs = documents.filter((d: Document) => d.status === "processed")

  const handleExtract = async (doc: Document) => {
    const job = await extractRequirements(doc.id)
    setExtractJobId(job.id)
    setActiveTab("requirements")
  }

  const handleSaveReq = async (data: { title: string; description?: string; req_type: string; priority: string }) => {
    if (editingReq) {
      await updateRequirement(editingReq.id, data)
    } else {
      await createRequirement(data)
    }
    setEditingReq(null)
  }

  if (projectError) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8 text-center">
        <p className="text-destructive">{projectError}</p>
        <Link href="/" className="text-sm text-muted-foreground underline mt-2 inline-block">← Projets</Link>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link href="/" className="text-sm text-muted-foreground hover:underline">← Projets</Link>
        <div className="mt-3 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{project?.name ?? "…"}</h1>
            {project?.domain && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full mt-1 inline-block">{project.domain}</span>
            )}
            {project?.description && (
              <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>{documents.length} doc{documents.length !== 1 ? "s" : ""}</span>
            <span>{requirements.length} req{requirements.length !== 1 ? "s" : ""}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b mb-6">
        {(["documents", "requirements"] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors capitalize ${
              activeTab === tab
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "documents" ? `Documents (${documents.length})` : `Requirements (${requirements.length})`}
          </button>
        ))}
      </div>

      {/* Documents tab */}
      {activeTab === "documents" && (
        <div className="flex flex-col gap-4">
          <DocumentUpload onUpload={handleUpload} />
          {docsLoading ? (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin border-2 border-primary border-t-transparent rounded-full" />
            </div>
          ) : (
            <>
              <DocumentList
                documents={documents}
                docJobMap={docJobMap}
                onDelete={deleteDocument}
                onJobComplete={refetchDocs}
              />
              {processedDocs.length > 0 && (
                <div className="border rounded-lg p-4 bg-muted/20">
                  <p className="text-sm font-medium mb-3">Extraire les exigences</p>
                  <div className="flex flex-wrap gap-2">
                    {processedDocs.map((doc) => (
                      <Button key={doc.id} variant="secondary" size="sm" onClick={() => handleExtract(doc)}>
                        {doc.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Requirements tab */}
      {activeTab === "requirements" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {requirements.length} exigence{requirements.length !== 1 ? "s" : ""}
              {requirements.filter((r: Requirement) => r.is_ambiguous).length > 0 && (
                <span className="ml-2 text-orange-500">
                  ⚠ {requirements.filter((r: Requirement) => r.is_ambiguous).length} ambiguë{requirements.filter((r: Requirement) => r.is_ambiguous).length > 1 ? "s" : ""}
                </span>
              )}
            </p>
            <Button size="sm" onClick={() => { setEditingReq(null); setShowReqForm(true) }}>
              + Nouvelle exigence
            </Button>
          </div>

          {extractJobId && (
            <div className="border rounded-lg p-4 bg-blue-50">
              <p className="text-sm font-medium mb-2">Extraction en cours…</p>
              <JobProgress
                jobId={extractJobId}
                onComplete={() => { setExtractJobId(null); refetchReqs() }}
              />
            </div>
          )}

          {reqsLoading ? (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin border-2 border-primary border-t-transparent rounded-full" />
            </div>
          ) : (
            <RequirementsTable
              requirements={requirements}
              onEdit={(req) => { setEditingReq(req); setShowReqForm(true) }}
              onDelete={deleteRequirement}
            />
          )}
        </div>
      )}

      <RequirementForm
        open={showReqForm}
        onClose={() => { setShowReqForm(false); setEditingReq(null) }}
        onSave={handleSaveReq}
        initial={editingReq}
      />
    </div>
  )
}
