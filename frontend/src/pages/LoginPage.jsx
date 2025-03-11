import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../api/authApi';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const data = await loginUser(email, password);
      // data will contain { access_token, token_type, ... }
      // Save token to localStorage or context for further requests
      localStorage.setItem('token', data.access_token);
      // Navigate to whatever page
      navigate('/optimize'); // or /evaluate, etc.
    } catch (error) {
      alert(error.message);
    }
  };

  return (
    <div className="flex flex-column align-items-center justify-content-center" style={{minHeight: '100vh'}}>
      <div className="card p-4 shadow-2 surface-card">
        <h2>Welcome Back!</h2>
        <div className="field mb-3">
          <label htmlFor="email" className="block font-medium mb-2">Email Address</label>
          <InputText id="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com"/>
        </div>
        <div className="field mb-3">
          <label htmlFor="password" className="block font-medium mb-2">Password</label>
          <InputText id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <Button label="Log In" className="p-button-success" onClick={handleLogin} />
        <Button label="Sign Up" className="p-button-text mt-3" onClick={() => navigate('/register')} />
      </div>
    </div>
  );
}

export default LoginPage;
