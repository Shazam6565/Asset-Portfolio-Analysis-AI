'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import PortfolioTable from '@/components/dashboard/PortfolioTable';
import ChatInterface from '@/components/dashboard/ChatInterface';
import LoginModal from '@/components/auth/LoginModal';
import { api } from '@/lib/api';

export default function Home() {
  const [showLogin, setShowLogin] = useState(false);
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [equity, setEquity] = useState(0);
  // Theme state management with persistence
  const [theme, setTheme] = useState('dark'); // Default to dark (Navy)

  useEffect(() => {
    // Check localStorage on mount
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      // Default to dark if no preference
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await api.getPortfolio();
      setPortfolio(res.data);
      // Calculate total equity
      const total = res.data.reduce((acc: number, item: any) => acc + item.value, 0);
      setEquity(total);
    } catch (err) {
      console.error(err);
      setShowLogin(true); // Assuming failure means not logged in for now
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="flex h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans overflow-hidden">
      {showLogin && (
        <LoginModal
          onCheckLogin={() => {
            setShowLogin(false);
            fetchData();
          }}
          onClose={() => setShowLogin(false)}
        />
      )}

      {/* Sidebar - Fixed width */}
      <div className="w-16 flex-none z-50 border-r border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <Sidebar toggleTheme={toggleTheme} currentTheme={theme} />
      </div>

      {/* Main Content Area - Split 50/50 */}
      <main className="flex-1 flex overflow-hidden">

        {/* Left Pane: Portfolio (50%) */}
        <div className="w-1/2 flex flex-col h-full bg-[var(--bg-primary)] overflow-hidden">
          <header className="flex-none p-8 border-b border-[var(--border-subtle)]">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight">Dashboard</h1>
                <p className="text-[var(--text-secondary)] mt-1">Overview</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-[var(--accent-primary)] font-mono uppercase tracking-wider">Market Open</p>
                <div className="flex gap-2 mt-2">
                  <button onClick={() => setShowLogin(true)} className="text-xs font-medium text-[var(--accent-primary)] border border-[var(--accent-primary)] px-3 py-1.5 rounded-full hover:bg-[var(--accent-primary)]/10 transition-colors">
                    Connect
                  </button>
                </div>
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto p-8 pt-6">
            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="bg-[var(--bg-secondary)] p-6 rounded-xl border border-[var(--border-subtle)]">
                <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Total Equity</p>
                <p className="text-3xl font-bold text-[var(--text-primary)] font-mono tracking-tight">${equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                <p className="text-xs text-[var(--accent-primary)] mt-2 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-[var(--accent-primary)]"></span>
                  Live
                </p>
              </div>
              <div className="bg-[var(--bg-secondary)] p-6 rounded-xl border border-[var(--border-subtle)]">
                <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Day's P&L</p>
                <p className="text-3xl font-bold text-[var(--text-primary)] font-mono tracking-tight text-[var(--text-muted)]">--</p>
              </div>
            </div>

            <div className="bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-subtle)] overflow-hidden">
              <PortfolioTable data={portfolio} loading={loading} />
            </div>
          </div>
        </div>

        {/* Right Pane: Chat Interface (50%) */}
        <div className="w-1/2 flex flex-col h-full bg-[var(--bg-secondary)] border-l border-[var(--border-subtle)]">
          <ChatInterface />
        </div>

      </main>
    </div>
  );
}
