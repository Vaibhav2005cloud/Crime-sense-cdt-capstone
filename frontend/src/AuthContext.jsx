import { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('cdt_user');
    return raw ? JSON.parse(raw) : null;
  });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('cdt_token');
    if (!token) { setReady(true); return; }
    api.me().then((u) => {
      setUser(u);
      localStorage.setItem('cdt_user', JSON.stringify(u));
    }).catch(() => {
      localStorage.removeItem('cdt_token');
      localStorage.removeItem('cdt_user');
      setUser(null);
    }).finally(() => setReady(true));
  }, []);

  async function login(username, password) {
    const res = await api.login(username, password);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('cdt_token', data.token);
    const u = { username: data.username, role: data.role, name: data.name };
    localStorage.setItem('cdt_user', JSON.stringify(u));
    setUser(u);
    return u;
  }

  async function logout() {
    try { await api.logout(); } catch { /* ignore */ }
    localStorage.removeItem('cdt_token');
    localStorage.removeItem('cdt_user');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, ready, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
