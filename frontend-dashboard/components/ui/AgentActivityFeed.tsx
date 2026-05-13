'use client';

import { useState, useEffect, useRef } from 'react';
import { useRealtimeUpdates } from '@/app/hooks/useRealtimeUpdates';

interface AgentActivityItemProps {
  agent: {
    role: string;
    task: string;
    status: 'completed' | 'running' | 'pending' | 'failed';
    time: string;
    output?: string;
  };
}

export function AgentActivityItem({ agent }: AgentActivityItemProps) {
  const statusColors: Record<string, string> = {
    completed: 'bg-green-500/20 text-green-400',
    running: 'bg-blue-500/20 text-blue-400',
    pending: 'bg-yellow-500/20 text-yellow-400',
    failed: 'bg-red-500/20 text-red-400',
  };

  const statusIcons: Record<string, string> = {
    completed: '\u2713',
    running: '\u27F3',
    pending: '\u25CB',
    failed: '\u2717',
  };

  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-700 last:border-0">
      <div className="flex items-center gap-3 flex-1">
        <span className="text-lg">{statusIcons[agent.status]}</span>
        <div>
          <p className="text-sm font-medium text-white capitalize">{agent.role}</p>
          <p className="text-xs text-slate-400">{agent.task}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[agent.status]}`}>
          {agent.status}
        </span>
        <span className="text-xs text-slate-500 whitespace-nowrap">{agent.time}</span>
      </div>
    </div>
  );
}

interface AgentActivityFeedProps {
  activities?: Array<{
    role: string;
    task: string;
    status: 'completed' | 'running' | 'pending' | 'failed';
    time: string;
    output?: string;
  }>;
  title?: string;
  businessId?: string;
  loading?: boolean;
  maxItems?: number;
}

export function AgentActivityFeed({
  activities: initialActivities,
  title = 'Agent Activity',
  businessId,
  loading: externalLoading,
  maxItems = 50,
}: AgentActivityFeedProps) {
  const [activities, setActivities] = useState(initialActivities || []);
  const [showOutput, setShowOutput] = useState<string | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  const { lastEvent, connected } = useRealtimeUpdates(businessId);

  useEffect(() => {
    if (initialActivities) {
      setActivities(initialActivities.slice(0, maxItems));
    }
  }, [initialActivities, maxItems]);

  useEffect(() => {
    if (lastEvent?.type === 'agent_task_update') {
      const newActivity = {
        role: lastEvent.data?.role_name || 'unknown',
        task: lastEvent.data?.task_type || 'Unknown task',
        status: (lastEvent.data?.status || 'pending') as 'completed' | 'running' | 'pending' | 'failed',
        time: new Date().toLocaleTimeString(),
        output: lastEvent.data?.output_data,
      };
      setActivities((prev) => [newActivity, ...prev].slice(0, maxItems));
    }
  }, [lastEvent, maxItems]);

  if (externalLoading) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 py-3 border-b border-slate-700">
              <div className="w-6 h-6 bg-slate-700 rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-slate-700 rounded w-24 mb-1" />
                <div className="h-3 bg-slate-700 rounded w-40" />
              </div>
              <div className="h-4 bg-slate-700 rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        {connected && (
          <span className="flex items-center gap-1.5 text-xs text-green-400">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            Live
          </span>
        )}
      </div>
      <div ref={feedRef} className="space-y-1 max-h-96 overflow-y-auto">
        {activities.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-slate-500">
            <span className="text-2xl text-slate-600">{'\u25CB'}</span>
            <p className="text-sm">No activity yet</p>
            <p className="text-xs">Agent activity will appear here in real time</p>
          </div>
        ) : (
          activities.map((activity, i) => (
            <div
              key={`${activity.role}-${i}`}
              className="cursor-pointer"
              onClick={() => setShowOutput(showOutput === `${i}` ? null : `${i}`)}
            >
              <AgentActivityItem agent={activity} />
              {showOutput === `${i}` && activity.output && (
                <div className="ml-9 mb-2 p-3 bg-slate-900/50 rounded-lg text-xs text-slate-400 font-mono">
                  {activity.output}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
