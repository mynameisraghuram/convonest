"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../src/lib/api";

interface CreateQrModalProps {
  wabas: any;
  numbers: any;
}

function toArray(value: any): any[] {
  if (Array.isArray(value)) return value;
  if (value && Array.isArray(value.results)) return value.results;
  return [];
}

export default function CreateQrModal({ wabas, numbers }: CreateQrModalProps) {
  const router = useRouter();
  const wabaList = useMemo(() => toArray(wabas), [wabas]);
  const numberList = useMemo(() => toArray(numbers), [numbers]);

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    waba_id: "",
    phone_number_id: "",
    name: "",
    message: "",
  });
  const [loading, setLoading] = useState(false);

  const canSubmit =
    !!form.waba_id && !!form.phone_number_id && !!form.name && !loading;

  async function handleCreate() {
    if (!form.waba_id || !form.phone_number_id || !form.name) {
      alert("Select WABA, phone number and name");
      return;
    }

    setLoading(true);
    try {
      await api.createQrCode(form);

      setOpen(false);
      setForm({ waba_id: "", phone_number_id: "", name: "", message: "" });

      // ✅ Refresh server data so QR list updates immediately
      router.refresh();
    } catch (e: any) {
      alert(e?.message || "Failed to create QR code");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-sm"
      >
        + Create QR Code
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md space-y-3">
            <h3 className="text-lg font-semibold">Create WhatsApp QR</h3>

            <select
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-2 text-sm"
              value={form.waba_id}
              onChange={(e) =>
                setForm((f) => ({ ...f, waba_id: e.target.value }))
              }
            >
              <option value="">Select Business Account</option>
              {wabaList.map((w: any) => (
                <option key={w.id} value={w.id}>
                  {w.name || w.id}
                </option>
              ))}
            </select>

            <select
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-2 text-sm"
              value={form.phone_number_id}
              onChange={(e) =>
                setForm((f) => ({ ...f, phone_number_id: e.target.value }))
              }
            >
              <option value="">Select Phone Number</option>
              {numberList.map((n: any) => (
                <option key={n.id} value={n.id}>
                  {n.display_name || n.id}{" "}
                  {n.e164_number ? `(${n.e164_number})` : ""}
                </option>
              ))}
            </select>

            <input
              placeholder="Label / Name"
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-2 text-sm"
              value={form.name}
              onChange={(e) =>
                setForm((f) => ({ ...f, name: e.target.value }))
              }
            />

            <input
              placeholder="Default message (optional)"
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-2 text-sm"
              value={form.message}
              onChange={(e) =>
                setForm((f) => ({ ...f, message: e.target.value }))
              }
            />

            <div className="flex justify-between gap-2 pt-2">
              <button
                type="button"
                disabled={!canSubmit}
                onClick={handleCreate}
                className={`px-3 py-2 rounded text-sm ${
                  canSubmit
                    ? "bg-emerald-600 hover:bg-emerald-500"
                    : "bg-emerald-900/40 text-slate-400 cursor-not-allowed"
                }`}
              >
                {loading ? "Creating..." : "Create"}
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => setOpen(false)}
                className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm"
              >
                Cancel
              </button>
            </div>

            {(wabaList.length === 0 || numberList.length === 0) && (
              <p className="text-xs text-slate-400">
                Missing data: make sure WABAs and phone numbers are synced in
                backend.
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
