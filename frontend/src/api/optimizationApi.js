// src/api/optimizationApi.js

export async function createOptimizedPrompt(promptData) {
    const token = localStorage.getItem('token'); // Retrieve token after login
    const response = await fetch('http://localhost:8000/optimizations/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,  // attach the JWT
      },
      body: JSON.stringify(promptData),
    });
    if (!response.ok) {
      throw new Error('Failed to create optimized prompt');
    }
    return await response.json();
  }
  