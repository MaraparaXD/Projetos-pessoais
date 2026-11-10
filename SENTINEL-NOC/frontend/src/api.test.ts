import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, setToken } from './api'
import { duration } from './format'

afterEach(() => {setToken(null); vi.unstubAllGlobals()})
describe('API transport', () => {
  it('attaches the in-memory bearer token', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('{"ok":true}', {status:200}))
    vi.stubGlobal('fetch', fetch); setToken('ephemeral-token')
    expect(await api('/auth/me')).toEqual({ok:true})
    expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer ephemeral-token')
  })
  it('handles successful empty logout responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, {status:204})))
    expect(await api('/auth/logout', {method:'POST'})).toBeUndefined()
  })
  it('invalidates authenticated sessions on 401', async () => {
    const dispatchEvent = vi.fn(); vi.stubGlobal('window', {dispatchEvent})
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', {status:401}))); setToken('expired')
    await expect(api('/incidents')).rejects.toMatchObject({status:401})
    expect(dispatchEvent).toHaveBeenCalledOnce()
  })
  it('provides an actionable error for network failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    await expect(api('/dashboard')).rejects.toBeInstanceOf(ApiError)
  })
  it('does not invent an average when no samples exist', () => {
    expect(duration(null)).toBe('Sem amostra'); expect(duration(0)).toBe('0 s')
  })
})
