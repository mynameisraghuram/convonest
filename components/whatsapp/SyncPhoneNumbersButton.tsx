"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../src/lib/api";

export default function SyncPhoneNumbersButton({ wabaDbId }: { wabaDbId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleSync() {
    setLoading(true);
    try {
      await api.syncPhoneNumbersForWaba(wabaDbId);
      router.refresh();
    } catch (e: any) {
      alert(e?.message || "Phone sync failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      disabled={loading}
      onClick={handleSync}
      className={`px-2 py-1 rounded text-xs ${
        loading
          ? "bg-slate-700 text-slate-300 cursor-not-allowed"
          : "bg-emerald-600 hover:bg-emerald-500 text-white"
      }`}
    >
      {loading ? "Syncing..." : "Sync Phone Numbers"}
    </button>
  );
}
