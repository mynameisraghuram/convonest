"use client";

export default function StatusBadge({ connected }: { connected: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border ${
        connected
          ? "bg-emerald-900/20 text-emerald-300 border-emerald-800"
          : "bg-rose-900/20 text-rose-300 border-rose-800"
      }`}
    >
      {connected ? "Connected" : "Disconnected"}
    </span>
  );
}
