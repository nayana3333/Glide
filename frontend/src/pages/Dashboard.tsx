import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import DipBadge from "@/components/DipBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/AuthContext";
import { api, type DashboardResponse } from "@/lib/api";

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardResponse | null>(null);

  useEffect(() => {
    if (!user) return;
    api.getDashboard(user.id).catch((err) => {
      toast.error(err instanceof Error ? err.message : "Failed to load dashboard");
    }).then((d) => d && setData(d));
  }, [user]);

  if (!data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-72" />
      </div>
    );
  }

  const chartData = data.recent_earnings.map((e) => ({
    week: e.week_start,
    earnings: Math.round(e.net_earnings),
  }));

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {data.latest_alert_message && (
        <div className="rounded-lg border bg-warning-bg px-4 py-3 text-sm text-foreground">
          {data.latest_alert_message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Buffer balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Rs.{Math.round(data.buffer_balance).toLocaleString()}</div>
          </CardContent>
        </Card>

        {data.next_week_forecast && (
          <Card>
            <CardHeader>
              <CardTitle>Next week forecast</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-2xl font-bold">
                Rs.{Math.round(data.next_week_forecast.yhat).toLocaleString()}
              </div>
              <DipBadge level={data.next_week_forecast.dip_level} />
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Recent weeks tracked</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.recent_earnings.length}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent earnings</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="week" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  color: "var(--popover-foreground)",
                }}
              />
              <Line type="monotone" dataKey="earnings" stroke="var(--primary)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
