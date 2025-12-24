// frontend/components/contacts/ContactsClient.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquareText } from "lucide-react";

import { api } from "../../src/lib/api";
import CreateContactModal from "./CreateContactModal";

type Contact = {
  id: string;
  full_name: string;
  phone: string;
  email?: string | null;
  tags?: string[];
  last_seen_at?: string | null;
  is_opted_out?: boolean;
  is_blocked?: boolean;
};

function toResultsArray(data: any): any[] {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

export default function ContactsClient() {
  const router = useRouter();

  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const contacts: Contact[] = useMemo(() => toResultsArray(data), [data]);
  const count: number = data?.count ?? contacts.length ?? 0;

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const res = await api.listContacts({ q, page });
      setData(res);
    } catch (e: any) {
      setErr(e?.message || "Failed to load contacts");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => {
      setPage(1);
      load();
    }, 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  async function handleExport() {
    try {
      await api.exportContactsCsv();
    } catch (e: any) {
      alert(e?.message || "Export failed");
    }
  }

  async function handleImport(file: File) {
    try {
      await api.importContactsCsv(file);
      await load();
      alert("Imported successfully");
    } catch (e: any) {
      alert(e?.message || "Import failed");
    }
  }

  const totalPages = Math.max(1, Math.ceil(count / 20));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-xl font-semibold text-slate-900">Contacts</h1>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExport}
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Export CSV
          </button>

          <label className="cursor-pointer rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50">
            Import CSV
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleImport(f);
                e.currentTarget.value = "";
              }}
            />
          </label>

          {/* ✅ Correct: modal provides its own button */}
          <CreateContactModal onCreated={load} />
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between gap-2">
          <input
            className="w-full max-w-xs rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
            placeholder="Search by name, phone, email..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />

          <div className="text-xs text-slate-500">
            {loading ? "Loading..." : `${count} contacts`}
          </div>
        </div>

        {err && (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-700">
            {err}
          </div>
        )}

        <div className="overflow-hidden rounded-md border border-slate-200">
          <table className="min-w-full border-collapse text-xs">
            <thead className="bg-slate-50">
              <tr className="text-left text-slate-500">
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Phone</th>
                <th className="px-3 py-2 font-medium">Tags</th>
                <th className="px-3 py-2 font-medium">Last seen</th>
                <th className="px-3 py-2 font-medium text-right">Action</th>
              </tr>
            </thead>

            <tbody>
              {contacts.length === 0 && !loading ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-3 py-6 text-center text-slate-400"
                  >
                    No contacts yet. Add one manually or import from CSV.
                  </td>
                </tr>
              ) : (
                contacts.map((c) => (
                  <tr
                    key={c.id}
                    className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                    onClick={() => router.push(`/inbox/${c.id}`)}
                    title="Open chat"
                  >
                    <td className="px-3 py-2">
                      <div className="font-medium text-slate-900">
                        {c.full_name || "—"}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {c.email || ""}
                      </div>
                    </td>

                    <td className="px-3 py-2 font-mono text-slate-700">
                      {c.phone}
                      {(c.is_blocked || c.is_opted_out) && (
                        <span className="ml-2 text-[11px] text-rose-600">
                          {c.is_blocked ? "Blocked" : "Opted-out"}
                        </span>
                      )}
                    </td>

                    <td className="px-3 py-2 text-slate-600">
                      {(c.tags || []).slice(0, 3).join(", ")}
                      {(c.tags || []).length > 3 ? "…" : ""}
                    </td>

                    <td className="px-3 py-2 text-slate-600">
                      {c.last_seen_at
                        ? new Date(c.last_seen_at).toLocaleString()
                        : "—"}
                    </td>

                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/inbox/${c.id}`);
                        }}
                        className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-700 hover:bg-slate-50"
                      >
                        <MessageSquareText size={14} />
                        Message
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="mt-3 flex items-center justify-between">
          <button
            type="button"
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </button>

          <div className="text-xs text-slate-500">
            Page {page} / {totalPages}
          </div>

          <button
            type="button"
            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
