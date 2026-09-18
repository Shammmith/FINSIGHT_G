// frontend/src/app/register/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { registerUser } from "@/services/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await registerUser(email, password);
      setSuccess(true);
      setTimeout(() => router.push("/login"), 1200);
    } catch {
      setError("Registration failed — email may already be in use.");
    }
  };

  return (
    <div style={{ maxWidth: 360, margin: "80px auto" }}>
      <h2>Create your FinSight account</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required
          style={{ width: "100%", padding: 8, marginBottom: 8 }} />
        <input type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)} required
          style={{ width: "100%", padding: 8, marginBottom: 8 }} />
        {error && <p style={{ color: "red" }}>{error}</p>}
        {success && <p style={{ color: "green" }}>Registered! Redirecting to login...</p>}
        <button type="submit" style={{ width: "100%", padding: 8 }}>Register</button>
      </form>
    </div>
  );
}