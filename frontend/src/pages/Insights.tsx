import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/context/AuthContext";
import { api, type BufferStateResponse, type EarningsResponse } from "@/lib/api";

function computeHealthScore(earnings: EarningsResponse[], bufferBalance: number): number | null {
  if (earnings.length < 4) return null;

  const values = earnings.map((e) => e.net_earnings);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
  const cv = mean > 0 ? Math.sqrt(variance) / mean : 1;

  const bufferWeeks = mean > 0 ? bufferBalance / mean : 0;
  const bufferScore = Math.min(bufferWeeks / 4, 1) * 40;

  const stabilityScore = Math.max(0, 1 - cv / 0.5) * 30;

  const recent = earnings.slice(-12);
  const recentDipRate = recent.filter((e) => e.net_earnings < mean * 0.8).length / recent.length;
  const dipScore = (1 - recentDipRate) * 30;

  return Math.round(bufferScore + stabilityScore + dipScore);
}

export default function Insights() {
  const { user } = useAuth();
  const [earnings, setEarnings] = useState<EarningsResponse[] | null>(null);
  const [bufferState, setBufferState] = useState<BufferStateResponse | null>(null);

  useEffect(() => {
    if (!user) return;
    Promise.all([api.getEarnings(user.id), api.getBuffer(user.id)])
      .then(([e, b]) => {
        setEarnings(e);
        setBufferState(b);
      })
      .catch((err) => toast.error(err instanceof Error ? err.message : "Failed to load insights"));
  }, [user]);

  const monthly = useMemo(() => {
    if (!earnings) return [];
    const byMonth: Record<string, number> = {};
    for (const row of earnings) {
      const month = row.week_start.slice(0, 7);
      byMonth[month] = (byMonth[month] || 0) + row.net_earnings;
    }
    return Object.entries(byMonth).map(([month, total]) => ({ month, total: Math.round(total) }));
  }, [earnings]);

  const bestWeeks = useMemo(() => {
    if (!earnings) return [];
    return earnings.slice().sort((a, b) => b.net_earnings - a.net_earnings).slice(0, 5);
  }, [earnings]);

  const healthScore = useMemo(() => {
    if (!earnings || !bufferState) return null;
    return computeHealthScore(earnings, bufferState.balance);
  }, [earnings, bufferState]);

  if (!earnings || !bufferState) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-32" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-72" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Insights</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Financial health score</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-4xl font-bold">{healthScore ?? "—"}/100</div>
            <p className="text-xs text-muted-foreground">
              Project-defined heuristic (buffer coverage + income stability + recent dip frequency), not a
              credit bureau score.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Weeks tracked</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{earnings.length}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monthly earnings trend</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  color: "var(--popover-foreground)",
                }}
              />
              <Bar dataKey="total" fill="var(--primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Best earning weeks</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Week</TableHead>
                <TableHead>Platform</TableHead>
                <TableHead>Net earnings</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bestWeeks.map((w) => (
                <TableRow key={w.id}>
                  <TableCell>{w.week_start}</TableCell>
                  <TableCell>{w.platform}</TableCell>
                  <TableCell>Rs.{Math.round(w.net_earnings).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
