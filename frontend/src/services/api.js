/**
 * API service for Fitness OptiMax backend.
 * Uses native Fetch API — no external HTTP library needed.
 */

const API_BASE = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_BASE || 'http://localhost:8000');

export const DIAGNOSTICS_URL = `${API_BASE}/api/diagnostics`;

/**
 * Turn a failed response into an Error carrying the backend's explanation.
 * The API always answers with { detail, code, hint } — showing only the status
 * code (the old behaviour) made failures impossible to diagnose from the UI.
 */
async function toError(res, fallback) {
  let body = null;
  try {
    body = await res.json();
  } catch {
    // Non-JSON body (proxy error page, timeout). Fall through to the status.
  }

  const detail = body?.detail || `${fallback} (HTTP ${res.status})`;
  const error = new Error(detail);
  error.status = res.status;
  error.code = body?.code;
  error.hint = body?.hint;
  return error;
}

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, options);
  } catch (networkError) {
    const error = new Error(`Cannot reach the API: ${networkError.message}`);
    error.code = 'network';
    throw error;
  }
  if (!res.ok) throw await toError(res, `Request to ${path} failed`);
  return res.json();
}

/**
 * Fetch all workout targets (Dashboard view).
 * GET /api/targets
 */
export async function fetchTargets() {
  return request('/api/targets');
}

/**
 * Fetch SPC chart data for a specific exercise group.
 * GET /api/charts/:exerciseGroup
 */
export async function fetchChartData(exerciseGroup) {
  return request(`/api/charts/${encodeURIComponent(exerciseGroup)}`);
}

/**
 * Log a workout session.
 * POST /api/workouts
 */
export async function logWorkout(workoutData) {
  return request('/api/workouts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workoutData)
  });
}

/**
 * Current 1RM per lift for an athlete.
 * GET /api/one-rep-maxes?athlete_name=…  →  { lift: kg, … }
 */
export async function fetchOneRepMaxes(athleteName) {
  const body = await request(`/api/one-rep-maxes?athlete_name=${encodeURIComponent(athleteName)}`);
  return Object.fromEntries(body.one_rep_maxes.map(m => [m.lift, m.one_rm_kg]));
}

/**
 * Record a new 1RM for a lift.
 * POST /api/one-rep-maxes
 */
export async function saveOneRepMax(athleteName, lift, oneRmKg) {
  return request('/api/one-rep-maxes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ athlete_name: athleteName, lift, one_rm_kg: oneRmKg })
  });
}

/**
 * Probe every layer of the BigQuery pipeline.
 * GET /api/diagnostics
 */
export async function fetchDiagnostics() {
  return request('/api/diagnostics');
}
