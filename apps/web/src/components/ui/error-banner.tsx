import { Button } from "@/components/ui/button"

interface Props {
  message: string
  onRetry?: (() => void) | undefined
}

export function ErrorBanner({ message, onRetry }: Props) {
  return (
    <div className="border border-destructive/30 bg-destructive/10 rounded-lg p-4 flex items-center justify-between gap-3">
      <p className="text-sm text-destructive">{message}</p>
      {onRetry && (
        <Button size="sm" variant="secondary" onClick={onRetry}>
          Réessayer
        </Button>
      )}
    </div>
  )
}
