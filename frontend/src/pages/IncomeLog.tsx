import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/context/AuthContext";
import { api, type EarningsResponse, type Platform } from "@/lib/api";

const PLATFORMS: Platform[] = ["Ola", "Uber", "Swiggy", "Zomato", "UrbanCompany"];

const earningsSchema = z.object({
  week_start: z.string().min(1, "Required"),
  platform: z.enum(PLATFORMS as [Platform, ...Platform[]]),
  hours_worked: z.string().refine((v) => Number(v) >= 0, "Must be 0 or more"),
  trips_completed: z.string().refine((v) => Number(v) >= 0, "Must be 0 or more"),
  gross_earnings: z.string().refine((v) => Number(v) >= 0, "Must be 0 or more"),
  fuel_cost: z.string().refine((v) => Number(v) >= 0, "Must be 0 or more"),
});
type EarningsForm = z.infer<typeof earningsSchema>;

export default function IncomeLog() {
  const { user } = useAuth();
  const [earnings, setEarnings] = useState<EarningsResponse[] | null>(null);

  const form = useForm<EarningsForm>({
    resolver: zodResolver(earningsSchema),
    defaultValues: {
      week_start: "",
      platform: PLATFORMS[0],
      hours_worked: "",
      trips_completed: "",
      gross_earnings: "",
      fuel_cost: "",
    },
  });

  function load() {
    if (!user) return;
    api
      .getEarnings(user.id)
      .then((rows) => setEarnings(rows.slice().reverse()))
      .catch((err) => toast.error(err instanceof Error ? err.message : "Failed to load earnings"));
  }

  useEffect(load, [user]);

  async function onSubmit(values: EarningsForm) {
    try {
      await api.addEarnings({
        week_start: values.week_start,
        platform: values.platform,
        hours_worked: Number(values.hours_worked),
        trips_completed: Number(values.trips_completed),
        gross_earnings: Number(values.gross_earnings),
        fuel_cost: Number(values.fuel_cost),
      });
      toast.success("Week added");
      form.reset({ ...form.getValues(), week_start: "", hours_worked: "", trips_completed: "", gross_earnings: "", fuel_cost: "" });
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add earnings");
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Income Log</h1>

      <Card>
        <CardHeader>
          <CardTitle>Log a week's earnings</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <FormField
                  control={form.control}
                  name="week_start"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Week start</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="platform"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Platform</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {PLATFORMS.map((p) => (
                            <SelectItem key={p} value={p}>
                              {p}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="hours_worked"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Hours worked</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.1" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="trips_completed"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Trips completed</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="gross_earnings"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Gross earnings (Rs.)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.01" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="fuel_cost"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Fuel cost (Rs.)</FormLabel>
                      <FormControl>
                        <Input type="number" step="0.01" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? "Saving..." : "Add week"}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>History {earnings ? `(${earnings.length} weeks)` : ""}</CardTitle>
        </CardHeader>
        <CardContent>
          {!earnings ? (
            <Skeleton className="h-40" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Week</TableHead>
                  <TableHead>Platform</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Trips</TableHead>
                  <TableHead>Gross</TableHead>
                  <TableHead>Fuel</TableHead>
                  <TableHead>Net</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {earnings.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.week_start}</TableCell>
                    <TableCell>{row.platform}</TableCell>
                    <TableCell>{row.hours_worked}</TableCell>
                    <TableCell>{row.trips_completed}</TableCell>
                    <TableCell>Rs.{Math.round(row.gross_earnings).toLocaleString()}</TableCell>
                    <TableCell>Rs.{Math.round(row.fuel_cost).toLocaleString()}</TableCell>
                    <TableCell>Rs.{Math.round(row.net_earnings).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
