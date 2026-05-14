import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Businesses | AutoBiz',
};

export default function BusinessesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Businesses</h1>
          <p className="text-slate-400">Manage and monitor your autonomous businesses</p>
        </div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center">
        <div className="text-6xl mb-4">🏗️</div>
        <h3 className="text-lg font-medium text-slate-300 mb-2">Business listing</h3>
        <p className="text-slate-500">This page will display all your businesses with status, metrics, and actions.</p>
        <div className="mt-6 flex gap-3 justify-center">
          <a
            href="/businesses/new"
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            + Create Business
          </a>
          <a
            href="/businesses"
            className="inline-flex items-center px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium text-sm transition-colors"
          >
            View All
          </a>
        </div>
      </div>
    </div>
  );
}