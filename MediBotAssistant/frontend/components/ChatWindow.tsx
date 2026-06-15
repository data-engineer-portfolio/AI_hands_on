'use client';

import { useState, useRef, useEffect } from 'react';
import { User } from '@/app/page';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Source {
  source_document: string;
  section_title: string;
  collection: string;
}

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  retrieval_type?: string;
  blocked?: boolean;
}

interface ChatWindowProps {
  user: User;
  onLogout: () => void;
}

const ROLE_COLORS: Record<string, string> = {
  doctor: 'bg-green-100 text-green-800',
  nurse: 'bg-pink-100 text-pink-800',
  billing_executive: 'bg-yellow-100 text-yellow-800',
  technician: 'bg-orange-100 text-orange-800',
  admin: 'bg-purple-100 text-purple-800',
};

const ROLE_ICONS: Record<string, string> = {
  doctor: '👨‍⚕️',
  nurse: '👩‍⚕️',
  billing_executive: '💼',
  technician: '🔧',
  admin: '⚙️',
};

const SAMPLE_QUESTIONS: Record<string, string[]> = {
  doctor: ['What is the treatment protocol for Type 2 diabetes?', 'What are the drug interactions for metformin?'],
  nurse: ['What is the correct IV cannula size for a paediatric patient under 5kg?', 'What are the ICU infection control guidelines?'],
  billing_executive: ['How many claims are pending vs approved?', 'What is the total approved claim amount?'],
  technician: ['What are the equipment calibration procedures?', 'What is the preventive maintenance schedule?'],
  admin: ['What is the staff leave policy?', 'How many open maintenance tickets are there by category?'],
};

export default function ChatWindow({ user, onLogout }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: 'assistant',
      content: `Hello ${user.username}! I'm MediBot. I can answer questions from the **${user.collections.join(', ')}** collections. How can I help you today?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (question?: string) => {
    const q = question || input.trim();
    if (!q || loading) return;

    setInput('');
    const userMsg: Message = { id: Date.now(), role: 'user', content: q };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, token: user.token }),
      });

      const data = await res.json();

      const assistantMsg: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        retrieval_type: data.retrieval_type,
        blocked: data.sources?.length === 0 && data.answer.includes("don't have access"),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: '❌ Error connecting to server. Please make sure the backend is running.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col p-4">
        {/* User Info */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">{ROLE_ICONS[user.role] || '👤'}</span>
            <div>
              <p className="font-semibold text-gray-800">{user.username}</p>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${ROLE_COLORS[user.role] || 'bg-gray-100'}`}>
                {user.role.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Collections */}
        <div className="mb-6">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Accessible Collections
          </p>
          <div className="space-y-1">
            {user.collections.map((col) => (
              <div key={col} className="flex items-center gap-2 px-3 py-2 bg-blue-50 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-blue-700 capitalize">{col}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sample Questions */}
        <div className="mb-6 flex-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Sample Questions
          </p>
          <div className="space-y-2">
            {(SAMPLE_QUESTIONS[user.role] || []).map((q, i) => (
              <button
                key={i}
                onClick={() => sendMessage(q)}
                className="w-full text-left text-xs px-3 py-2 bg-gray-50 hover:bg-blue-50 border border-gray-200 rounded-lg transition text-gray-600"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Logout */}
        <button
          onClick={onLogout}
          className="w-full px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition"
        >
          Logout
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-xl font-bold text-gray-800">🏥 MediBot</h1>
          <p className="text-sm text-gray-500">AI Assistant for MediAssist Health Network</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-2xl ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                {/* Bubble */}
                <div className={`px-4 py-3 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : msg.blocked
                    ? 'bg-red-50 border border-red-200 text-red-800 rounded-bl-sm'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>

                {/* Retrieval type badge */}
                {msg.retrieval_type && (
                  <div className="mt-1 flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      msg.retrieval_type === 'sql_rag'
                        ? 'bg-purple-100 text-purple-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {msg.retrieval_type === 'sql_rag' ? '🗄️ SQL RAG' : '🔍 Hybrid RAG'}
                    </span>
                  </div>
                )}

                {/* Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-gray-500 font-medium">📚 Sources:</p>
                    {msg.sources.map((src, i) => (
                      <div key={i} className="text-xs bg-gray-50 border border-gray-200 rounded px-2 py-1">
                        <span className="font-medium text-gray-700">{src.source_document}</span>
                        <span className="text-gray-400"> · {src.section_title}</span>
                        <span className={`ml-1 px-1 rounded text-xs ${ROLE_COLORS[user.role] || 'bg-gray-100'}`}>
                          {src.collection}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask a question..."
              disabled={loading}
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
