"use client";

import { useEffect, useMemo, useState } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  onCreate: (payload: { name: string; category: string; language: string }) => Promise<void> | void;
};

function normalizeTemplateName(input: string) {
  return input
    .toLowerCase()
    .trim()
    .replace(/[\s-]+/g, "_")     // spaces & hyphens -> _
    .replace(/[^a-z0-9_]/g, "")  // remove invalid chars
    .replace(/_+/g, "_")         // collapse __ -> _
    .replace(/^_+|_+$/g, "");    // trim leading/trailing _
}

function validateTemplateName(name: string): string | null {
  if (!name) return "Name is required.";
  if (name.length < 3) return "Name must be at least 3 characters.";
  if (!/^[a-z]/.test(name)) return "Name must start with a letter (a-z).";
  if (!/^[a-z0-9_]+$/.test(name)) return "Only lowercase letters, numbers, and underscore (_) allowed.";
  return null;
}

export default function NewTemplateModal({ open, onClose, onCreate }: Props) {
  const [rawName, setRawName] = useState("");
  const [category, setCategory] = useState("UTILITY");
  const [language, setLanguage] = useState("en_US");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setRawName("");
    setCategory("UTILITY");
    setLanguage("en_US");
    setSubmitting(false);
    setErr(null);
  }, [open]);

  const normalizedName = useMemo(() => normalizeTemplateName(rawName), [rawName]);
  const nameError = useMemo(() => validateTemplateName(normalizedName), [normalizedName]);

  async function handleCreate() {
    setErr(null);

    const v = validateTemplateName(normalizedName);
    if (v) {
      setErr(v);
      return;
    }

    try {
      setSubmitting(true);
      await onCreate({
        name: normalizedName,
        category,
        language,
      });
      onClose();
    } catch (e: any) {
      setErr(e?.message || "Failed to create template");
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-5 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-900">New template</div>
          <button onClick={onClose} className="text-xs text-slate-500 hover:text-slate-900">
            Close
          </button>
        </div>

        {(err || nameError) && (
          <div className="mb-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
            {err || nameError}
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-700">Name</label>
            <input
              value={rawName}
              onChange={(e) => setRawName(e.target.value)}
              placeholder="e.g. onboarding_welcome_v1"
              className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-sky-500"
            />
            <div className="mt-1 text-[11px] text-slate-500">
              Will be saved as: <span className="font-mono text-slate-700">{normalizedName || "—"}</span>
            </div>
            <div className="mt-1 text-[11px] text-slate-500">
              Rules: min 3 chars, start with <span className="font-mono">a-z</span>, only{" "}
              <span className="font-mono">a-z0-9_</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-2 text-sm outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="MARKETING">Marketing</option>
                <option value="UTILITY">Utility</option>
                <option value="AUTHENTICATION">Authentication</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700">Language</label>
              <input
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder="en_US"
                className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            className="rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-700 disabled:opacity-60"
            disabled={submitting || !!nameError}
          >
            {submitting ? "Creating..." : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
