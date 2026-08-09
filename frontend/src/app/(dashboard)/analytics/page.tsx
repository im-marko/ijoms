'use client';

import { useEffect, useState } from 'react';
import api, { getApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { isManagerOrAbove } from '@/lib/roles';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell,
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444', '#22c55e', '#06b6d4'];

interface TechPerf {
  technician_id: number;
  name: string;
  total_jobs: number;
  completed: number;
  in_progress: number;
  avg_resolution_hours: number | null;
}

interface AnalyticsSummary {
  job_summary: { total: number; by_status: Record<string, number>; by_priority: Record<string, number> };
  sla_compliance: { total_closed: number; met_sla: number; breached_sla: number; compliance_rate: number; open_breached: number };
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [techPerf, setTechPerf] = useState<TechPerf[]>([]);
  const [jobVolume, setJobVolume] = useState<{ period: string; count: number }[]>([]);
  const [escalations, setEscalations] = useState<{ date: string; count: number }[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [period, setPeriod] = useState('daily');
  const [days, setDays] = useState('30');

  // technician-performance and CSV export are manager-and-above on the backend
  const managerView = !!user && isManagerOrAbove(user.role);

  useEffect(() => {
    api.get('/analytics/summary/').then((r) => setSummary(r.data))
      .catch((err) => toast.error(getApiError(err, 'Failed to load summary')));
    api.get('/analytics/escalation-trends/').then((r) => setEscalations(r.data))
      .catch((err) => toast.error(getApiError(err, 'Failed to load escalation trends')));
  }, []);

  useEffect(() => {
    if (!managerView) return;
    api.get('/analytics/technician-performance/').then((r) => setTechPerf(r.data))
      .catch((err) => toast.error(getApiError(err, 'Failed to load technician performance')));
  }, [managerView]);

  useEffect(() => {
    api.get(`/analytics/job-volume/?period=${period}&days=${days}`)
      .then((r) => setJobVolume(r.data))
      .catch((err) => toast.error(getApiError(err, 'Failed to load job volume')));
  }, [period, days]);

  const exportCSV = async () => {
    try {
      const res = await api.get('/analytics/export/jobs/', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'jobs_export.csv';
      a.click();
    } catch (err) {
      toast.error(getApiError(err, 'Failed to export CSV'));
    }
  };

  const statusData: { name: string; value: number }[] = summary?.job_summary?.by_status
    ? Object.entries(summary.job_summary.by_status as Record<string, number>).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analytics & Reports</h1>
        {managerView && (
          <Button variant="outline" onClick={exportCSV}>
            <Download className="mr-2 h-4 w-4" />Export CSV
          </Button>
        )}
      </div>

      {/* SLA & Summary */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500">Total Jobs</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{summary.job_summary.total}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500">SLA Compliance</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-green-600">{summary.sla_compliance.compliance_rate}%</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500">Met SLA</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{summary.sla_compliance.met_sla}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm text-gray-500">Breached SLA</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-red-600">{summary.sla_compliance.breached_sla}</div></CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Job Volume */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Job Volume</CardTitle>
              <div className="flex gap-2">
                <Select value={period} onValueChange={(v) => v && setPeriod(String(v))} items={[{ value: 'daily', label: 'Daily' }, { value: 'weekly', label: 'Weekly' }, { value: 'monthly', label: 'Monthly' }]}>
                  <SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={days} onValueChange={(v) => v && setDays(String(v))} items={[{ value: '7', label: '7 days' }, { value: '30', label: '30 days' }, { value: '90', label: '90 days' }]}>
                  <SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">7 days</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={jobVolume}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" tickFormatter={(v) => new Date(v).toLocaleDateString()} />
                <YAxis />
                <Tooltip labelFormatter={(v) => new Date(v).toLocaleDateString()} />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Status Distribution */}
        <Card>
          <CardHeader><CardTitle>Job Status Distribution</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Escalation Trends */}
        <Card>
          <CardHeader><CardTitle>Escalation Trends</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={escalations}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(v) => new Date(v).toLocaleDateString()} />
                <YAxis />
                <Tooltip labelFormatter={(v) => new Date(v).toLocaleDateString()} />
                <Line type="monotone" dataKey="count" stroke="#ef4444" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Technician Performance (manager+ only) */}
        {managerView && (
        <Card>
          <CardHeader><CardTitle>Technician Performance</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {techPerf.map((t) => (
                <div key={t.technician_id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="text-sm font-medium">{t.name}</p>
                    <p className="text-xs text-gray-500">{t.completed} completed, {t.in_progress} active</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">{t.total_jobs} total</p>
                    {t.avg_resolution_hours && (
                      <p className="text-xs text-gray-500">Avg: {t.avg_resolution_hours}h</p>
                    )}
                  </div>
                </div>
              ))}
              {techPerf.length === 0 && <p className="py-4 text-center text-sm text-gray-500">No technician data</p>}
            </div>
          </CardContent>
        </Card>
        )}
      </div>
    </div>
  );
}
