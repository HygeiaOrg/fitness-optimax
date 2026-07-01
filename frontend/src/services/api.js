/**
 * API service for Fitness OptiMax backend.
 * Uses native Fetch API — no external HTTP library needed.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * Fetch all workout targets (Dashboard view).
 * GET /api/targets
 */
export async function fetchTargets() {
  const res = await fetch(`${API_BASE}/api/targets`);
  if (!res.ok) throw new Error(`Failed to fetch targets: ${res.status}`);
  return res.json();
}

/**
 * Fetch SPC chart data for a specific exercise group.
 * GET /api/charts/:exerciseGroup
 */
export async function fetchChartData(exerciseGroup) {
  const encoded = encodeURIComponent(exerciseGroup);
  const res = await fetch(`${API_BASE}/api/charts/${encoded}`);
  if (!res.ok) throw new Error(`Failed to fetch chart data: ${res.status}`);
  return res.json();
}

/**
 * Update training goal for an exercise group.
 * POST /api/goals
 */
export async function updateTrainingGoal(exerciseGroup, trainingGoal) {
  const res = await fetch(`${API_BASE}/api/goals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      exercise_group: exerciseGroup,
      training_goal: trainingGoal,
    }),
  });
  if (!res.ok) throw new Error(`Failed to update goal: ${res.status}`);
  return res.json();
}
