import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { BusinessCard } from '@/components/ui/BusinessCard';

export default function HomePage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBusinesses();
  }, []);

  const fetchBusinesses = async () => {
    setLoading(true);
    try {
      const data = await api.getBusinesses();
      setBusinesses(data);
    } catch {
      setBusinesses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBusiness = () => {
    router.push('/businesses/new');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">AutoBiz Dashboard</h1>
          <p className="text-slate-400 mt-1">AI-powered autonomous business platform</p>
        </div>
        <button
          onClick={handleCreateBusiness}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          + New Business
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      ) : businesses.length === 0 ? (
        <div className="text-center py-20 text-slate-400">
          <p className="text-xl mb-2">No businesses yet</p>
          <button
            onClick={handleCreateBusiness}
            className="text-blue-500 hover:text-blue-400 underline"
          >
            Create your first business
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {businesses.map((biz) => (
            <BusinessCard
              key={biz.id}
              business={biz}
              onView={(id) => router.push(`/businesses/${id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}