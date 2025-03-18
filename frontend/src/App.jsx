import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ComparePage from './pages/ComparePage';
import EvaluationPage from './pages/EvaluationPage';
import OptimizationPage from './pages/OptimizationPage';
import BlindResultsPage from './pages/BlindResultsPage';

function App() {
  return (
    <Router>
      {/* If you want a global NavBar, place it here */}
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/evaluate" element={<EvaluationPage />} />
        <Route path="/optimize" element={<OptimizationPage />} />
        <Route path="/blind" element={<BlindResultsPage />} />
      </Routes>
    </Router>
  );
}

export default App;
