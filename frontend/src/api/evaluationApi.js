const BASE_URL = 'http://localhost:8000';

export async function createEvaluation(evaluationData) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${BASE_URL}/evaluations/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(evaluationData),
  });
  if (!response.ok) {
    throw new Error('Evaluation failed');
  }
  return await response.json();
}

export async function createComparison(evaluationData) {
  const token = localStorage.getItem('token');
  const response = await fetch(`${BASE_URL}/evaluations/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(evaluationData),
  });
  if (!response.ok) {
    throw new Error('Comparison request failed');
  }
  return await response.json();
}
