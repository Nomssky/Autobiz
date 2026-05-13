'use client';

import { Bell, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useStore } from '@/lib/store';

export function Header() {
  const { sidebarOpen, toggleSidebar } = useStore();

  return (
    <header className="sticky top-0 z-30 h-16 bg-slate-900/95 backdrop-blur border-b border-slate-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        {!sidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        )}
        <h1 className="text-lg font-semibold text-white">AutoBiz Dashboard</h1>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="relative text-slate-400 hover:text-white"
        >
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </Button>
        <div className="h-8 w-px bg-slate-700" />
        <Button
          variant="ghost"
          size="sm"
          className="text-slate-400 hover:text-white"
        >
          <LogOut size={16} className="mr-2" />
          Logout
        </Button>
      </div>
    </header>
  );
}