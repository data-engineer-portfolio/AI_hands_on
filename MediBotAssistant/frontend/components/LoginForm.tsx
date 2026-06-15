'use client';

import { useState } from 'react';
import { User } from '@/app/page';

const DEMO_USERS = [
  { username: 'dr.mehta', password: 'doctor123', role: 'doctor', label: '👨‍⚕️ Dr. Mehta (Doctor)' },
  { username: 'nurse.priya', password: 'nurse123', role: 'nurse', label: '👩‍⚕️ Nurse Priya (Nurse)' },
  { username: 'billing.ravi', password: 'billing123', role: 'billing_executive', label: '💼 Billing Ravi (Billing Executive)' },
  { username: 'tech.anand', password: 'tech123', role: 'technician', label: '🔧 Tech Anand (Technician)' },
  { username: 'admin.sys', password: 'admin123', role: 'admin', label: '⚙️ Admin (Administrator)' },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface LoginFormProps {
  onLogin: (user: User) => void;
}

export default function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (u?: string, p?: string) => {
    const loginUsername = u || username;
    const loginPassword = p || password;

    if (!loginUsername || !loginPassword) {
      setError('Please enter username and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Login
      const loginRes = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });

      if (!loginRes.ok) {
        setError('Invalid username or password');
        setLoading(false);
        return;
      }

      const loginData = await loginRes.json();

      // Get collections for this role
      const colRes = await fetch(`${API_URL}/collections/${loginData.role}`);
      const colData = await colRes.json();

      onLogin({
        username: loginData.username,
        role: loginData.role,
        token: loginData.access_token,
        collections: colData.collections,
      });
    } catch (err) {
      setError('Cannot connect to server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = (demo: typeof DEMO_USERS[0]) => {
    setUsername(demo.username);
    setPassword(demo.password);
    handleLogin(demo.username, demo.password);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🏥</div>
          <h1 className="text-3xl font-bold text-gray-800">MediBot</h1>
          <p className="text-gray-500 mt-1">MediAssist Health Network AI Assistant</p>
        </div>

        {/* Login Form */}
        <div className="space-y-4 mb-6">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
            className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            onClick={() => handleLogin()}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </div>

        {/* Demo Users */}
        <div>
          <p className="text-sm text-gray-500 text-center mb-3">— or login as demo user —</p>
          <div className="space-y-2">
            {DEMO_USERS.map((demo) => (
              <button
                key={demo.username}
                onClick={() => handleDemoLogin(demo)}
                disabled={loading}
                className="w-full text-left px-4 py-2 bg-gray-50 hover:bg-blue-50 border border-gray-200 rounded-lg text-sm transition disabled:opacity-50"
              >
                {demo.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
