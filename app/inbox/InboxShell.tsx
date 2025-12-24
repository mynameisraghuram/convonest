// frontend/components/inbox/InboxShell.tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/src/lib/api";
import StatusIcon from "./StatusIcon";

type Conversation = {
  contact_id: number;
  contact_full_name: string;
  contact_phone: string;
  last_message_text: string;
  last_message_at: string;
  last_direction: string;
  unread_count: number;
};

type Message = {
  id: string | number;
  direction: string;
  status: string;
  body_text: string;
  created_at: string;
  contact_id?: number;
};

function safeArray(x: any): any[] {
  if (Array.isArray(x)) return x;
  if (x && Array.isArray(x.results)) return x.results;
  return [];
}

export default function InboxShell({ initialContactId }: { initialContactId?: string }) {
  const router = useRouter();

  const [search, setSearch] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingLeft, setLoadingLeft] = useState(false);

  const [activeContactId, setActiveContactId] = useState<string | null>(initialContactId ?? null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingRight, setLoadingRight] = useState(false);

  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);

  const endRef = useRef<HTMLDivElement>(null);

  // Load conversation list
  async function loadConversations(q: string) {
    setLoadingLeft(true);
    try {
      const res = await api.listInboxConversations({ q });
      setConversations(safeArray(res));
    } finally {
      setLoadingLeft(false);
    }
  }

  // Load messages for selected contact
  async function loadMessages(contactId: string) {
    setLoadingRight(true);
    try {
      const res = await api.listInboxMessages(contactId);
      const arr = safeArray(res);
      setMessages(arr);

      // ✅ Mark as read when opened
      await api.markInboxRead(contactId);

      // Refresh conversation list to update unread badges
      await loadConversations(search);
    } finally {
      setLoadingRight(false);
    }
  }

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initial load
  useEffect(() => {
    loadConversations("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => loadConversations(search), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  // When activeContactId changes, load messages
  useEffect(() => {
    if (!activeContactId) return;
    loadMessages(activeContactId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeContactId]);

  const activeConversation = useMemo(() => {
    if (!activeContactId) return null;
    return conversations.find((c) => String(c.contact_id) === String(activeContactId)) ?? null;
  }, [activeContactId, conversations]);

  async function handleSend() {
    const text = draft.trim();
    if (!text || !activeContactId) return;

    setSending(true);

    // ✅ optimistic insert
    const tempId = `temp-${Date.now()}`;
    const optimistic: Message = {
      id: tempId,
      direction: "OUT",
      status: "QUEUED",
      body_text: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setDraft("");

    try {
      const saved = await api.sendInboxMessage(activeContactId, text);

      // Replace temp message with saved one
      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? saved : m))
      );

      // Refresh left list for last message preview
      await loadConversations(search);
    } catch (e) {
      // Mark failed
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId ? { ...m, status: "FAILED" } : m
        )
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid h-[calc(100vh-140px)] grid-cols-12 gap-4">
      {/* Left: conversations */}
      <div className="col-span-4 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="p-3 border-b border-slate-200">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search chats by name / phone..."
            className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          {loadingLeft && <p className="mt-2 text-[11px] text-slate-500">Loading…</p>}
        </div>

        <div className="divide-y divide-slate-100 overflow-y-auto h-full">
          {conversations.length === 0 ? (
            <div className="p-6 text-sm text-slate-500">No conversations yet.</div>
          ) : (
            conversations.map((c) => {
              const active = String(c.contact_id) === String(activeContactId);
              return (
                <button
                  key={c.contact_id}
                  type="button"
                  onClick={() => {
                    setActiveContactId(String(c.contact_id));
                    router.push(`/inbox/${c.contact_id}`);
                  }}
                  className={`w-full text-left px-3 py-3 hover:bg-slate-50 ${
                    active ? "bg-sky-50" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-slate-900 text-sm">
                      {c.contact_full_name || c.contact_phone}
                    </div>
                    {c.unread_count > 0 && (
                      <span className="min-w-6 rounded-full bg-sky-600 px-2 py-0.5 text-[11px] text-white text-center">
                        {c.unread_count}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate mt-1">
                    {c.last_message_text || "—"}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Right: chat */}
      <div className="col-span-8 rounded-xl border border-slate-200 bg-white shadow-sm flex flex-col overflow-hidden">
        {!activeConversation ? (
          <div className="p-8 text-slate-500">
            Select a conversation to view messages.
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="p-4 border-b border-slate-200">
              <div className="font-semibold text-slate-900">
                {activeConversation.contact_full_name || activeConversation.contact_phone}
              </div>
              <div className="text-xs text-slate-500">
                {activeConversation.contact_phone}
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-slate-50">
              {loadingRight ? (
                <div className="text-xs text-slate-500">Loading messages…</div>
              ) : messages.length === 0 ? (
                <div className="text-xs text-slate-500">No messages.</div>
              ) : (
                messages.map((m) => {
                  const outbound = m.direction === "OUT";
                  return (
                    <div
                      key={m.id}
                      className={`flex ${outbound ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm shadow-sm border ${
                          outbound
                            ? "bg-white border-slate-200"
                            : "bg-sky-50 border-sky-100"
                        }`}
                      >
                        <div className="text-slate-900">{m.body_text}</div>

                        <div className="mt-1 flex items-center justify-end gap-2 text-[11px] text-slate-500">
                          <span>
                            {m.created_at
                              ? new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                              : ""}
                          </span>
                          {outbound && <StatusIcon status={m.status} />}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}

              <div ref={endRef} />
            </div>

            {/* Composer */}
            <div className="p-3 border-t border-slate-200 bg-white">
              <div className="flex gap-2">
                <input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Type a message…"
                  className="flex-1 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={sending || !draft.trim()}
                  className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
                >
                  {sending ? "Sending…" : "Send"}
                </button>
              </div>
              <div className="mt-1 text-[11px] text-slate-500">
                Enter to send • Shift+Enter for new line
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
