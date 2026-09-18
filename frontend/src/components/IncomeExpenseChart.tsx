import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function IncomeExpenseChart({ monthlyTrend }: { monthlyTrend: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={monthlyTrend}>
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="income" fill="#22c55e" name="Income" />
        <Bar dataKey="expense" fill="#ef4444" name="Expense" />
      </BarChart>
    </ResponsiveContainer>
  );
}