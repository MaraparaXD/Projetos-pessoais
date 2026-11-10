let token: string | null = null
export const setToken = (value: string | null) => { token = value }

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message) }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      ...options, headers: {...(options.body ? {'Content-Type': 'application/json'} : {}),
        ...(token ? {Authorization: `Bearer ${token}`} : {}), ...options.headers},
    })
  } catch {
    throw new ApiError('Não foi possível conectar à API. Verifique o backend e tente novamente.', 0)
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    if (response.status === 401 && token) window.dispatchEvent(new CustomEvent('session-expired'))
    const message = response.status === 401 ? 'E-mail ou senha inválidos, ou sessão expirada.'
      : response.status === 403 ? 'Seu perfil não permite esta ação.'
      : response.status === 429 ? 'Muitas tentativas. Aguarde um minuto e tente novamente.'
      : typeof data.detail === 'string' ? data.detail : 'Dados inválidos. Revise os campos e tente novamente.'
    throw new ApiError(message, response.status)
  }
  return response.status === 204 ? undefined as T : response.json()
}

export const send = <T>(path: string, body: unknown, method = 'POST') => api<T>(path, {method, body: JSON.stringify(body)})
