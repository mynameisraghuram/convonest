"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/apiClient";

export default function DashboardPage() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.get("/accounts/ping/")
      .then((res) => setMessage(res.data.message))
      .catch(() => setMessage("Error connecting to backend"));
  }, []);

  return (
    <div style={{ padding: 40 }}>
      <h1>Dashboard</h1>
      <p>Backend says: {message}</p>
    </div>
  );
}
