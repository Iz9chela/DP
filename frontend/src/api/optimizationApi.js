const BASE_URL = 'http://localhost:8000';

// Creates a new optimized prompt (POST)
export async function createOptimizedPrompt(promptData) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${BASE_URL}/optimizations/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(promptData),
  });
  if (!response.ok) {
    throw new Error('Failed to create optimized prompt');
  }
  return await response.json();
}

// Updates an existing optimized prompt (PUT)
// e.g., add_expert_persona or add_emotional_stimulus
export async function updateOptimizedPrompt(promptId, updateData) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${BASE_URL}/optimizations/${promptId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(updateData),
  });
  if (!response.ok) {
    throw new Error('Failed to update optimized prompt');
  }
  return await response.json();
}
