"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { getDashboard } from "@/services/api";
import UploadWidget from "@/components/UploadWidget";
import JobStatusPoller from "@/components/JobStatusPoller";
import ClusterView from "@/components/ClusterView";
import IncomeExpenseChart from "@/components/IncomeExpenseChart";

export default function DashboardPage() {
  const { isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);
  const [statementId, setStatementId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const handleJobStarted = (newJobId: string, newStatementId: string) => {
    setJobId(newJobId);
    setStatementId(newStatementId);
    setDashboard(null);
  };

  const handleJobDone = async () => {
    if (!statementId) return;
    const data = await getDashboard(statementId);
    setDashboard(data);
  };

  if (!isAuthenticated) return null;

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <h1>FinSight Dashboard</h1>
        <button onClick={logout}>Logout</button>
      </div>

      <UploadWidget onJobStarted={handleJobStarted} />

      {jobId && !dashboard && (
        <div style={{ marginTop: 20 }}>
          <JobStatusPoller jobId={jobId} onDone={handleJobDone} />
        </div>
      )}

      {dashboard && (
        <div style={{ marginTop: 24 }}>
          <h3>Cash Flow Summary</h3>
          <p>Income: ${dashboard.cash_flow.total_income.toFixed(2)} |
             Expense: ${dashboard.cash_flow.total_expense.toFixed(2)} |
             Net: ${dashboard.cash_flow.net_cash_flow.toFixed(2)}</p>

          <h3>Monthly Trend</h3>
          <IncomeExpenseChart monthlyTrend={dashboard.monthly_trend} />

          <h3>Spending Clusters</h3>
          <ClusterView clusters={dashboard.clusters} />
        </div>
      )}
    </div>
  );
}