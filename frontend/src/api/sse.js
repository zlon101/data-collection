export function createEventSource(taskId, handlers) {
  const es = new EventSource(`/api/collector/sse/${taskId}`)

  es.addEventListener('log', (e) => {
    handlers.onLog?.(JSON.parse(e.data))
  })
  es.addEventListener('complete', (e) => {
    handlers.onComplete?.(JSON.parse(e.data))
    es.close()
  })
  es.addEventListener('error', (e) => {
    handlers.onError?.(JSON.parse(e.data))
    es.close()
  })

  return es
}
