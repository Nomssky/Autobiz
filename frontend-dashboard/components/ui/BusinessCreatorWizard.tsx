'use client';

import { useState } from 'react';
import { Check, X, Loader2 } from 'lucide-react';

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center space-x-2 py-4">
      {steps.map((step, index) => (
        <div key={step} className="flex items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
              index < currentStep
                ? 'bg-green-500 text-white'
                : index === currentStep
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-400'
            }`}
          >
            {index < currentStep ? <Check size={14} /> : step[0]}
          </div>
          {index < steps.length - 1 && (
            <div
              className={`w-8 h-0.5 ${
                index < currentStep ? 'bg-green-500' : 'bg-slate-700'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

interface FormFieldProps {
  label: string;
  name: string;
  value: string;
  onChange: (name: string, value: string) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
}

export function FormField({
  label, name, value, onChange, placeholder, type = 'text', required, options
}: FormFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-1">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      {options ? (
        <select
          name={name}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          className="w-full p-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select...</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      ) : (
        <input
          type={type}
          name={name}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          placeholder={placeholder}
          required={required}
          className="w-full p-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      )}
    </div>
  );
}

interface LoadingButtonProps {
  children: React.ReactNode;
  loading: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary' | 'danger';
}

export function LoadingButton({
  children, loading, disabled, onClick, type = 'button', variant = 'primary'
}: LoadingButtonProps) {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white',
    secondary: 'bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-slate-200',
    danger: 'bg-red-600 hover:bg-red-700 disabled:bg-slate-700 text-white',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading || disabled}
      className={`px-6 py-2.5 rounded-lg font-medium text-sm transition-colors flex items-center gap-2 ${variants[variant]}`}
    >
      {loading ? <Loader2 size={16} className="animate-spin" /> : null}
      {children}
    </button>
  );
}