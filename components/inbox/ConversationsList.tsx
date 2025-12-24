"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  MessageCircle,
  ArrowDownLeft,
  ArrowUpRight,
  Search,
  MessageSquarePlus,
} from "lucide-react";

type Conversation = {
  contact_id: number;
  contact_full_name: string;
  contact_phone: string;
  last_message_text: string;
  last_message_at: string;
  last_direction: "IN" | "OUT";
  unread_count: number;
};

type ContactHit = {
  id: number;
  full_name: string;
  phone: string;
};

type Row =
  | { type: "thread"; data: Conversation }
  | { type: "contact"; data: ContactHit }
  | { type: "cta" };

function formatWhen(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfThatDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());

  const dayDiff = Math.round(
    (startOfToday.getTime() - startOfThatDay.getTime()) /
      (1000 * 60 * 60 * 24)
  );

  if (dayDiff === 0) {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  if (dayDiff === 1) return "Yesterday";
  return d.toLocaleDateString([], { day: "2-digit", month: "short" });
}

export default function ConversationsList({
  conversations,
  selectedId,
  onSelect,
  query,
  setQuery,
  contactResults,
  loadingContacts,
  onOpenContact,
}: {
  conversations: Conversation[];
  selectedId: number | null;
  onSelect: (c: Conversation) => void;

  query: string;
  setQuery: (v: string) => void;

  contactResults: ContactHit[];
  loadingContacts: boolean;
  onOpenContact: (c: ContactHit) => void;
}) {
  const listRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const [activeIndex, setActiveIndex] = useState<number>(-1);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();

    const sorted = [...conversations].sort((a, b) => {
      const ta = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
      const tb = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
      if (tb !== ta) return tb - ta;

      const na = (a.contact_full_name || a.contact_phone || "").toLowerCase();
      const nb = (b.contact_full_name || b.contact_phone || "").toLowerCase();
      return na.localeCompare(nb);
    });

    if (!needle) return sorted;

    return sorted.filter((c) => {
      const name = (c.contact_full_name || "").toLowerCase();
      const phone = (c.contact_phone || "").toLowerCase();
      const last = (c.last_message_text || "").toLowerCase();
      return name.includes(needle) || phone.includes(needle) || last.includes(needle);
    });
  }, [conversations, query]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: 0 });
  }, [conversations.length]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: 0 });
  }, [query]);

  const showContactsSection = query.trim().length > 0;
  const showStartNewChatCTA =
    query.trim().length > 0 &&
    filtered.length === 0 &&
    contactResults.length === 0 &&
    !loadingContacts;

  const rows: Row[] = useMemo(() => {
    const r: Row[] = [];
    filtered.forEach((c) => r.push({ type: "thread", data: c }));
    contactResults.forEach((c) => r.push({ type: "contact", data: c }));
    if (showStartNewChatCTA) r.push({ type: "cta" });
    return r;
  }, [filtered, contactResults, showStartNewChatCTA]);

  useEffect(() => {
    setActiveIndex(rows.length > 0 ? 0 : -1);
  }, [rows.length]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!rows.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, rows.length - 1));
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    }

    if (e.key === "Enter") {
      e.preventDefault();
      const row = rows[activeIndex];
      if (!row) return;

      if (row.type === "thread") onSelect(row.data);
      if (row.type === "contact") onOpenContact(row.data);
      if (row.type === "cta") {
        onOpenContact({
          id: Date.now(),
          full_name: query.trim(),
          phone: query.trim(),
        });
      }
    }
  }

  useEffect(() => {
    const el = listRef.current?.children[activeIndex] as HTMLElement | undefined;
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  return (
    <div className="h-[calc(100%-56px)] overflow-hidden">
      {/* Search */}
      <div className="sticky top-0 z-10 bg-white px-3 py-2">
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2 py-1.5">
          <Search size={16} className="text-slate-400" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search chats or contacts…"
            className="w-full bg-transparent text-sm outline-none"
            autoFocus
          />
        </div>
      </div>

      {/* Scrollable list */}
      <div ref={listRef} className="h-[calc(100%-52px)] overflow-y-scroll">
        {/* THREADS */}
        {filtered.map((c, i) => {
          const active = i === activeIndex;
          const name = c.contact_full_name || c.contact_phone || "Unknown";
          const preview = c.last_message_text || "—";
          const when = formatWhen(c.last_message_at);

          return (
            <button
              key={c.contact_id}
              onClick={() => onSelect(c)}
              className={`w-full px-4 py-3 text-left ${
                active ? "bg-sky-100" : "hover:bg-slate-50"
              }`}
            >
              <div className="flex justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{name}</div>
                  <div className="truncate text-xs text-slate-500">{preview}</div>
                </div>
                <div className="shrink-0 text-[10px] text-slate-400">{when}</div>
              </div>
            </button>
          );
        })}

        {/* CONTACTS */}
        {showContactsSection &&
          contactResults.map((c, i) => {
            const idx = filtered.length + i;
            const active = idx === activeIndex;

            return (
              <button
                key={c.id}
                onClick={() => onOpenContact(c)}
                className={`w-full px-4 py-3 text-left ${
                  active ? "bg-sky-100" : "hover:bg-slate-50"
                }`}
              >
                <div className="truncate text-sm font-medium text-slate-900">
                  {c.full_name || c.phone}
                </div>
                <div className="truncate text-xs text-slate-500">{c.phone}</div>
              </button>
            );
          })}

        {/* START NEW CHAT CTA (taller like WhatsApp) */}
        {showStartNewChatCTA && (
          <button
            onClick={() =>
              onOpenContact({
                id: Date.now(),
                full_name: query.trim(),
                phone: query.trim(),
              })
            }
            className={[
              "w-full border-t border-slate-200",
              "min-h-[260px] py-10 px-6",
              "flex flex-col items-center justify-center text-center",
              activeIndex === rows.length - 1 ? "bg-sky-100" : "hover:bg-slate-50",
            ].join(" ")}
          >
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white">
              <MessageSquarePlus size={18} className="text-slate-500" />
            </div>

            <div className="text-sm font-medium text-slate-800">
              No chats or contacts found
            </div>

            <div className="mt-4">
              <span className="inline-flex items-center rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-sky-700">
                Start new chat with “{query.trim()}”
              </span>
            </div>

            <div className="mt-3 text-xs text-slate-500">
              You can save this contact later
            </div>
          </button>
        )}
      </div>
    </div>
  );
}
