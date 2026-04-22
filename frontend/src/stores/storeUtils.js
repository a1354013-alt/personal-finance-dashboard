export function toErrorMessage(error, fallback = 'Request failed.') {
  if (!error) return fallback
  if (typeof error === 'string') return error
  if (error instanceof Error && error.message) return error.message
  const message = error?.message
  return typeof message === 'string' && message.trim() ? message : fallback
}

