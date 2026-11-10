import { expect, test, type Page } from '@playwright/test'
import { createHmac } from 'node:crypto'
import { mkdirSync } from 'node:fs'

const email = 'e2e@test.local', password = 'e2e-only-strong-password'
const secret = 'e2e-only-synthetic-webhook-secret-32chars'

async function login(page: Page, account = email, pass = password) {
  await page.goto('/')
  await page.getByLabel('E-mail', {exact:true}).fill(account)
  await page.getByLabel('Senha', {exact:true}).fill(pass)
  await page.getByRole('button', {name:'Entrar no painel'}).click()
  await expect(page.getByRole('heading', {name:'Visão geral'})).toBeVisible()
}

test('login, simulator contract, replay, triage, comments, audit and themes', async ({page, request}) => {
  const browserErrors: string[] = []; page.on('pageerror', e => browserErrors.push(e.message))
  const auth = await request.post('/api/auth/login', {data:{email,password}})
  expect(auth.ok()).toBeTruthy()
  const headers = {Authorization:`Bearer ${(await auth.json()).access_token}`}
  const integrations = await (await request.get('/api/integrations', {headers})).json()
  const payload = {external_id:'browser-01',host:'lab-browser-01',service:'HTTP health',event_type:'SERVICE',state:'CRIT',output:'HTTP 503 — cenário sintético E2E',observed_at:new Date().toISOString()}
  const body = JSON.stringify(payload), timestamp = String(Math.floor(Date.now()/1000))
  const signed = {'Content-Type':'application/json','X-Sentinel-Timestamp':timestamp,'X-Sentinel-Signature':`sha256=${createHmac('sha256',secret).update(`${timestamp}.${body}`).digest('hex')}`}
  const url = `/api/webhooks/checkmk/${integrations[0].id}`
  const event = await request.post(url, {data:body,headers:signed}); expect(event.status()).toBe(201)
  expect((await request.post(url, {data:body,headers:signed})).status()).toBe(200)
  await login(page)
  await expect(page.getByRole('link', {name:'lab-browser-01',exact:true})).toBeVisible()
  mkdirSync('../output/playwright', {recursive:true})
  await page.screenshot({path:'../output/playwright/dashboard-desktop.png',fullPage:true})
  await page.getByRole('link', {name:'lab-browser-01',exact:true}).click()
  await page.getByRole('button', {name:'Reconhecer',exact:true}).click()
  await expect(page.getByText('Reconhecido',{exact:true})).toBeVisible()
  await page.getByLabel('Adicionar comentário').fill('Verificar diagnóstico HTTP no laboratório.')
  await page.getByRole('button', {name:'Adicionar comentário'}).click()
  await expect(page.getByText('Verificar diagnóstico HTTP no laboratório.',{exact:true})).toBeVisible()
  await page.getByLabel('Responsável pelo incidente').selectOption({label:'Administrador'})
  await expect(page.getByLabel('Responsável pelo incidente')).not.toHaveValue('')
  await page.getByRole('button', {name:'Resolver',exact:true}).click()
  await expect(page.getByText('Resolvido',{exact:true})).toBeVisible()
  await page.getByRole('link', {name:'Auditoria',exact:true}).click()
  await expect(page.getByText('incident.status_changed',{exact:true}).first()).toBeVisible()
  await page.getByRole('button', {name:'Ativar tema claro'}).click()
  await expect(page.locator('html')).toHaveAttribute('data-theme','light')
  await page.getByRole('button', {name:'Ativar tema escuro'}).click()
  await page.getByRole('link', {name:'Visão geral',exact:true}).click()
  await page.setViewportSize({width:390,height:844})
  await page.screenshot({path:'../output/playwright/dashboard-mobile.png',fullPage:true})
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  expect(browserErrors).toEqual([])
  await page.getByRole('button',{name:'Sair da conta'}).click()
  await expect(page.getByRole('heading',{name:'Acesse a operação'})).toBeVisible()
})

test('viewer cannot alter incidents or open admin pages', async ({page,request}) => {
  const auth = await request.post('/api/auth/login',{data:{email,password}})
  const headers = {Authorization:`Bearer ${(await auth.json()).access_token}`}
  const viewer = {email:'viewer@e2e.local',password:'viewer-only-strong-password',name:'Observador',role:'Viewer'}
  expect((await request.post('/api/users',{data:viewer,headers})).status()).toBe(201)
  const loginResponse = await request.post('/api/auth/login',{data:{email:viewer.email,password:viewer.password}})
  const viewerHeaders = {Authorization:`Bearer ${(await loginResponse.json()).access_token}`}
  expect((await request.get('/api/integrations',{headers:viewerHeaders})).status()).toBe(403)
  const integrations = await (await request.get('/api/integrations', {headers})).json()
  const timestamp = String(Math.floor(Date.now()/1000))
  const body = JSON.stringify({external_id:'viewer-browser-01',host:'lab-viewer-01',event_type:'HOST',state:'CRIT',output:'Synthetic viewer test',observed_at:new Date().toISOString()})
  const signature = `sha256=${createHmac('sha256',secret).update(`${timestamp}.${body}`).digest('hex')}`
  expect((await request.post(`/api/webhooks/checkmk/${integrations[0].id}`,{data:body,headers:{'Content-Type':'application/json','X-Sentinel-Timestamp':timestamp,'X-Sentinel-Signature':signature}})).status()).toBe(201)
  const incidents = await (await request.get('/api/incidents',{headers})).json()
  expect(incidents.total).toBeGreaterThan(0)
  expect((await request.patch(`/api/incidents/${incidents.items[0].id}/status`,{data:{status:'OPEN'},headers:viewerHeaders})).status()).toBe(403)
  await login(page,viewer.email,viewer.password)
  await expect(page.getByRole('link',{name:'Integrações',exact:true})).toHaveCount(0)
  await page.getByRole('link',{name:'lab-viewer-01',exact:true}).click()
  await expect(page.getByText('Perfil Viewer: acesso de leitura.')).toBeVisible()
  await expect(page.getByRole('button',{name:'Reabrir',exact:true})).toHaveCount(0)
})
