import { useEffect, useState, type FormEvent } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Activity, Cable, CircleDot, LayoutDashboard, LogOut, Moon, Server, Settings, Shield, ShieldCheck, Sun, ScrollText } from 'lucide-react'
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { api, send, setToken } from './api'
import { ErrorNotice } from './components'
import type { User } from './types'
import { AuditPage, DashboardPage, EventsPage, HostsPage, IncidentPage, IncidentsPage, IntegrationsPage, SettingsPage } from './pages'

function Login({onLogin}: {onLogin: (user: User) => void}) {
  const [error, setError] = useState<Error | null>(null)
  const [pending, setPending] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null); setPending(true)
    const data = new FormData(event.currentTarget)
    try {
      const result = await send<{access_token: string; user: User}>('/auth/login', {email: data.get('email'), password: data.get('password')})
      setToken(result.access_token); onLogin(result.user)
    } catch (error) {setError(error as Error)} finally {setPending(false)}
  }
  return <main className="login-layout"><section className="login-story"><div className="brand"><Shield size={28}/><span>SENTINEL<span className="brand-noc">NOC</span></span></div><div><h1>O sinal certo.<br/>A próxima ação.</h1><p>Um espaço para transformar alertas de infraestrutura em incidentes que você consegue acompanhar.</p><div className="login-diagram" aria-hidden="true"><span>MONITORAMENTO</span><i/><span>EVENTO</span><i/><span>INCIDENTE</span></div></div><p className="muted">Laboratório independente · Portfólio técnico</p></section><section className="login-form-wrap"><form onSubmit={submit} className="login-form"><ShieldCheck size={30} className="accent"/><h2>Acesse a operação</h2><p>Entre com uma conta autorizada do seu ambiente.</p><label>E-mail<input name="email" type="email" autoComplete="username" placeholder="seu@email.com" required maxLength={254}/></label><label>Senha<input name="password" type="password" autoComplete="current-password" placeholder="Sua senha" required maxLength={128}/></label><ErrorNotice error={error}/><button className="primary" disabled={pending}>{pending ? 'Autenticando…' : 'Entrar no painel'}</button><div className="login-note"><CircleDot size={16}/><span>Ambiente local. Credenciais geradas pelo script de configuração; consulte seu arquivo .env.</span></div></form></section></main>
}

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('sentinel:theme:v1') || 'dark')
  const [logoutError, setLogoutError] = useState<Error | null>(null)
  const client = useQueryClient()
  useEffect(() => {document.documentElement.dataset.theme = theme; localStorage.setItem('sentinel:theme:v1', theme)}, [theme])
  useEffect(() => {
    const expired = () => {setToken(null); setUser(null); client.clear()}
    window.addEventListener('session-expired', expired)
    return () => window.removeEventListener('session-expired', expired)
  }, [client])
  if (!user) return <Login onLogin={setUser}/>
  const links = [{to: '/', title: 'Visão geral', icon: LayoutDashboard}, {to: '/incidentes', title: 'Incidentes', icon: CircleDot}, {to: '/eventos', title: 'Eventos', icon: Activity}, {to: '/hosts', title: 'Hosts e serviços', icon: Server}, ...(user.role === 'Admin' ? [{to: '/integracoes', title: 'Integrações', icon: Cable}, {to: '/auditoria', title: 'Auditoria', icon: ScrollText}] : []), {to: '/configuracoes', title: 'Configurações', icon: Settings}]
  async function logout() {
    try {await api('/auth/logout', {method: 'POST'}); setToken(null); setUser(null); client.clear()}
    catch (error) {setLogoutError(error as Error)}
  }
  return <div className="app-shell"><a className="skip-link" href="#main">Ir para o conteúdo</a><aside className="sidebar"><Link className="brand" to="/" aria-label="SENTINEL NOC início"><Shield size={27}/><span>SENTINEL<span className="brand-noc">NOC</span></span></Link><div className="workspace"><span className="workspace-dot"/><div>Operação local<small>Workspace independente</small></div></div><nav aria-label="Navegação principal">{links.map(({to, title, icon: Icon}) => <NavLink end={to === '/'} to={to} key={to}><Icon size={18}/>{title}</NavLink>)}</nav><div className="sidebar-bottom"><div className="phase-note"><ShieldCheck size={18}/><span>Núcleo do MVP<small>Fases 1 e 2</small></span></div><div className="user-block"><span className="avatar">{user.name.slice(0, 2).toUpperCase()}</span><div>{user.name}<small>{user.role}</small></div><button className="icon-button" onClick={logout} aria-label="Sair da conta"><LogOut size={18}/></button></div></div></aside><div className="main-shell"><header className="topbar"><span><span className="live-dot"/>Atualização automática · 10 s</span><div><span className="lab-label">LABORATÓRIO</span><button className="icon-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}>{theme === 'dark' ? <Sun size={18}/> : <Moon size={18}/>}</button></div></header><main id="main"><ErrorNotice error={logoutError}/><Routes><Route path="/" element={<DashboardPage/>}/><Route path="/incidentes" element={<IncidentsPage/>}/><Route path="/incidentes/:id" element={<IncidentPage user={user}/>}/><Route path="/eventos" element={<EventsPage/>}/><Route path="/hosts" element={<HostsPage/>}/><Route path="/integracoes" element={user.role === 'Admin' ? <IntegrationsPage/> : <Navigate to="/" replace/>}/><Route path="/auditoria" element={user.role === 'Admin' ? <AuditPage/> : <Navigate to="/" replace/>}/><Route path="/configuracoes" element={<SettingsPage user={user}/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes></main><footer className="app-footer"><span>SENTINEL NOC <span className="muted">/</span> v0.1.0</span><span>Dados da API · laboratório sintético identificado por registro</span></footer></div></div>
}
