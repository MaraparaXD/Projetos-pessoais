import type { ReactNode } from 'react'
import { ArrowLeft, ArrowRight, RefreshCw, Radio } from 'lucide-react'
import { Link } from 'react-router-dom'
import { date, labels } from './format'
import type { Incident } from './types'

export function Badge({value}: {value: string}) { return <span className={`badge ${value.toLowerCase()}`}>{labels[value] || value}</span> }
export function ErrorNotice({error}: {error: Error | null}) {return error ? <div className="error" role="alert">{error.message}</div> : null}
export function Loading() {return <div className="empty" role="status"><RefreshCw size={20} className="spin" /> Carregando dados da API…</div>}
export function Empty({children}: {children?: ReactNode}) {return <div className="empty"><Radio size={26} /><strong>Nenhum registro por aqui</strong><span>{children || 'Os dados recebidos aparecerão nesta área.'}</span></div>}
export function PageHeading({title, description, children}: {title: string; description: string; children?: ReactNode}) {return <header className="page-heading"><div><h1>{title}</h1><p>{description}</p></div>{children}</header>}
export function Pagination({total, offset, onChange, limit = 25}: {total: number; offset: number; limit?: number; onChange: (offset: number) => void}) {
  return <div className="pagination"><span>{total === 0 ? '0 registros' : `${offset + 1}–${Math.min(offset + limit, total)} de ${total} registros`}</span><div><button className="icon-button" aria-label="Página anterior" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset-limit))}><ArrowLeft size={16}/></button><button className="icon-button" aria-label="Próxima página" disabled={offset+limit >= total} onClick={() => onChange(offset+limit)}><ArrowRight size={16}/></button></div></div>
}
export function IncidentTable({items}: {items: Incident[]}) {
  if (!items.length) return <Empty>Execute o simulador para receber alertas de laboratório.</Empty>
  return <div className="table-scroll"><table><thead><tr><th>Severidade</th><th>Host / serviço</th><th>Estado</th><th>Atualizado</th><th><span className="sr-only">Detalhes</span></th></tr></thead><tbody>{items.map(i => <tr key={i.id}><td><Badge value={i.severity}/></td><td><Link className="resource-link" to={`/incidentes/${i.id}`}>{i.host_name}</Link><span className="subtext">{i.service_name || 'Disponibilidade do host'}{i.flapping ? ' · Flapping' : ''}</span></td><td><Badge value={i.status}/></td><td className="mono nowrap">{date(i.updated_at)}</td><td><Link className="icon-button" aria-label={`Abrir incidente de ${i.host_name} ${i.service_name || ''}`} to={`/incidentes/${i.id}`}><ArrowRight size={17}/></Link></td></tr>)}</tbody></table></div>
}
