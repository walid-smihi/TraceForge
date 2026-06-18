"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { DocumentList } from "@/components/documents/DocumentList"
import { DocumentUpload } from "@/components/documents/DocumentUpload"
import { JobProgress } from "@/components/jobs/JobProgress"
import { FilesList } from "@/components/repositories/FilesList"
import { RepositoryForm } from "@/components/repositories/RepositoryForm"
import { RequirementForm } from "@/components/requirements/RequirementForm"
import { RequirementsTable } from "@/components/requirements/RequirementsTable"
import { TraceLinksView } from "@/components/trace_links/TraceLinksView"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useDocuments } from "@/lib/hooks/useDocuments"
import { useRepositories } from "@/lib/hooks/useRepositories"
import { useRequirements } from "@/lib/hooks/useRequirements"
import { useTraceLinks } from "@/lib/hooks/useTraceLinks"
import type { AnalysisJob, CodeFile, Document, Project, Repository, Requirement } from "@/lib/types"

interface Props {
  params: { id: string }
}

type Tab = "documents" | "requirements" | "code" | "liens"

export default function ProjectPage({ params }: Props) {
  const { id } = params
  const [project, setProject] = useState<Project | null>(null)
  const [projectError, setProjectError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>("documents")
  const [docJobMap, setDocJobMap] = useState<Record<string, string>>({})
  const [extractJobId, setExtractJobId] = useState<string | null>(null)
  const [showReqForm, setShowReqForm] = useState(false)
  const [editingReq, setEditingReq] = useState<Requirement | null>(null)

  // Code tab state
  const [showRepoForm, setShowRepoForm] = useState(false)
  const [scanJobId, setScanJobId] = useState<string | null>(null)
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null)
  const [repoFiles, setRepoFiles] = useState<CodeFile[]>([])
  const [filesLoading, setFilesLoading] = useState(false)

  // Liens tab state
  const [linkJobId, setLinkJobId] = useState<string | null>(null)

  const { documents, loading: docsLoading, uploadDocument, deleteDocument, refetch: refetchDocs } = useDocuments(id)
  const { requirements, loading: reqsLoading, extractRequirements, createRequirement, updateRequirement, deleteRequirement, refetch: refetchReqs } = useRequirements(id)
  const { repositories, loading: reposLoading, addRepository, deleteRepository, getFiles, refetch: refetchRepos } = useRepositories(id)
  const { links, loading: linksLoading, generateLinks, updateLink, deleteLink, refetch: refetchLinks } = useTraceLinks(id)

  useEffect(() => {
    api.get<Project>(`/api/v1/projects/${id}`)
      .then(setProject)
      .catch(() => setProjectError("Projet introuvable"))

    // Restore active jobs on page load
    api.get<AnalysisJob[]>(`/api/v1/projects/${id}/jobs`).then((jobs) => {
      const activeExtract = jobs.find(
        (j) => j.job_type === "extract_requirements" &&
          (j.status === "pending" || j.status === "running")
      )
      if (activeExtract) setExtractJobId(activeExtract.id)

      const activeScan = jobs.find(
        (j) => j.job_type === "scan_repository" &&
          (j.status === "pending" || j.status === "running")
      )
      if (activeScan) setScanJobId(activeScan.id)

      const activeLinks = jobs.find(
        (j) => j.job_type === "suggest_links" &&
          (j.status === "pending" || j.status === "running")
      )
      if (activeLinks) setLinkJobId(activeLinks.id)
    }).catch(() => {})
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

  const handleSaveReq = async (data: { title: string; description?: string | undefined; req_type: string; priority: string }) => {
    if (editingReq) {
      await updateRequirement(editingReq.id, data)
    } else {
      await createRequirement(data)
    }
    setEditingReq(null)
  }

  const handleAddRepo = async (name: string, localPath: string) => {
    const job = await addRepository(name, localPath)
    setScanJobId(job.id)
  }

  const handleScanComplete = async () => {
    setScanJobId(null)
    await refetchRepos()
  }

  const handleSelectRepo = async (repo: Repository) => {
    setSelectedRepo(repo)
    setFilesLoading(true)
    try {
      const files = await getFiles(repo.id)
      setRepoFiles(files)
    } finally {
      setFilesLoading(false)
    }
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
            <span>{repositories.reduce((s, r) => s + r.file_count, 0)} fichiers</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b mb-6">
        {(["documents", "requirements", "code", "liens"] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "documents"
              ? `Documents (${documents.length})`
              : tab === "requirements"
              ? `Requirements (${requirements.length})`
              : tab === "code"
              ? `Code (${repositories.length})`
              : `Liens (${links.length})`}
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
              <p className="text-sm font-medium mb-2">Extraction des exigences</p>
              <JobProgress
                jobId={extractJobId}
                onComplete={() => { setExtractJobId(null); refetchReqs() }}
                onCancel={() => setExtractJobId(null)}
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

      {/* Code tab */}
      {activeTab === "code" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {repositories.length} dépôt{repositories.length !== 1 ? "s" : ""} connecté{repositories.length !== 1 ? "s" : ""}
            </p>
            <Button size="sm" onClick={() => setShowRepoForm(true)}>
              + Connecter un dépôt
            </Button>
          </div>

          {scanJobId && (
            <div className="border rounded-lg p-4 bg-blue-50">
              <p className="text-sm font-medium mb-2">Scan du dépôt en cours…</p>
              <JobProgress
                jobId={scanJobId}
                onComplete={handleScanComplete}
                onCancel={() => setScanJobId(null)}
              />
            </div>
          )}

          {reposLoading ? (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin border-2 border-primary border-t-transparent rounded-full" />
            </div>
          ) : repositories.length === 0 ? (
            <div className="text-center py-12 border rounded-lg border-dashed">
              <p className="text-muted-foreground text-sm">Aucun dépôt connecté.</p>
              <p className="text-muted-foreground text-xs mt-1">Ajoutez un dépôt local pour scanner votre code.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {repositories.map((repo) => (
                <div key={repo.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{repo.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        repo.status === "scanned" ? "bg-green-100 text-green-700" :
                        repo.status === "failed" ? "bg-red-100 text-red-700" :
                        "bg-muted text-muted-foreground"
                      }`}>
                        {repo.status === "scanned" ? "scanné" : repo.status === "failed" ? "erreur" : "en attente"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {repo.status === "scanned" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSelectRepo(repo)}
                        >
                          Voir les fichiers
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => deleteRepository(repo.id)}
                      >
                        Supprimer
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground font-mono">{repo.local_path}</p>
                  {repo.status === "scanned" && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {repo.file_count} fichiers · {repo.test_count} tests
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {selectedRepo && (
            <div className="mt-2">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">{selectedRepo.name} — fichiers</h3>
                <button
                  className="text-xs text-muted-foreground hover:underline"
                  onClick={() => { setSelectedRepo(null); setRepoFiles([]) }}
                >
                  Fermer
                </button>
              </div>
              {filesLoading ? (
                <div className="flex justify-center py-8">
                  <div className="h-6 w-6 animate-spin border-2 border-primary border-t-transparent rounded-full" />
                </div>
              ) : (
                <FilesList repository={selectedRepo} files={repoFiles} />
              )}
            </div>
          )}
        </div>
      )}

      {/* Liens tab */}
      {activeTab === "liens" && (
        <TraceLinksView
          projectId={id}
          links={links}
          loading={linksLoading}
          linkJobId={linkJobId}
          onGenerate={generateLinks}
          onJobStart={(jobId) => setLinkJobId(jobId)}
          onJobComplete={() => { setLinkJobId(null); refetchLinks() }}
          onAccept={(linkId) => updateLink(linkId, "validated")}
          onReject={(linkId) => updateLink(linkId, "rejected")}
          onDelete={(linkId) => deleteLink(linkId)}
        />
      )}

      <RequirementForm
        open={showReqForm}
        onClose={() => { setShowReqForm(false); setEditingReq(null) }}
        onSave={handleSaveReq}
        initial={editingReq}
      />

      <RepositoryForm
        open={showRepoForm}
        onClose={() => setShowRepoForm(false)}
        onSave={handleAddRepo}
      />
    </div>
  )
}
