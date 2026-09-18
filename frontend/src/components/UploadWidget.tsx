// frontend/src/components/UploadWidget.tsx
"use client";
import { useState } from "react";
import { uploadStatement, triggerClustering } from "@/services/api";

export default function UploadWidget({ onJobStarted }: { onJobStarted: (jobId: string, statementId: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const uploadRes = await uploadStatement(file);
      const jobRes = await triggerClustering(uploadRes.statement_id);
      onJobStarted(jobRes.job_id, uploadRes.statement_id);
    } catch {
      setError("Upload failed. Check file format (CSV/PDF only) and try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ border: "2px dashed #ccc", padding: 20, borderRadius: 8 }}>
      <input type="file" accept=".csv,.pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <button onClick={handleUpload} disabled={!file || uploading} style={{ marginLeft: 12 }}>
        {uploading ? "Uploading..." : "Upload & Analyze"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}