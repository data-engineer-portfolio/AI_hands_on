'use client';

import { useState } from 'react';
import LoginForm from '@/components/LoginForm';
import ChatWindow from '@/components/ChatWindow';

export interface User {
  username: string;
  role: string;
  token: string;
  collections: string[];
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);

  const handleLogin = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setUser(null);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {!user ? (
        <LoginForm onLogin={handleLogin} />
      ) : (
        <ChatWindow user={user} onLogout={handleLogout} />
      )}
    </main>
  );
}
