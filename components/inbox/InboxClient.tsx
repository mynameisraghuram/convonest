"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/src/lib/api";

type Conversation = {
  contact_id: number;
  contact_full_name: string;
  contact_phone: string;
  last_message_text: string;
  last_message_at: string;
  last_direction: "IN" | "OUT";
  unread_count: number;
};

type Message = {
  id: number;
  direction: "IN" | "OUT";
  status: string;
  contact: number | null;
  contact_full_name?: string;
  contact_phone: string;
  body_text: string;
  created_at: string;
  read_at?: string | null;
  delivered_at?: string | null;
  sent_at?: string | null;
  received_at?: string | null;
  msg_type?: string;
};

function safeArray(v: any) {
  return Array.isArray(v) ? v : [];
}

export default function InboxClient() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingThreads, setLoadingThreads] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const [sendText, setSendText] = useState("");
  const [sending, setSending] = useState(false);

  const [err, setErr] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  async function loadThreads() {
    setLoadingThreads(true);
    setErr(null);
    try {
      const data = await api.listInboxConversations();
      setConversations(safeArray(data));
    } catch (e: any) {
      setErr(e?.message || "Failed to fetch");
      setConversations([]);
    } finally {
      setLoadingThreads(false);
    }
  }

  async function loadMessages(contactId: number) {
    setLoadingMessages(true);
    setErr(null);
    try {
      const data = await api.listInboxMessages(contactId);
      setMessages(safeArray(data));
    } catch (e: any) {
      setErr(e?.message || "Failed to load messages");
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  }

  async function openConversation(c: Conversation) {
    setSelected(c);

    // 1) Load messages
    await loadMessages(c.contact_id);

    // 2) Mark read in backend
    try {
      await api.markConversationRead(c.contact_id);
      // update unread badge locally
      setConversations((prev) =>
        prev.map((x) => (x.contact_id === c.contact_id ? { ...x, unread_count: 0 } : x))
      );
      // also update message statuses locally if they were inbound unread
      setMessages((prev) =>
        prev.map((m) =>
          m.direction === "IN" && m.status !== "READ" ? { ...m, status: "READ" } : m
        )
      );
    } catch {
      // non-blocking
    }
  }

  async function handleSend() {
    if (!selected) return;
    const text = sendText.trim();
    if (!text) return;

    setSending(true);
    setErr(null);

    try {
      // optimistic bubble
      const tempId = Date.now();
      const optimistic: Message = {
        id: tempId,
        direction: "OUT",
        status: "QUEUED",
        contact: selected.contact_id,
        contact_phone: selected.contact_phone,
        body_text: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimistic]);
      setSendText("");

      const saved = await api.sendInboxMessage({
        contact_id: selected.contact_id,
        body_text: text,
      });

      // replace optimistic
      setMessages((prev) => prev.map((m) => (m.id === tempId ? saved : m)));

      // update thread preview
      setConversations((prev) =>
        prev.map((t) =>
          t.contact_id === selected.contact_id
            ? {
                ...t,
                last_message_text: text,
                last_message_at: new Date().toISOString(),
                last_direction: "OUT",
              }
            : t
        )
      );
    } catch (e: any) {
      setErr(e?.message || "Send failed");
    } finally {
      setSending(false);
    }
  }

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, selected?.contact_id]);

  useEffect(() => {
    loadThreads();
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-[320px_1fr] min-h-[70vh]">
        {/* Left: conversation list */}
        <div className="border-r border-slate-200">
          <div className="flex items-center justify-between p-4">
            <div>
              <div className="text-sm font-semibold text-slate-900">Inbox</div>
              <div className="text-xs text-slate-500">
                {loadingThreads ? "Loading..." : `${conversations.length} threads`}
              </div>
            </div>
            <button
              onClick={loadThreads}
              className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
            >
              Refresh
            </button>
          </div>

          {err && (
            <div className="mx-4 mb-3 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-700">
              {err}
            </div>
          )}

          <div className="max-h-[70vh] overflow-y-auto">
            {conversations.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-500">
                No conversations yet
              </div>
            ) : (
              conversations.map((c) => {
                const active = selected?.contact_id === c.contact_id;
                return (
                  <button
                    key={c.contact_id}
                    onClick={() => openConversation(c)}
                    className={`w-full text-left px-4 py-3 border-t border-slate-100 hover:bg-slate-50 ${
                      active ? "bg-sky-50" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-slate-900">
                          {c.contact_full_name || c.contact_phone}
                        </div>
                        <div className="truncate text-xs text-slate-500">
                          {c.last_message_text || "—"}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {c.unread_count > 0 && (
                          <span className="inline-flex items-center justify-center rounded-full bg-sky-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                            {c.unread_count}
                          </span>
                        )}
                        <div className="text-[10px] text-slate-400">
                          {c.last_message_at
                            ? new Date(c.last_message_at).toLocaleTimeString()
                            : ""}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right: chat */}
        <div className="flex flex-col">
          {!selected ? (
            <div className="flex flex-1 items-center justify-center text-center p-10">
              <div>
                <div className="text-base font-semibold text-slate-900">
                  Select a conversation
                </div>
                <div className="text-sm text-slate-500 mt-1">
                  Choose a contact on the left to view messages.
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="border-b border-slate-200 p-4">
                <div className="text-sm font-semibold text-slate-900">
                  {selected.contact_full_name || selected.contact_phone}
                </div>
                <div className="text-xs text-slate-500">{selected.contact_phone}</div>
              </div>

              {/* Messages */}
              <div className="flex-1 p-4 overflow-y-auto bg-slate-50">
                {loadingMessages ? (
                  <div className="text-sm text-slate-500">Loading messages…</div>
                ) : messages.length === 0 ? (
                  <div className="text-sm text-slate-500">No messages yet.</div>
                ) : (
                  <div className="space-y-2">
                    {messages.map((m) => (
                      <MessageBubble key={m.id} m={m} />
                    ))}
                    <div ref={bottomRef} />
                  </div>
                )}
              </div>

              {/* Composer */}
              <div className="border-t border-slate-200 p-3">
                <div className="flex items-end gap-2">
                  <textarea
                    value={sendText}
                    onChange={(e) => setSendText(e.target.value)}
                    rows={2}
                    placeholder="Type a message…"
                    className="flex-1 resize-none rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-200"
                  />
                  <button
                    onClick={handleSend}
                    disabled={sending || !sendText.trim()}
                    className={`rounded-md px-4 py-2 text-sm font-medium text-white ${
                      sending || !sendText.trim()
                        ? "bg-sky-300 cursor-not-allowed"
                        : "bg-sky-600 hover:bg-sky-700"
                    }`}
                  >
                    {sending ? "Sending…" : "Send"}
                  </button>
                </div>
                <div className="mt-1 text-[11px] text-slate-500">
                  Phase-1: logs OUTBOUND immediately (Meta send will come next).
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ m }: { m: Message }) {
  const inbound = m.direction === "IN";
  return (
    <div className={`flex ${inbound ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm shadow-sm border ${
          inbound
            ? "bg-white border-slate-200 text-slate-800"
            : "bg-sky-600 border-sky-600 text-white"
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{m.body_text || "—"}</div>
        <div className={`mt-1 flex items-center gap-2 text-[10px] ${inbound ? "text-slate-400" : "text-sky-100"}`}>
          <span>{m.created_at ? new Date(m.created_at).toLocaleTimeString() : ""}</span>
          {!inbound && <StatusDot status={m.status} />}
          {inbound && m.status === "READ" && <span className="text-slate-500">read</span>}
        </div>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  // dots: queued/sent/delivered/read/failed
  const s = (status || "").toUpperCase();
  let cls = "bg-slate-300";
  if (s === "QUEUED") cls = "bg-slate-300";
  else if (s === "SENT") cls = "bg-sky-200";
  else if (s === "DELIVERED") cls = "bg-sky-300";
  else if (s === "READ") cls = "bg-emerald-300";
  else if (s === "FAILED") cls = "bg-rose-300";
  else if (s === "RECEIVED") cls = "bg-slate-300";

  return (
    <span className="inline-flex items-center gap-1">
      <span className={`h-2 w-2 rounded-full ${cls}`} />
      <span className="uppercase">{s.toLowerCase()}</span>
    </span>
  );
}
