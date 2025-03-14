import * as jwtDecodeModule from 'jwt-decode';

const BASE_URL = 'http://localhost:8000';

export function getUserIdFromToken(token) {
  const decoded = jwtDecodeModule.jwtDecode(token);
  return decoded.sub;
}

export async function fetchUserById(userId) {
  const jwt = localStorage.getItem('token');
  const res = await fetch(`${BASE_URL}/users/${userId}`, {
    headers: { Authorization: `Bearer ${jwt}` }
  });
  if (!res.ok) throw new Error('Failed to fetch user info');
  return await res.json();
}