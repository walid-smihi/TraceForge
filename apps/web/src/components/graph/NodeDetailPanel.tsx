import type { CodeFileNodeData, GraphNode, RequirementNodeData } from "@/lib/types"

interface Props {
  node: GraphNode
  onClose: () => void
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-700",
}

export function NodeDetailPanel({ node, onClose }: Props) {
  const isReq = node.node_type === "requirement"

  return (
    <div className="absolute top-3 right-3 w-72 border rounded-lg bg-background shadow-lg p-4 z-10">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs uppercase text-muted-foreground font-medium">
          {isReq ? "Exigence" : "Fichier de code"}
        </span>
        <button className="text-muted-foreground hover:text-foreground text-sm" onClick={onClose}>
          ✕
        </button>
      </div>

      {isReq ? (
        <ReqDetail data={node.data as RequirementNodeData} />
      ) : (
        <FileDetail data={node.data as CodeFileNodeData} />
      )}
    </div>
  )
}

function ReqDetail({ data }: { data: RequirementNodeData }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-muted-foreground">{data.code}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded ${PRIORITY_COLORS[data.priority] ?? ""}`}>
          {data.priority}
        </span>
      </div>
      <p className="text-sm font-semibold">{data.title}</p>
      {data.description && <p className="text-xs text-muted-foreground">{data.description}</p>}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="px-1.5 py-0.5 rounded bg-muted">{data.req_type}</span>
        <span className="px-1.5 py-0.5 rounded bg-muted">{data.status}</span>
      </div>
      {data.is_ambiguous && (
        <p className="text-xs text-orange-600">⚠ {data.ambiguity_reason}</p>
      )}
      {!data.is_linked && (
        <p className="text-xs text-red-600">Aucun lien validé — non couverte</p>
      )}
    </div>
  )
}

function FileDetail({ data }: { data: CodeFileNodeData }) {
  return (
    <div className="flex flex-col gap-2">
      <code className="text-xs font-mono break-all">{data.path}</code>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {data.language && <span className="px-1.5 py-0.5 rounded bg-muted">{data.language}</span>}
        {data.role_detected && <span className="px-1.5 py-0.5 rounded bg-muted">{data.role_detected}</span>}
        {data.is_test_file && <span className="px-1.5 py-0.5 rounded bg-muted">test</span>}
      </div>
      {data.summary && <p className="text-xs text-muted-foreground">{data.summary}</p>}
      {!data.is_linked && (
        <p className="text-xs text-orange-600">Non lié à aucune exigence</p>
      )}
    </div>
  )
}
