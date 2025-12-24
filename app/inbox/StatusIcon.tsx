// frontend/components/inbox/StatusIcon.tsx
"use client";

import { Check, CheckCheck, Clock } from "lucide-react";

export default function StatusIcon({ status }: { status: string }) {
  // QUEUED | SENT | DELIVERED | READ | FAILED | RECEIVED
  if (status === "QUEUED") return <Clock size={14} className="text-slate-400" />;
  if (status === "SENT") return <Check size={14} className="text-slate-500" />;
  if (status === "DELIVERED") return <CheckCheck size={14} className="text-slate-500" />;
  if (status === "READ") return <CheckCheck size={14} className="text-sky-600" />;
  if (status === "FAILED") return <span className="text-red-600 text-xs">!</span>;
  return null;
}
