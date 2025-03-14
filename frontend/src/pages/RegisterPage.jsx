import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../api/authApi';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';

function RegisterPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleRegister() {
    try {
      await registerUser(fullName, email, password);
      // Then direct to login
      navigate('/');
    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  }

  return (
    <div className="flex flex-column align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
      <div className="card p-4 shadow-2 surface-card">
        <h2>Create Your Account</h2>
        <div className="field mb-3">
          <label htmlFor="fullname" className="block font-medium mb-2">Full Name</label>
          <InputText
            id="fullname"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div className="field mb-3">
          <label htmlFor="email" className="block font-medium mb-2">Email</label>
          <InputText
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
        <Button label="Sign Up" className="p-button-success" onClick={handleRegister} />
        <Button label="Back to Login" className="p-button-text mt-3" onClick={() => navigate('/')} />
      </div>
    </div>
  );
}

export default RegisterPage;
