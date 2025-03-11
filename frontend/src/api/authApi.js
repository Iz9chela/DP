const BASE_URL = 'http://localhost:8000';

export async function registerUser(fullName, email, password) {
  const response = await fetch(`${BASE_URL}/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_name: fullName,
      email,
      password
    }),
  });
  if (!response.ok) {
    throw new Error('Registration failed');
  }
  return await response.json();
}

export async function loginUser(email, password) {
  const response = await fetch(`${BASE_URL}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new Error('Login failed');
  }
  return await response.json();
}
