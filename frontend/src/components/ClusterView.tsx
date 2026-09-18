export default function ClusterView({ clusters }: { clusters: any[] }) {
  return (
    <div style={{ display: "grid", gap: "12px" }}>
      {clusters.map((c) => (
        <div key={c.cluster_id} style={{ border: "1px solid #ddd", padding: "12px", borderRadius: "8px" }}>
          <strong>Cluster {c.cluster_label}</strong> — {c.txn_count} transactions, ${c.total_amount.toFixed(2)}
          <div style={{ marginTop: "4px" }}>
            {c.keywords.map((k: string) => (
              <span key={k} style={{ background: "#f0f0f0", padding: "2px 8px", borderRadius: "12px", marginRight: "4px", fontSize: "12px" }}>
                {k}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}