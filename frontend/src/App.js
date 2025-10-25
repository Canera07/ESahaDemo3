import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";

// Pages
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import SahalarPage from "./pages/SahalarPage";
import SahaDetayPage from "./pages/SahaDetayPage";
import ProfilPage from "./pages/ProfilPage";
import TakimAramaPage from "./pages/TakimAramaPage";
import OwnerPanel from "./pages/OwnerPanel";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Setup axios defaults
axios.defaults.withCredentials = true;

export const AuthContext = React.createContext();

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      // Check for session_id in URL fragment (Emergent OAuth)
      const fragment = window.location.hash.substring(1);
      const params = new URLSearchParams(fragment);
      const sessionId = params.get('session_id');

      if (sessionId) {
        // Process Emergent OAuth
        const response = await axios.post(`${API}/auth/google`, { session_id: sessionId });
        setUser(response.data.user);
        localStorage.setItem('session_token', response.data.session_token);
        
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        toast.success('Giriş başarılı!');
      } else {
        // Check existing session
        const token = localStorage.getItem('session_token');
        if (token) {
          const response = await axios.get(`${API}/auth/session`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(response.data);
        }
      }
    } catch (error) {
      console.error('Session check failed:', error);
      localStorage.removeItem('session_token');
    } finally {
      setLoading(false);
    }
  };

  const login = (userData, token) => {
    setUser(userData);
    localStorage.setItem('session_token', token);
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      localStorage.removeItem('session_token');
      toast.success('Çıkış yapıldı');
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={user ? <Navigate to="/dashboard" /> : <LandingPage />} />
            <Route path="/auth" element={user ? <Navigate to="/dashboard" /> : <AuthPage />} />
            <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/auth" />} />
            <Route path="/sahalar" element={user ? <SahalarPage /> : <Navigate to="/auth" />} />
            <Route path="/saha/:id" element={user ? <SahaDetayPage /> : <Navigate to="/auth" />} />
            <Route path="/profil" element={user ? <ProfilPage /> : <Navigate to="/auth" />} />
            <Route path="/takim-arama" element={user ? <TakimAramaPage /> : <Navigate to="/auth" />} />
            <Route path="/owner" element={user && user.role === 'owner' ? <OwnerPanel /> : <Navigate to="/dashboard" />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </AuthContext.Provider>
  );
}

import React from 'react';
export default App;
