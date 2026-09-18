// frontend/src/components/JobStatusPoller.tsx
import { useEffect, useState } from "react";
import { getJobStatus } from "@/services/api";

export default function JobStatusPoller({ jobId, onDone }: { jobId: string; onDone: () => void }) {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      const data = await getJobStatus(jobId);
      setStatus(data);
      if (data.status === "DONE" || data.status === "FAILED") clearInterval(interval); if (data.status === "DONE") onDone();
    }, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  if (!status) return <p>Loading job status...</p>;
  return (
    <div>
      <p>Status: {status.status}</p>
      {status.status === "DONE" && (
        <p>Optimal clusters found: {status.k_optimal} (silhouette: {status.silhouette?.toFixed(2)})</p>
      )}
      {status.status === "FAILED" && <p style={{ color: "red" }}>Error: {status.error_message}</p>}
    </div>
  );
}