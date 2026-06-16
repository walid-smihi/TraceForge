import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "TraceForge",
  description: "Requirements → Code → Tests traceability tool",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen flex-col">
          <header className="border-b bg-card px-6 py-3 flex items-center gap-3">
            <span className="text-lg font-bold tracking-tight">TraceForge</span>
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
              Sprint 1
            </span>
          </header>
          <main className="flex-1 bg-background">{children}</main>
        </div>
      </body>
    </html>
  )
}
