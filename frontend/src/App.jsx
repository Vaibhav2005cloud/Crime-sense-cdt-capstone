import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import ProtectedRoute from './ProtectedRoute';
import Layout from './Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import CommandCenter from './pages/CommandCenter';
import CognitiveTwin from './pages/CognitiveTwin';
import Analytics from './pages/Analytics';
import Predictor from './pages/Predictor';
import { Allocation, Explainable, WhatIf, Copilot, Reports } from './pages/OtherPages';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/app" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<CommandCenter />} />
            <Route path="digital-twin" element={<CognitiveTwin />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="predictor" element={<Predictor />} />
            <Route path="allocation" element={<Allocation />} />
            <Route path="explainable" element={<Explainable />} />
            <Route path="whatif" element={<WhatIf />} />
            <Route path="copilot" element={<Copilot />} />
            <Route path="reports" element={<Reports />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
