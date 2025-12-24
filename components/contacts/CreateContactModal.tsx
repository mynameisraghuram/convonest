"use client";

import { useState } from "react";
import { api } from "../../src/lib/api";

export default function CreateContactModal({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    tags: "",
  });

  async function handleSubmit() {
    if (!form.phone.trim()) {
      alert("Phone is required (E.164 format like +919876543210)");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim() || null,
        tags: form.tags
          ? form.tags.split(",").map((t) => t.trim()).filter(Boolean)
          : [],
      };

      await api.createContact(payload);
      setOpen(false);
      setForm({ full_name: "", phone: "", email: "", tags: "" });
      onCreated();
    } catch (e: any) {
      alert(e?.message || "Create failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-sky-700"
      >
        + Add contact
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-5 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">Add Contact</h3>
              <button
                onClick={() => setOpen(false)}
                className="text-slate-500 hover:text-slate-800"
                type="button"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <input
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
                placeholder="Full name (optional)"
                value={form.full_name}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              />
              <input
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
                placeholder="Phone (E.164) e.g. +919876543210"
                value={form.phone}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              />
              <input
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
                placeholder="Email (optional)"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              />
              <input
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
                placeholder="Tags (comma separated) e.g. lead, webinar"
                value={form.tags}
                onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
              />
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setOpen(false)}
                disabled={loading}
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="rounded-md bg-sky-600 px-3 py-2 text-xs font-medium text-white hover:bg-sky-700 disabled:opacity-50"
              >
                {loading ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
