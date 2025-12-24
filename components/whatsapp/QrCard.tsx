"use client";

import { useRouter } from "next/navigation";
import { api } from "../../src/lib/api";

interface QrCardProps {
  qr: any;
  onDelete?: (id: string) => void;
}

export default function QrCard({ qr, onDelete }: QrCardProps) {
  const router = useRouter();

  async function handleDelete() {
    const id = qr?.id;
    if (!id) return alert("QR id missing");
    if (!confirm("Delete this QR code?")) return;

    try {
      await api.deleteQrCode(id);
      onDelete?.(id);

      // ✅ refresh server page data immediately
      router.refresh();
    } catch (e: any) {
      alert(e?.message || "Failed to delete QR code");
    }
  }

  return (
    <div className="border border-slate-800 rounded-xl p-4 bg-slate-900/40 space-y-2">
      <p className="font-semibold text-sm">{qr?.name || "Unnamed QR"}</p>
      <p className="text-xs text-slate-400 break-all">
        {qr?.deep_link || "-"}
      </p>

      {qr?.image_url && (
        <img
          src={qr.image_url}
          alt={qr?.name || "QR"}
          className="w-28 h-28 mt-2 border border-slate-700 rounded"
        />
      )}

      <button
        type="button"
        onClick={handleDelete}
        className="text-xs text-red-400 hover:underline"
      >
        Delete
      </button>
    </div>
  );
}
