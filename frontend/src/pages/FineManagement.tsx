import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldAlert,
  IndianRupee,
  Search,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Plus,
  Edit3,
  CreditCard,
  CheckCircle,
  FileText,
  Printer,
  X,
  Sparkles,
  Info
} from "lucide-react";

interface FineRule {
  id: number
  violation_type: string
  amount: number
  description?: string
}

interface PaymentItem {
  id: number
  violation_id: number
  amount: number
  payment_date: string
  transaction_id: string
  payment_method: string
  status: string
}

const VIOLATION_LABELS: { [key: string]: string } = {
  red_light_jump: "Red Light Jump",
  wrong_lane: "Wrong Lane Driving",
  overspeeding: "Overspeeding",
  no_helmet: "No Helmet",
  no_seatbelt: "No Seatbelt",
  triple_riding: "Triple Riding",
  mobile_usage: "Using Mobile",
  illegal_parking: "Illegal Parking",
  against_traffic: "Wrong Direction",
  stop_line_crossing: "Stop Line Crossing"
};

export default function FineManagement() {
  const { token, user } = useContext(AuthContext);

  // Lists
  const [rules, setRules] = useState<FineRule[]>([]);
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [totalPayments, setTotalPayments] = useState(0);
  const [loadingRules, setLoadingRules] = useState(true);
  const [loadingPayments, setLoadingPayments] = useState(true);

  // Filters
  const [searchTxn, setSearchTxn] = useState("");
  const [filterMethod, setFilterMethod] = useState("all");
  const [page, setPage] = useState(1);
  const limit = 6;

  // Edit Fine Rule Modal
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<FineRule | null>(null);
  const [editAmount, setEditAmount] = useState(0);
  const [editDesc, setEditDesc] = useState("");
  const [savingRule, setSavingRule] = useState(false);

  // Record Manual Payment Modal
  const [isPayOpen, setIsPayOpen] = useState(false);
  const [payViolId, setPayViolId] = useState("");
  const [payMethod, setPayMethod] = useState("upi");
  const [payAmount, setPayAmount] = useState("");
  const [savingPayment, setSavingPayment] = useState(false);

  // Digital Receipt Modal
  const [selectedPayment, setSelectedPayment] = useState<PaymentItem | null>(null);

  const fetchFineRules = async () => {
    setLoadingRules(true);
    try {
      const res = await fetch(`${API_BASE_URL}/fines/rules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setRules(data);
      }
    } catch (err) {
      console.warn("Using offline fallback fine rules.");
    } finally {
      setLoadingRules(false);
    }
  };

  const fetchPayments = async () => {
    setLoadingPayments(true);
    try {
      const skip = (page - 1) * limit;
      let url = `${API_BASE_URL}/fines/payments?skip=${skip}&limit=${limit}`;
      if (searchTxn) url += `&transaction_id=${searchTxn}`;
      if (filterMethod !== "all") url += `&payment_method=${filterMethod}`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPayments(data.items);
        setTotalPayments(data.total);
      }
    } catch (err) {
      console.warn("Using offline fallback payments list.");
    } finally {
      setLoadingPayments(false);
    }
  };

  useEffect(() => {
    fetchFineRules();
  }, [token]);

  useEffect(() => {
    fetchPayments();
  }, [token, page, searchTxn, filterMethod]);

  const handleEditRuleClick = (rule: FineRule) => {
    setSelectedRule(rule);
    setEditAmount(rule.amount);
    setEditDesc(rule.description || "");
    setIsEditOpen(true);
  };

  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRule) return;
    setSavingRule(true);

    try {
      const res = await fetch(`${API_BASE_URL}/fines/rules/${selectedRule.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ amount: editAmount, description: editDesc })
      });
      if (res.ok) {
        setIsEditOpen(false);
        fetchFineRules();
      }
    } catch (err) {
      // Mock local update
      setRules((prev) =>
        prev.map((r) =>
          r.id === selectedRule.id ? { ...r, amount: editAmount, description: editDesc } : r
        )
      );
      setIsEditOpen(false);
    } finally {
      setSavingRule(false);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!payViolId || !payAmount) return;
    setSavingPayment(true);

    try {
      const res = await fetch(`${API_BASE_URL}/fines/payments`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          violation_id: parseInt(payViolId),
          payment_method: payMethod,
          amount: parseFloat(payAmount)
        })
      });

      if (res.ok) {
        setIsPayOpen(false);
        setPayViolId("");
        setPayAmount("");
        fetchPayments();
      } else {
        const errData = await res.json();
        alert(errData.detail || "Payment record failure.");
      }
    } catch (err) {
      console.warn("API offline, mock logging payment locally.");
      const mockPay: PaymentItem = {
        id: Date.now(),
        violation_id: parseInt(payViolId),
        amount: parseFloat(payAmount),
        payment_date: new Date().toISOString(),
        transaction_id: `TXN-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
        payment_method: payMethod,
        status: "completed"
      };
      setPayments((prev) => [mockPay, ...prev]);
      setIsPayOpen(false);
      setPayViolId("");
      setPayAmount("");
    } finally {
      setSavingPayment(false);
    }
  };

  const totalPages = Math.ceil(totalPayments / limit);
  const isAdmin = user?.role === "admin";

  return (
    <div className="space-y-6">
      
      {/* 1. Edit Fine Rule Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="glass-card text-slate-100 max-w-sm border-slate-800 p-6">
          <DialogHeader>
            <DialogTitle className="text-xs font-bold uppercase tracking-wider text-slate-455">
              Edit Traffic Fine Policy
            </DialogTitle>
            <DialogDescription className="text-[9px] text-slate-500 font-semibold">
              Update the penalty fine amount and description rules.
            </DialogDescription>
          </DialogHeader>

          {selectedRule && (
            <form onSubmit={handleSaveRule} className="space-y-4 my-2 text-xs">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Violation Class</label>
                <Input value={VIOLATION_LABELS[selectedRule.violation_type] || selectedRule.violation_type} disabled className="h-9 text-xs" />
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-450 uppercase">Penalty Fine (INR)</label>
                <div className="relative">
                  <span className="absolute left-3 top-3 text-[10px] text-slate-400 font-bold">₹</span>
                  <Input
                    type="number"
                    value={editAmount}
                    onChange={(e) => setEditAmount(parseFloat(e.target.value))}
                    className="pl-8 h-9 text-xs"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-450 uppercase">Description Details</label>
                <textarea
                  rows={2}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-transparent p-2.5 text-xs dark:border-slate-800 dark:bg-slate-900"
                />
              </div>

              <DialogFooter className="pt-2">
                <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)} className="h-9 text-[10px]">Cancel</Button>
                <Button type="submit" disabled={savingRule} className="h-9 text-[10px]">{savingRule ? "Saving..." : "Save Rule"}</Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* 2. Record Manual Payment Dialog */}
      <Dialog open={isPayOpen} onOpenChange={setIsPayOpen}>
        <DialogContent className="glass-card text-slate-100 max-w-sm border-slate-800 p-6">
          <DialogHeader>
            <DialogTitle className="text-xs font-bold uppercase tracking-wider text-slate-455">
              Record Challan Settlement
            </DialogTitle>
            <DialogDescription className="text-[9px] text-slate-500 font-semibold">
              Log a manual cash, UPI, or card payment for a violation.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleRecordPayment} className="space-y-4 my-2 text-xs">
            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-450 uppercase">Violation Incident ID</label>
              <Input
                value={payViolId}
                onChange={(e) => setPayViolId(e.target.value)}
                placeholder="e.g. 102"
                required
                className="h-9 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-450 uppercase">Payment Method</label>
                <Select value={payMethod} onChange={(e) => setPayMethod(e.target.value)} className="h-9">
                  <option value="upi">UPI (GPay/Paytm)</option>
                  <option value="cash">Cash Settlement</option>
                  <option value="credit_card">Credit Card</option>
                  <option value="debit_card">Debit Card</option>
                </Select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-450 uppercase">Settlement Fine (₹)</label>
                <Input
                  type="number"
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                  placeholder="e.g. 2000"
                  required
                  className="h-9 text-xs"
                />
              </div>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setIsPayOpen(false)} className="h-9 text-[10px]">Cancel</Button>
              <Button type="submit" disabled={savingPayment} className="h-9 text-[10px]">{savingPayment ? "Settling..." : "Record Payment"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* 3. Interactive Digital Receipt Dialog */}
      <Dialog open={selectedPayment !== null} onOpenChange={() => setSelectedPayment(null)}>
        <DialogContent className="glass-card max-w-sm border-slate-800 p-6 text-slate-100 font-semibold text-xs">
          {selectedPayment && (
            <div className="space-y-5">
              {/* Receipt Header */}
              <div className="text-center space-y-1.5 border-b border-slate-800 pb-4">
                <div className="h-9 w-9 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto mb-1 border border-emerald-500/20">
                  <CheckCircle size={20} />
                </div>
                <h3 className="font-extrabold text-sm uppercase tracking-wider text-slate-100">Delhi Traffic Receipt</h3>
                <span className="text-[9px] text-slate-500 block uppercase">Gov-AI Enforcement Settlement</span>
              </div>

              {/* Receipt Parameters */}
              <div className="space-y-3 font-semibold">
                <div className="flex justify-between">
                  <span className="text-slate-450">Transaction ID</span>
                  <span className="font-mono text-slate-200">{selectedPayment.transaction_id}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-450">Violation ID</span>
                  <span className="text-slate-300">#{selectedPayment.violation_id}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-450">Date Settled</span>
                  <span className="text-slate-400 font-mono">{new Date(selectedPayment.payment_date).toLocaleString()}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-450">Payment Method</span>
                  <span className="text-slate-350 uppercase">{selectedPayment.payment_method.replace("_", " ")}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-450">Settlement Status</span>
                  <Badge variant="success" className="text-[8px] uppercase font-bold py-0">
                    {selectedPayment.status.toUpperCase()}
                  </Badge>
                </div>

                <div className="flex justify-between border-t border-slate-850/60 pt-3">
                  <span className="text-slate-455 font-bold text-sm">Amount Paid</span>
                  <span className="text-emerald-450 font-black text-sm">₹{selectedPayment.amount.toLocaleString()}</span>
                </div>
              </div>

              <DialogFooter className="pt-2">
                <Button onClick={() => window.print()} variant="outline" className="w-full text-[10px] font-bold h-8 flex items-center justify-center gap-1.5">
                  <Printer size={12} /> Print Receipt
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Header and Payment Logger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Fine & Rules Desk</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Audit automatic fine rules, log transaction ledger lists, and update policy tariffs.
          </p>
        </div>

        <Button
          onClick={() => setIsPayOpen(true)}
          className="text-[10px] font-bold h-9 bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20"
        >
          <Plus size={12} className="mr-1" /> Settle Fine Challan
        </Button>
      </div>

      {/* Fine Rules Policy List (Admin edits fine rules here!) */}
      <Card className="glass-card p-5 space-y-4">
        <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <ShieldAlert size={16} className="text-red-500" />
          Automatic Fine Tariffs Policy
        </CardTitle>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 text-xs font-semibold">
          {loadingRules ? (
            [1, 2, 3, 4].map((i) => (
              <div key={i} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 animate-pulse h-28 bg-slate-100 dark:bg-slate-900" />
            ))
          ) : (
            rules.map((rule) => (
              <div
                key={rule.id}
                className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/60 flex flex-col justify-between gap-3 relative group hover:shadow-md transition-shadow"
              >
                <div>
                  <div className="flex justify-between items-center">
                    <Badge variant="outline" className="bg-red-500/10 text-red-500 border-none font-bold text-[8px] py-0 px-1.5 uppercase">
                      {VIOLATION_LABELS[rule.violation_type] || rule.violation_type}
                    </Badge>
                    <span className="text-slate-800 dark:text-slate-250 font-black">₹{rule.amount}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold mt-2 leading-relaxed truncate-2-lines">
                    {rule.description || "Automatic detection penalization tariff."}
                  </p>
                </div>

                {isAdmin && (
                  <Button
                    onClick={() => handleEditRuleClick(rule)}
                    variant="ghost"
                    size="sm"
                    className="h-6 w-full text-[9px] font-bold border border-slate-200 dark:border-slate-800 hover:bg-slate-100/50 dark:hover:bg-slate-900/60 mt-1"
                  >
                    <Edit3 size={10} className="mr-1" /> Edit Tariff
                  </Button>
                )}
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Payment Settlement History Ledger */}
      <Card className="glass-card p-5 space-y-4">
        <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <CreditCard size={16} className="text-blue-500" />
          Settlement Ledger List
        </CardTitle>

        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between print:hidden">
          <div className="relative w-full sm:w-64">
            <Search size={14} className="absolute left-3 top-3 text-slate-400" />
            <Input
              value={searchTxn}
              onChange={(e) => { setSearchTxn(e.target.value); setPage(1); }}
              placeholder="Search transaction hash..."
              className="pl-9 text-xs h-9"
            />
          </div>

          <Select value={filterMethod} onChange={(e) => { setFilterMethod(e.target.value); setPage(1); }} className="h-9 w-full sm:w-44">
            <option value="all">All Methods</option>
            <option value="upi">UPI Channels</option>
            <option value="cash">Cash Settlement</option>
            <option value="credit_card">Credit Card</option>
            <option value="debit_card">Debit Card</option>
          </Select>
        </div>

        <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-2xl">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transaction Hash</TableHead>
                <TableHead>Challan ID</TableHead>
                <TableHead>Settlement Amount</TableHead>
                <TableHead>Payment Method</TableHead>
                <TableHead>Date Settled</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loadingPayments ? (
                [1, 2, 3].map((i) => (
                  <TableRow key={i} className="animate-pulse">
                    <TableCell><div className="h-4 w-28 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                    <TableCell><div className="h-4 w-12 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                    <TableCell><div className="h-4 w-16 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                    <TableCell><div className="h-4 w-16 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                    <TableCell><div className="h-4 w-24 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                    <TableCell><div className="h-7 w-16 rounded bg-slate-200 dark:bg-slate-800 ml-auto"></div></TableCell>
                  </TableRow>
                ))
              ) : payments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-slate-450 font-bold py-6">
                    No transactions settled yet.
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-slate-400 font-bold">
                      {item.transaction_id}
                    </TableCell>
                    <TableCell className="font-bold">
                      #{item.violation_id}
                    </TableCell>
                    <TableCell className="font-extrabold text-slate-800 dark:text-slate-100">
                      ₹{item.amount.toLocaleString()}
                    </TableCell>
                    <TableCell className="uppercase text-[10px]">
                      {item.payment_method.replace("_", " ")}
                    </TableCell>
                    <TableCell className="text-slate-450 text-[10px]">
                      {new Date(item.payment_date).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        onClick={() => setSelectedPayment(item)}
                        variant="ghost"
                        size="sm"
                        className="h-7 text-blue-500 bg-blue-500/5 hover:bg-blue-600 hover:text-white px-2.5 text-[9px] font-bold"
                      >
                        <FileText size={10} className="mr-1" /> View Receipt
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {!loadingPayments && totalPages > 1 && (
          <div className="p-4 flex items-center justify-between border-t border-slate-250/20">
            <span className="text-[9px] font-bold text-slate-400">
              Showing {(page - 1) * limit + 1} to {Math.min(page * limit, totalPayments)} of {totalPayments} records
            </span>
            <div className="flex gap-1 text-xs font-bold">
              <Button disabled={page === 1} variant="outline" size="sm" className="h-8 w-8 p-0" onClick={() => setPage(page - 1)}>
                <ChevronLeft size={14} />
              </Button>
              <span className="flex items-center px-3 border border-slate-200 dark:border-slate-800 rounded-lg text-[9px] bg-slate-50 dark:bg-slate-900">
                Page {page} of {totalPages}
              </span>
              <Button disabled={page === totalPages} variant="outline" size="sm" className="h-8 w-8 p-0" onClick={() => setPage(page + 1)}>
                <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
