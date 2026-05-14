'use client';

interface AlertProps {
  type: 'warning' | 'success' | 'error' | 'info';
  message: string;
}

export function Alert({ type, message }: AlertProps) {
  const styles: Record<string, string> = {
    warning: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300',
    success: 'bg-green-500/10 border-green-500/30 text-green-300',
    error: 'bg-red-500/10 border-red-500/30 text-red-300',
    info: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
  };

  const icons: Record<string, string> = {
    warning: '⚠️',
    success: '✅',
    error: '❌',
    info: 'ℹ️',
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${styles[type]}`}>
      <span className="text-sm mt-0.5">{icons[type]}</span>
      <p className="text-sm">{message}</p>
    </div>
  );
}