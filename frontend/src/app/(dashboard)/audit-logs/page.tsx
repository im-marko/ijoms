'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { AuditLog, PaginatedResponse } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Search } from 'lucide-react';

const ACTION_COLORS: Record<string, string> = {
  create: 'bg-green-100 text-green-700',
  update: 'bg-blue-100 text-blue-700',
  delete: 'bg-red-100 text-red-700',
  status_change: 'bg-purple-100 text-purple-700',
  assignment: 'bg-yellow-100 text-yellow-700',
  escalation: 'bg-orange-100 text-orange-700',
  login: 'bg-gray-100 text-gray-700',
};

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [entityFilter, setEntityFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchLogs = async () => {
    const params: any = { page, search };
    if (actionFilter !== 'all') params.action = actionFilter;
    if (entityFilter) params.entity_type = entityFilter;
    if (startDate) params.start_date = new Date(startDate).toISOString();
    if (endDate) params.end_date = new Date(endDate).toISOString();
    try {
      const res = await api.get<PaginatedResponse<AuditLog>>('/audit-logs/', { params });
      setLogs(res.data.results);
      setTotal(res.data.count);
    } catch {}
  };

  useEffect(() => { fetchLogs(); }, [page, actionFilter]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-wrap items-end gap-4 pt-6">
          <div className="space-y-1">
            <label className="text-xs text-gray-500">Search</label>
            <div className="flex gap-2">
              <Input placeholder="Entity, user..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-48" onKeyDown={(e) => e.key === 'Enter' && fetchLogs()} />
              <Button variant="outline" size="sm" onClick={fetchLogs}><Search className="h-4 w-4" /></Button>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-500">Action</label>
            <Select value={actionFilter} onValueChange={(v) => { if (v) { setActionFilter(v); setPage(1); } }}>
              <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="create">Create</SelectItem>
                <SelectItem value="update">Update</SelectItem>
                <SelectItem value="delete">Delete</SelectItem>
                <SelectItem value="status_change">Status Change</SelectItem>
                <SelectItem value="assignment">Assignment</SelectItem>
                <SelectItem value="escalation">Escalation</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-500">Entity Type</label>
            <Input placeholder="e.g. Job" value={entityFilter} onChange={(e) => setEntityFilter(e.target.value)} className="w-32" />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-500">From</label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-36" />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-gray-500">To</label>
            <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-36" />
          </div>
          <Button onClick={fetchLogs}>Apply</Button>
          <span className="text-sm text-gray-500">{total} entries</span>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Entity ID</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Changes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-xs">{new Date(log.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-sm">
                    {log.user_detail ? `${log.user_detail.first_name} ${log.user_detail.last_name}` : 'System'}
                  </TableCell>
                  <TableCell>
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${ACTION_COLORS[log.action] || 'bg-gray-100'}`}>
                      {log.action}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm">{log.entity_type}</TableCell>
                  <TableCell className="font-mono text-xs">{log.entity_id || '-'}</TableCell>
                  <TableCell className="text-xs text-gray-500">{log.ip_address || '-'}</TableCell>
                  <TableCell className="max-w-xs truncate text-xs text-gray-500">
                    {Object.keys(log.changes).length > 0 ? JSON.stringify(log.changes).slice(0, 80) : '-'}
                  </TableCell>
                </TableRow>
              ))}
              {logs.length === 0 && (
                <TableRow><TableCell colSpan={7} className="py-8 text-center text-gray-500">No audit logs found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="text-sm text-gray-500">Page {page} of {Math.ceil(total / 20)}</span>
          <Button variant="outline" size="sm" disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
