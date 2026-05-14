'use client';

import { createContext, useContext } from 'react';
import { useStore } from '@/lib/store';

interface AppContextValue {
  store: ReturnType<typeof useStore>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function Providers({ children }: { children: React.ReactNode }) {
  const store = useStore();

  return (
    <AppContext.Provider value={{ store }}>
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within Providers');
  return ctx;
};