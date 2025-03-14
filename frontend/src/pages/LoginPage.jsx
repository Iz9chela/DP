import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../api/authApi';
import { getUserIdFromToken, fetchUserById } from '../api/userApi';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleLogin() {
    try {
      // 1) Perform the login, get token
      const data = await loginUser(email, password);
      // data => { access_token, token_type, ... }

      // 2) Store token in localStorage
      localStorage.setItem('token', data.access_token);

      // 3) Decode token to get user ID
      const userId = getUserIdFromToken(data.access_token);

      // 4) Fetch user doc to get full_name
      const userDoc = await fetchUserById(userId);

      // 5) Store the full_name in localStorage for other pages
      localStorage.setItem('fullName', userDoc.full_name);

      // 6) Navigate to e.g. the Compare page
      navigate('/optimize');
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  return (
    <div className="flex flex-column align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
      <div className="card p-4 shadow-2 surface-card">
        <h2>Welcome Back!</h2>
        <div className="field mb-3">
          <label htmlFor="email" className="block font-medium mb-2">Email Address</label>
          <InputText
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
          />
        </div>
        <div className="field mb-3">
          <label htmlFor="password" className="block font-medium mb-2">Password</label>
          <InputText
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button label="Log In" className="p-button-success" onClick={handleLogin} />
        <Button label="Sign Up" className="p-button-text mt-3" onClick={() => navigate('/register')} />
      </div>
    </div>
  );
}

export default LoginPage;
