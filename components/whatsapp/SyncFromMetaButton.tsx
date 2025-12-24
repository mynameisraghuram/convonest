"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../src/lib/api";

export default function SyncFromMetaButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleSync() {
    setLoading(true);
    try {
      await api.syncWabasFromMeta();
      router.refresh();
    } catch (e: any) {
      alert(e?.message || "Sync failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      disabled={loading}
      onClick={handleSync}
      className={`px-3 py-2 rounded text-sm ${
        loading
          ? "bg-slate-700 text-slate-300 cursor-not-allowed"
          : "bg-sky-600 hover:bg-sky-500 text-white"
      }`}
    >
      {loading ? "Syncing..." : "Sync from Meta"}
    </button>
  );
}
