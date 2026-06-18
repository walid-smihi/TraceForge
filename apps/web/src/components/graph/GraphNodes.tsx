import { Handle, Position } from "reactflow"

import type { CodeFileNodeData, RequirementNodeData } from "@/lib/types"

const REQ_TYPE_COLORS: Record<string, string> = {
  functional: "border-blue-400 bg-blue-50",
  security: "border-red-400 bg-red-50",
  performance: "border-orange-400 bg-orange-50",
  availability: "border-purple-400 bg-purple-50",
  compliance: "border-teal-400 bg-teal-50",
  interface: "border-pink-400 bg-pink-50",
}

export function RequirementNode({ data }: { data: RequirementNodeData }) {
  const colors = REQ_TYPE_COLORS[data.req_type] ?? "border-gray-400 bg-gray-50"
  return (
    <div
      className={`rounded-lg border-2 px-3 py-2 shadow-sm w-[220px] ${colors} ${
        !data.is_linked ? "opacity-60" : ""
      }`}
    >
      <Handle type="source" position={Position.Right} className="!bg-foreground" />
      <Handle type="target" position={Position.Left} className="!bg-foreground" />
      <div className="flex items-center justify-between gap-1">
        <span className="text-[10px] font-mono text-muted-foreground">{data.code}</span>
        {data.is_ambiguous && <span className="text-[10px] text-orange-600">⚠</span>}
      </div>
      <p className="text-xs font-medium leading-tight line-clamp-2">{data.title}</p>
    </div>
  )
}

const LANG_COLORS: Record<string, string> = {
  Python: "border-blue-300 bg-white",
  TypeScript: "border-indigo-300 bg-white",
  JavaScript: "border-yellow-300 bg-white",
}

export function CodeFileNode({ data }: { data: CodeFileNodeData }) {
  const colors = LANG_COLORS[data.language ?? ""] ?? "border-gray-300 bg-white"
  return (
    <div
      className={`rounded-lg border-2 px-3 py-2 shadow-sm w-[220px] ${colors} ${
        data.is_test_file ? "border-dashed" : ""
      } ${!data.is_linked ? "opacity-60" : ""}`}
    >
      <Handle type="source" position={Position.Right} className="!bg-foreground" />
      <Handle type="target" position={Position.Left} className="!bg-foreground" />
      <div className="flex items-center justify-between gap-1">
        <span className="text-[10px] text-muted-foreground">{data.language ?? "?"}</span>
        {data.is_test_file && <span className="text-[10px] text-muted-foreground">test</span>}
      </div>
      <p className="text-xs font-medium leading-tight line-clamp-1 font-mono">{data.path.split("/").pop()}</p>
    </div>
  )
}
