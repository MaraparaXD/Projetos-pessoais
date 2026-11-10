export const labels: Record<string, string> = {OPEN: 'Aberto', ACKNOWLEDGED: 'Reconhecido', INVESTIGATING: 'Em investigação', RESOLVED: 'Resolvido', CLOSED: 'Encerrado', CRIT: 'Crítico', WARN: 'Atenção', UNKNOWN: 'Desconhecido', OK: 'Normal', RECOVERY: 'Recuperação'}
const dateFormatter = new Intl.DateTimeFormat('pt-BR', {day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'})
export const date = (value: string) => dateFormatter.format(new Date(value))
export function duration(seconds: number | null) {
  if (seconds === null) return 'Sem amostra'
  if (seconds < 60) return `${Math.max(0, Math.round(seconds))} s`
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`
  return `${(seconds / 3600).toFixed(1)} h`
}
export const transitions: Record<string, string[]> = {OPEN: ['ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED'], ACKNOWLEDGED: ['INVESTIGATING', 'RESOLVED'], INVESTIGATING: ['RESOLVED'], RESOLVED: ['OPEN', 'CLOSED'], CLOSED: []}
