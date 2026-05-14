'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bell, LayoutDashboard, Building2, ClipboardList, BarChart3, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useStore } from '@/lib/store';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Businesses', href: '/businesses', icon: Building2 },
  { label: 'Approvals', href: '/approvals', icon: ClipboardList },
  { label: 'Metrics', href: '/metrics', icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useStore();

  return (
    <>
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white lg:hidden"
      >
        <LayoutDashboard size={20} />
      </button>

      <aside
        className={`fixed top-0 left-0 z-40 h-full w-64 bg-slate-900 border-r border-slate-700 transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="px-6 py-5 border-b border-slate-700">
            <h2 className="text-xl font-bold text-blue-400">AutoBiz</h2>
            <p className="text-xs text-slate-500 mt-1">AI-Powered Business Platform</p>
          </div>

          <nav className="flex-1 px-4 py-4 space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <Icon size={18} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="px-4 py-4 border-t border-slate-700">
            <Button
              variant="ghost"
              className="w-full justify-start text-slate-400 hover:text-white"
            >
              <Settings size={18} className="mr-3" />
              Settings
            </Button>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
    </>
  );
}