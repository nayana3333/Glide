import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import DipBadge from "@/components/DipBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/context/AuthContext";
import { api, type ExplainResponse, type ForecastResponse } from "@/lib/api";

export default function Forecast() {
  const { user } = useAuth();
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [explainError, setExplainError] = useState("");

  useEffect(() => {
    if (!user) return;
    api.getForecast(user.id).then(setForecast).catch((err) => {
      toast.error(err instanceof Error ? err.message : "Failed to load forecast");
    });
    api.getExplanation(user.id).then(setExplanation).catch((err) => {
      setExplainError(err instanceof Error ? err.message : "Could not generate explanation");
    });
  }, [user]);

  if (!forecast) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-72" />
        <Skeleton className="h-56" />
      </div>
    );
  }

  const chartData = forecast.forecast.map((w) => ({
    week: w.week_start,
    predicted: Math.round(w.yhat),
    lower: w.yhat_lower != null ? Math.round(w.yhat_lower) : null,
    upper: w.yhat_upper != null ? Math.round(w.yhat_upper) : null,
  }));

  const contributions = explanation
    ? Object.entries(explanation.contributions).sort((a, b) => a[1] - b[1])
    : [];
  const maxAbs = Math.max(1, ...contributions.map(([, v]) => Math.abs(v)));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Forecast</h1>
        <p className="text-sm text-muted-foreground">
          Model: {forecast.model_used} · Rolling average: Rs.{Math.round(forecast.rolling_avg).toLocaleString()}
        </p>
      </div>

      <Card>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
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
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="predicted" name="Predicted" stroke="var(--primary)" strokeWidth={2} />
              <Line
                type="monotone"
                dataKey="upper"
                name="Upper (80%)"
                stroke="var(--muted-foreground)"
                strokeDasharray="4 4"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="lower"
                name="Lower (80%)"
                stroke="var(--muted-foreground)"
                strokeDasharray="4 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Week-by-week</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Week</TableHead>
                <TableHead>Predicted</TableHead>
                <TableHead>Range</TableHead>
                <TableHead>Alert</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {forecast.forecast.map((w) => (
                <TableRow key={w.week_start}>
                  <TableCell>{w.week_start}</TableCell>
                  <TableCell>Rs.{Math.round(w.yhat).toLocaleString()}</TableCell>
                  <TableCell>
                    {w.yhat_lower != null
                      ? `Rs.${Math.round(w.yhat_lower).toLocaleString()} – Rs.${Math.round(w.yhat_upper!).toLocaleString()}`
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <DipBadge level={w.dip_level} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Why this forecast (SHAP)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {explainError && <p className="text-xs text-muted-foreground">{explainError}</p>}
          {explanation && (
            <>
              <p className="text-sm text-muted-foreground">
                Predicted Rs.{Math.round(explanation.predicted).toLocaleString()} vs recent 4-week average
                Rs.{Math.round(explanation.rolling_avg_4wk).toLocaleString()}
              </p>
              <div className="space-y-2">
                {contributions.map(([label, value]) => (
                  <div key={label} className="grid grid-cols-[140px_1fr_90px] items-center gap-3 text-sm sm:grid-cols-[160px_1fr_90px]">
                    <span className="truncate text-muted-foreground">{label}</span>
                    <div className="h-2.5 overflow-hidden rounded bg-muted">
                      <div
                        className={value < 0 ? "h-full bg-destructive" : "h-full bg-success"}
                        style={{ width: `${(Math.abs(value) / maxAbs) * 100}%` }}
                      />
                    </div>
                    <span className="text-right tabular-nums">
                      {value < 0 ? "-" : "+"}Rs.{Math.round(Math.abs(value)).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
          {!explanation && !explainError && <Skeleton className="h-24" />}
        </CardContent>
      </Card>
    </div>
  );
}
