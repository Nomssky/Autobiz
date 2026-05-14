// Shared button component
export function Button({
  children,
  className = '',
  variant = 'default',
  ...props
}) {
  const variants = {
    default: 'bg-blue-600 hover:bg-blue-700 text-white',
    ghost: 'hover:bg-slate-800 text-slate-300',
    outline: 'border border-slate-600 text-slate-300 hover:bg-slate-800',
    destructive: 'bg-red-600 hover:bg-red-700 text-white',
  };

  return (
    <button
      className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}