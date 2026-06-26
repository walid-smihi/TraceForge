"use client"

import type { CodeFile, Repository } from "@/lib/types"

interface Props {
  repository: Repository
  files: CodeFile[]
}

const LANG_COLOR: Record<string, string> = {
  TypeScript: "bg-blue-100 text-blue-700",
  JavaScript: "bg-yellow-100 text-yellow-700",
  Python: "bg-green-100 text-green-700",
  Go: "bg-cyan-100 text-cyan-700",
  Rust: "bg-orange-100 text-orange-700",
  Java: "bg-red-100 text-red-700",
  "C#": "bg-purple-100 text-purple-700",
  SQL: "bg-slate-100 text-slate-700",
  Shell: "bg-gray-100 text-gray-700",
}

const ROLE_LABEL: Record<string, string> = {
  component: "Composant",
  service: "Service",
  util: "Utilitaire",
  config: "Config",
  test: "Test",
  model: "Modèle",
  router: "Router",
  worker: "Worker",
  other: "Autre",
}

export function FilesList({ repository, files }: Props) {
  if (files.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground text-sm">
        Aucun fichier trouvé dans ce dépôt.
      </div>
    )
  }

  const byLanguage = files.reduce<Record<string, number>>((acc, f) => {
    const lang = f.language ?? "Unknown"
    acc[lang] = (acc[lang] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="flex flex-col gap-4">
      {/* Stats */}
      <div className="flex flex-wrap gap-3">
        <span className="text-sm text-muted-foreground">
          {repository.file_count} fichier{repository.file_count !== 1 ? "s" : ""}
          {repository.test_count > 0 && (
            <span className="ml-2 text-green-600">· {repository.test_count} tests</span>
          )}
        </span>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(byLanguage)
            .sort((a, b) => b[1] - a[1])
            .map(([lang, count]) => (
              <span
                key={lang}
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${LANG_COLOR[lang] ?? "bg-muted text-muted-foreground"}`}
              >
                {lang} {count}
              </span>
            ))}
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead className="bg-muted/50 border-b">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium text-muted-foreground">Fichier</th>
              <th className="text-left px-3 py-2.5 font-medium text-muted-foreground w-28">Langage</th>
              <th className="text-left px-3 py-2.5 font-medium text-muted-foreground w-24">Rôle</th>
              <th className="text-right px-4 py-2.5 font-medium text-muted-foreground w-16">Lignes</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {files.map((file) => (
              <tr key={file.id} className="hover:bg-muted/30 transition-colors group">
                <td className="px-4 py-3">
                  <div className="flex items-start gap-2">
                    {file.is_test_file && (
                      <span className="mt-0.5 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded shrink-0">
                        test
                      </span>
                    )}
                    <div>
                      <p className="font-mono text-xs text-foreground leading-snug">{file.path}</p>
                      {file.summary && (
                        <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{file.summary}</p>
                      )}
                      {file.entities && file.entities.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {file.entities.slice(0, 5).map((e) => (
                            <span key={e} className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">
                              {e}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3">
                  {file.language && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${LANG_COLOR[file.language] ?? "bg-muted text-muted-foreground"}`}
                    >
                      {file.language}
                    </span>
                  )}
                </td>
                <td className="px-3 py-3 text-xs text-muted-foreground">
                  {file.role_detected ? ROLE_LABEL[file.role_detected] ?? file.role_detected : "—"}
                </td>
                <td className="px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                  {file.line_count ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
