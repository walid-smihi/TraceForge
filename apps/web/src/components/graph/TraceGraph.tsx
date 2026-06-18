"use client"

import { toPng } from "html-to-image"
import { useCallback, useMemo, useRef, useState } from "react"
import ReactFlow, {
  Background,
  Controls,
  type Edge,
  type Node,
  ReactFlowProvider,
  useReactFlow,
} from "reactflow"
import "reactflow/dist/style.css"

import { Button } from "@/components/ui/button"
import { layoutGraph } from "@/lib/graphLayout"
import type { CodeFileNodeData, GraphData, GraphNode as GraphNodeT, TraceLinkStatus } from "@/lib/types"

import { type FilterState, GraphFilters } from "./GraphFilters"
import { CodeFileNode, RequirementNode } from "./GraphNodes"
import { NodeDetailPanel } from "./NodeDetailPanel"

const nodeTypes = {
  requirement: RequirementNode,
  code_file: CodeFileNode,
}

const EDGE_STYLE: Record<TraceLinkStatus, { stroke: string; dashed: boolean }> = {
  validated: { stroke: "#16a34a", dashed: false },
  suggested: { stroke: "#94a3b8", dashed: true },
  rejected: { stroke: "#ef4444", dashed: true },
  needs_review: { stroke: "#f59e0b", dashed: true },
}

interface Props {
  graph: GraphData
}

function GraphInner({ graph }: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null)
  const { fitView } = useReactFlow()
  const [selected, setSelected] = useState<GraphNodeT | null>(null)
  const [filters, setFilters] = useState<FilterState>({
    showRequirements: true,
    showCodeFiles: true,
    statuses: new Set<TraceLinkStatus>(["validated", "suggested"]),
    hideTests: false,
  })

  const nodesById = useMemo(() => {
    const map = new Map<string, GraphNodeT>()
    for (const n of graph.nodes) map.set(n.id, n)
    return map
  }, [graph.nodes])

  const { rfNodes, rfEdges } = useMemo(() => {
    const visibleNodeIds = new Set<string>()

    for (const n of graph.nodes) {
      if (n.node_type === "requirement" && !filters.showRequirements) continue
      if (n.node_type === "code_file" && !filters.showCodeFiles) continue
      if (n.node_type === "code_file" && filters.hideTests && (n.data as CodeFileNodeData).is_test_file) {
        continue
      }
      visibleNodeIds.add(n.id)
    }

    const visibleEdges = graph.edges.filter(
      (e) =>
        filters.statuses.has(e.status) &&
        visibleNodeIds.has(e.source) &&
        visibleNodeIds.has(e.target)
    )

    // Only show nodes that have at least one visible edge, or show isolated nodes too?
    // Keep isolated nodes visible so unlinked requirements/files are still discoverable.
    const baseNodes: Node[] = graph.nodes
      .filter((n) => visibleNodeIds.has(n.id))
      .map((n) => ({
        id: n.id,
        type: n.node_type,
        position: { x: 0, y: 0 },
        data: n.data,
      }))

    const baseEdges: Edge[] = visibleEdges.map((e) => {
      const style = EDGE_STYLE[e.status]
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        animated: false,
        style: { stroke: style.stroke, strokeDasharray: style.dashed ? "5 5" : undefined },
      }
    })

    return { rfNodes: layoutGraph(baseNodes, baseEdges), rfEdges: baseEdges }
  }, [graph, filters])

  const handleNodeClick = useCallback(
    (_: unknown, node: Node) => {
      const original = nodesById.get(node.id)
      if (original) setSelected(original)
    },
    [nodesById]
  )

  const handleExportPng = useCallback(() => {
    if (!wrapperRef.current) return
    toPng(wrapperRef.current, { backgroundColor: "#ffffff" }).then((dataUrl) => {
      const link = document.createElement("a")
      link.download = "trace-graph.png"
      link.href = dataUrl
      link.click()
    })
  }, [])

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <GraphFilters filters={filters} onChange={setFilters} />
        <div className="flex items-center gap-2 shrink-0">
          <Button size="sm" variant="secondary" onClick={() => fitView({ duration: 300 })}>
            Recentrer
          </Button>
          <Button size="sm" variant="secondary" onClick={handleExportPng}>
            Exporter PNG
          </Button>
        </div>
      </div>

      <div ref={wrapperRef} className="relative border rounded-lg h-[600px] bg-white">
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          nodeTypes={nodeTypes}
          onNodeClick={handleNodeClick}
          onPaneClick={() => setSelected(null)}
          fitView
          minZoom={0.1}
        >
          <Background />
          <Controls />
        </ReactFlow>
        {selected && <NodeDetailPanel node={selected} onClose={() => setSelected(null)} />}
      </div>
    </div>
  )
}

export function TraceGraph({ graph }: Props) {
  return (
    <ReactFlowProvider>
      <GraphInner graph={graph} />
    </ReactFlowProvider>
  )
}
