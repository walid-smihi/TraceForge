// ── Projects ─────────────────────────────────────────────────────────────────

export interface Project {
  id: string
  name: string
  description: string | null
  domain: string | null
  created_at: string
  updated_at: string
}

// ── Documents ─────────────────────────────────────────────────────────────────

export type DocumentStatus = "uploaded" | "processing" | "processed" | "failed"

export interface Document {
  id: string
  project_id: string
  name: string
  file_type: string
  file_size_bytes: number | null
  status: DocumentStatus
  created_at: string
}

// ── Requirements ──────────────────────────────────────────────────────────────

export type RequirementType =
  | "functional"
  | "security"
  | "performance"
  | "availability"
  | "compliance"
  | "interface"

export type RequirementPriority = "critical" | "high" | "medium" | "low"
export type RequirementStatus = "draft" | "active" | "modified" | "deprecated"

export interface Requirement {
  id: string
  project_id: string
  code: string
  title: string
  description: string | null
  req_type: RequirementType
  priority: RequirementPriority
  status: RequirementStatus
  is_ambiguous: boolean
  ambiguity_reason: string | null
  version: number
  created_at: string
  updated_at: string
}

// ── Repositories ──────────────────────────────────────────────────────────────

export type RepositoryStatus = "pending" | "scanning" | "scanned" | "failed"

export interface Repository {
  id: string
  project_id: string
  name: string
  source_type: string
  local_path: string | null
  status: RepositoryStatus
  file_count: number
  test_count: number
  scanned_at: string | null
  created_at: string
}

export interface CodeFile {
  id: string
  repository_id: string
  project_id: string
  path: string
  language: string | null
  summary: string | null
  role_detected: string | null
  entities: string[] | null
  is_test_file: boolean
  line_count: number | null
  created_at: string
}

// ── Trace Links ───────────────────────────────────────────────────────────────

export type TraceLinkStatus = "suggested" | "validated" | "rejected" | "needs_review"

export interface TraceLink {
  id: string
  project_id: string
  source_type: string
  source_id: string
  target_type: string
  target_id: string
  link_type: string
  confidence_score: number | null
  status: TraceLinkStatus
  justification: string | null
  is_manual: boolean
  created_at: string
  requirement_code: string | null
  requirement_title: string | null
  file_path: string | null
  file_language: string | null
  file_summary: string | null
}

// ── Graph ─────────────────────────────────────────────────────────────────────

export type GraphNodeType = "requirement" | "code_file"

export interface RequirementNodeData {
  id: string
  code: string
  title: string
  description: string | null
  req_type: RequirementType
  priority: RequirementPriority
  status: RequirementStatus
  is_ambiguous: boolean
  ambiguity_reason: string | null
  is_linked: boolean
}

export interface CodeFileNodeData {
  id: string
  path: string
  language: string | null
  summary: string | null
  role_detected: string | null
  is_test_file: boolean
  is_linked: boolean
}

export interface GraphNode {
  id: string
  node_type: GraphNodeType
  label: string
  sublabel: string | null
  data: RequirementNodeData | CodeFileNodeData
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  status: TraceLinkStatus
  confidence_score: number | null
  is_manual: boolean
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface ProjectMetrics {
  project_id: string
  requirements_total: number
  requirements_linked: number
  requirements_unlinked: number
  requirements_ambiguous: number
  coverage_percent: number
  code_files_total: number
  code_files_linked: number
  test_files_total: number
  links_total: number
  links_validated: number
  links_suggested: number
  links_rejected: number
  conflicts_open: number
}

// ── Search ────────────────────────────────────────────────────────────────────

export interface SearchResult {
  type: "requirement" | "code_file"
  id: string
  code: string
  title: string
  summary: string | null
  score: number
}

// ── Jobs ──────────────────────────────────────────────────────────────────────

export type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled"
export type JobType =
  | "extract_document"
  | "extract_requirements"
  | "scan_repository"
  | "suggest_links"
  | "generate_impact"

export interface AnalysisJob {
  id: string
  project_id: string
  job_type: JobType
  status: JobStatus
  progress: number
  input_data: Record<string, string> | null
  result_data: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

// ── Conflicts ─────────────────────────────────────────────────────────────────

export type ConflictSeverity = "critical" | "warning" | "info"

export interface DetectedConflict {
  id: string
  project_id: string
  rule_id: string | null
  severity: ConflictSeverity
  title: string
  description: string | null
  requirement_ids: string[] | null
  status: string
  created_at: string
  resolved_at: string | null
}

// ── Impact analysis ─────────────────────────────────────────────────────────────

export interface ImpactFile {
  path: string
  language: string | null
  summary?: string | null
}

export interface ImpactIndirectRequirement {
  code: string
  title: string
}

export interface ImpactConflict {
  rule_id: string | null
  title: string
  description: string | null
}

export interface ImpactReport {
  requirement: {
    id: string
    code: string
    title: string
    description: string | null
  }
  modification_description: string
  summary: string | null
  direct_files: ImpactFile[]
  direct_tests: ImpactFile[]
  indirect_requirements: ImpactIndirectRequirement[]
  conflicts: ImpactConflict[]
}
