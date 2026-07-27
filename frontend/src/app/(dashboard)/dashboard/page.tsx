'use client';

import { useEffect, useState } from 'react';
import api, { getApiError } from '@/lib/api';
import { JobListItem } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Briefcase, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { toast } from 'sonner';

const STATUS_COLORS: Record<string, string> = {
  open: '#3b82f6',
  assigned: '#f59e0b',
  in_progress: '#8b5cf6',
  escalated: '#ef4444',
  closed: '#22c55e',
};

interface Summary {
  job_summary: { total: number; by_status: Record<string, number>; by_priority: Record<string, number> };
  sla_compliance: { total_closed: number; met_sla: number; breached_sla: number; compliance_rate: number; open_breached: number };
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [summaryRes, jobsRes] = await Promise.all([
          api.get('/analytics/summary/'),
          api.get('/jobs/?page_size=5'),
        ]);
        setSummary(summaryRes.data);
        setRecentJobs(jobsRes.data.results || jobsRes.data || []);
      } catch (err) {
        toast.error(getApiError(err, 'Failed to load dashboard'));
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center py-20"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div>;
  }

  const statusData: { name: string; value: number }[] = summary?.job_summary?.by_status
    ? Object.entries(summary.job_summary.by_status).map(([name, value]) => ({ name, value }))
    : [];

  const sla = summary?.sla_compliance;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Total Jobs</CardTitle>
            <Briefcase className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.job_summary?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Open</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.job_summary?.by_status?.open || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Escalated</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{summary?.job_summary?.by_status?.escalated || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">SLA Compliance</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{sla?.compliance_rate || 0}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Jobs by Status</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {statusData.map((entry, i) => (
                    <Cell key={i} fill={STATUS_COLORS[entry.name] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Recent Jobs</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="text-sm font-medium">{job.title}</p>
                    <p className="text-xs text-gray-500">{job.reference_number}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={job.priority === 'critical' ? 'destructive' : 'secondary'}>
                      {job.priority}
                    </Badge>
                    <Badge style={{ backgroundColor: STATUS_COLORS[job.status], color: 'white' }}>
                      {job.status}
                    </Badge>
                  </div>
                </div>
              ))}
              {recentJobs.length === 0 && (
                <p className="py-4 text-center text-sm text-gray-500">No jobs yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
