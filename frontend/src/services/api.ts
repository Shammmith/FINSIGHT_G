// frontend/src/services/api.ts
import axios from "axios";

const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL });

export const uploadStatement = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(`/api/v1/statements/upload`, formData);
  return data;
};

export const triggerClustering = async (statementId: string) => {
  const { data } = await api.post("/api/v1/cluster", { statement_id: statementId });
  return data;
};

export const getJobStatus = async (jobId: string) => {
  const { data } = await api.get(`/api/v1/cluster/${jobId}/status`);
  return data;
};

// frontend/src/services/api.ts — additions
export const getDashboard = async (statementId: string) => {
  const { data } = await api.get(`/api/v1/analytics/dashboard/${statementId}`);
  return data;
};

export const registerUser = async (email: string, password: string) => {
  const { data } = await api.post("/api/v1/auth/register", { email, password });
  return data;
};

export const loginUser = async (email: string, password: string) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const { data } = await api.post("/api/v1/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  localStorage.setItem("token", data.access_token);
  api.defaults.headers.common["Authorization"] = `Bearer ${data.access_token}`;
  return data;
};

export default api;