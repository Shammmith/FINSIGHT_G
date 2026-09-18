"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginUser } from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const data = await loginUser(email, password);
      login(data.access_token);
      router.push("/");
    } catch {
      setError("Invalid email or password.");
    }
  };

  return (
    <div style={{ maxWidth: 360, margin: "80px auto" }}>
      <h2>Login to FinSight</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required
          style={{ width: "100%", padding: 8, marginBottom: 8 }} />
        <input type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)} required
          style={{ width: "100%", padding: 8, marginBottom: 8 }} />
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" style={{ width: "100%", padding: 8 }}>Login</button>
      </form>
      <p style={{ marginTop: 12 }}>
        No account? <a href="/register">Register here</a>
      </p>
    </div>
  );
}