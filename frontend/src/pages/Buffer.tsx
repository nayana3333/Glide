import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/context/AuthContext";
import { api, type BufferStateResponse } from "@/lib/api";

const amountSchema = z.object({
  amount: z.string().refine((v) => Number(v) > 0, "Enter an amount greater than 0"),
});
type AmountForm = z.infer<typeof amountSchema>;

export default function Buffer() {
  const { user } = useAuth();
  const [state, setState] = useState<BufferStateResponse | null>(null);
  const form = useForm<AmountForm>({ resolver: zodResolver(amountSchema), defaultValues: { amount: "" } });

  function load() {
    if (!user) return;
    api.getBuffer(user.id).then(setState).catch((err) => {
      toast.error(err instanceof Error ? err.message : "Failed to load buffer");
    });
  }

  useEffect(load, [user]);

  async function handleAction(action: "deposit" | "withdraw", values: AmountForm) {
    const value = Number(values.amount);
    try {
      if (action === "deposit") {
        await api.deposit(value);
        toast.success(`Deposited Rs.${value.toLocaleString()}`);
      } else {
        await api.withdraw(value);
        toast.success(`Withdrew Rs.${value.toLocaleString()}`);
      }
      form.reset({ amount: "" });
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Transaction failed");
    }
  }

  if (!state) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Buffer</h1>

      <Card>
        <CardHeader>
          <CardTitle>Current balance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-4xl font-bold">Rs.{Math.round(state.balance).toLocaleString()}</div>

          <Form {...form}>
            <form className="flex items-start gap-2">
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem className="flex-1">
                    <FormControl>
                      <Input type="number" min={1} placeholder="Amount" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button
                type="button"
                disabled={form.formState.isSubmitting}
                onClick={form.handleSubmit((v) => handleAction("deposit", v))}
              >
                Deposit
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={form.formState.isSubmitting}
                onClick={form.handleSubmit((v) => handleAction("withdraw", v))}
              >
                Withdraw
              </Button>
            </form>
          </Form>

          <p className="text-xs text-muted-foreground">
            Manual deposits/withdrawals are on top of the automatic weekly save/release schedule — every
            transaction here is something you confirmed, not an automatic action.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Transaction history</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Week</TableHead>
                <TableHead>Kind</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Balance after</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {state.transactions.map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{t.week_start}</TableCell>
                  <TableCell className="capitalize">{t.kind.replaceAll("_", " ")}</TableCell>
                  <TableCell>Rs.{Math.round(t.amount).toLocaleString()}</TableCell>
                  <TableCell>Rs.{Math.round(t.balance_after).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
