const BASE = '/api'
// A bit above the backend's own LLM_TIMEOUT_SECONDS (45s), so the backend's
// own timeout fires first in the common case - this is the last-resort
// backstop so a dropped connection (e.g. the dev server reloading mid-request)
// can never hang the UI forever with no feedback.
const REQUEST_TIMEOUT_MS = 60_000

async function fetchWithTimeout(path, options) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    return await fetch(`${BASE}${path}`, { ...options, signal: controller.signal })
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(`${path} timed out after ${REQUEST_TIMEOUT_MS / 1000}s`)
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}

async function postJSON(path, body) {
  const res = await fetchWithTimeout(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`${path} failed with status ${res.status}`)
  }
  return res.json()
}

export async function fetchQuestions() {
  const res = await fetchWithTimeout('/questions')
  if (!res.ok) {
    throw new Error(`questions failed with status ${res.status}`)
  }
  return res.json()
}

export function postOverview(profile) {
  return postJSON('/overview', profile)
}

export function postRecommendations(profile) {
  return postJSON('/recommendations', profile)
}

export function postEvent(sessionId, eventType, payload) {
  // Fire-and-forget: analytics must never block or break the questionnaire.
  fetch(`${BASE}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, event_type: eventType, payload: payload ?? null }),
  }).catch(() => {})
}
