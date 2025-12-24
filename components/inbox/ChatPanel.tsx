// frontend/components/inbox/ChatPanel.tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Send,
  Clock,
  Check,
  CheckCheck,
  AlertTriangle,
  ChevronDown,
} from "lucide-react";

type Conversation = {
  contact_id: number;
  contact_full_name: string;
  contact_phone: string;
};

type Message = {
  id: string | number;
  direction: "IN" | "OUT";
  msg_type: string;
  status: string; // QUEUED / SENT / DELIVERED / READ (+ UI-only: SENDING / FAILED)
  contact_phone: string;
  body_text: string;
  created_at: string;
};

// UI-only fields (safe to add; doesn't affect backend)
type UiMessage = Message & {
  _optimistic?: boolean;
};

function safeArray(v: any): any[] {
  if (Array.isArray(v)) return v;
  if (v && Array.isArray(v.results)) return v.results;
  return [];
}

type ChatPanelProps = {
  conversation: Conversation | null;
  messages: any[];
  loading: boolean;
  error: string | null;
  onSend: (text: string) => Promise<void>;
};

function makeTempId() {
  return `tmp_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function StatusDot({ status }: { status?: string }) {
  const s = (status || "").toUpperCase();

  // UI-only:
  if (s === "SENDING") return <Clock size={12} className="inline-block opacity-90" />;
  if (s === "FAILED") return <AlertTriangle size={12} className="inline-block opacity-90" />;

  // Backend-ish:
  if (s === "QUEUED") return <Clock size={12} className="inline-block" />;
  if (s === "SENT") return <Check size={12} className="inline-block" />;
  if (s === "DELIVERED") return <CheckCheck size={12} className="inline-block" />;
  if (s === "READ") return <CheckCheck size={12} className="inline-block" />;

  return null;
}

export default function ChatPanel({
  conversation,
  messages,
  loading,
  error,
  onSend,
}: ChatPanelProps) {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  // Local optimistic overlay
  const [optimistic, setOptimistic] = useState<UiMessage[]>([]);

  // ✅ scroll container ref + jump button state
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [showJump, setShowJump] = useState(false);

  // ✅ new messages counter while user is scrolled up
  const [newCount, setNewCount] = useState(0);
  const atBottomRef = useRef(true);
  const prevLenRef = useRef(0);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  const serverList: Message[] = useMemo(
    () => safeArray(messages) as Message[],
    [messages]
  );

  function scrollToBottom(behavior: ScrollBehavior = "smooth") {
    bottomRef.current?.scrollIntoView({ behavior, block: "end" });
  }

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;

    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;

    const atBottom = distanceFromBottom <= 200; // threshold
    atBottomRef.current = atBottom;

    setShowJump(!atBottom);

    // If user reaches bottom manually, clear counter
    if (atBottom) {
      setNewCount(0);
    }
  }

  // Merge server + optimistic, but avoid duplicates if server refreshed
  const msgList: UiMessage[] = useMemo(() => {
    if (!conversation) return [];

    const serverIds = new Set(serverList.map((m) => String(m.id)));

    const stillRelevant = optimistic.filter((o) => {
      if (!o._optimistic) return true;
      if (o.status?.toUpperCase() === "FAILED") return true;
      if (serverIds.has(String(o.id))) return false;
      return true;
    });

    const merged = [...serverList, ...stillRelevant].sort((a, b) => {
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
      return ta - tb;
    });

    return merged;
  }, [conversation, serverList, optimistic]);

  // ✅ Auto-scroll if at bottom; otherwise count new messages
  useEffect(() => {
    const prevLen = prevLenRef.current;
    const currLen = msgList.length;

    // first run
    if (prevLen === 0) {
      prevLenRef.current = currLen;
      requestAnimationFrame(() => scrollToBottom("auto"));
      return;
    }

    // how many new items were appended
    const delta = Math.max(0, currLen - prevLen);
    prevLenRef.current = currLen;

    if (delta === 0) return;

    if (atBottomRef.current) {
      // user is at bottom -> keep them at bottom
      scrollToBottom("smooth");
      setNewCount(0);
    } else {
      // user is reading older messages -> show "new messages" count
      setNewCount((c) => c + delta);
      setShowJump(true);
    }
  }, [msgList.length]);

  // When switching conversations, clear composer + optimistic overlay + counters
  useEffect(() => {
    setText("");
    setOptimistic([]);
    setNewCount(0);
    setShowJump(false);
    atBottomRef.current = true;
    prevLenRef.current = 0;

    // snap to bottom on switch (after paint)
    requestAnimationFrame(() => scrollToBottom("auto"));
  }, [conversation?.contact_id]);

  // Optional cleanup: if server messages increased, remove non-failed optimistic
  useEffect(() => {
    setOptimistic((prev) =>
      prev.filter((m) => (m.status || "").toUpperCase() === "FAILED")
    );
  }, [serverList.length]);

  async function handleSend(customText?: string) {
    if (!conversation) return;

    const trimmed = (customText ?? text).trim();
    if (!trimmed) return;

    const tempId = makeTempId();
    const nowIso = new Date().toISOString();

    // optimistic insert immediately
    setOptimistic((prev) => [
      ...prev,
      {
        id: tempId,
        direction: "OUT",
        msg_type: "text",
        status: "SENDING",
        contact_phone: conversation.contact_phone,
        body_text: trimmed,
        created_at: nowIso,
        _optimistic: true,
      },
    ]);

    setSending(true);
    try {
      await onSend(trimmed);

      setOptimistic((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, status: "SENT" } : m))
      );

      if (!customText) setText("");

      // If user is at bottom, keep bottom. If not, don't force scroll.
      if (atBottomRef.current) {
        requestAnimationFrame(() => scrollToBottom("smooth"));
      }
    } catch (e: any) {
      setOptimistic((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, status: "FAILED" } : m))
      );
      alert(e?.message || "Send failed");
    } finally {
      setSending(false);
    }
  }

  if (!conversation) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div>
          <div className="text-sm font-semibold text-slate-900">Select a conversation</div>
          <div className="mt-1 text-xs text-slate-500">
            Choose a contact on the left to view messages.
          </div>
        </div>
      </div>
    );
  }

  const title = conversation.contact_full_name || conversation.contact_phone;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-slate-200 px-5 py-3">
        <div className="text-sm font-semibold text-slate-900 truncate">{title}</div>
        <div className="text-xs text-slate-500 font-mono truncate">{conversation.contact_phone}</div>
      </div>

      {/* Messages (✅ scroll container + jump button) */}
      <div className="relative flex-1 overflow-hidden bg-slate-50">
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="h-full overflow-y-auto p-4"
        >
          {error && (
            <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-700">
              {error}
            </div>
          )}

          {loading && msgList.length === 0 ? (
            <div className="text-xs text-slate-500">Loading…</div>
          ) : msgList.length === 0 ? (
            <div className="text-xs text-slate-500">No messages yet. Send a message to start.</div>
          ) : (
            <div className="space-y-2">
              {msgList.map((m) => {
                const inbound = m.direction === "IN";
                const statusText = (m.status || "").toUpperCase();
                const isFailed = statusText === "FAILED";
                const isOptimistic = !!(m as UiMessage)._optimistic;

                return (
                  <div
                    key={m.id}
                    className={`flex ${inbound ? "justify-start" : "justify-end"}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm shadow-sm ${
                        inbound
                          ? "bg-white border border-slate-200 text-slate-900"
                          : isFailed
                            ? "bg-rose-600 text-white"
                            : "bg-sky-600 text-white"
                      } ${isOptimistic ? "opacity-[0.97]" : ""}`}
                    >
                      <div className="whitespace-pre-wrap break-words">
                        {m.body_text || "—"}
                      </div>

                      <div
                        className={`mt-1 flex items-center gap-1 text-[10px] ${
                          inbound ? "text-slate-400" : "text-sky-100"
                        }`}
                      >
                        <span>
                          {m.created_at ? new Date(m.created_at).toLocaleString() : ""}
                        </span>

                        {!inbound && statusText ? (
                          <>
                            <span>•</span>
                            <StatusDot status={statusText} />
                            <span className="ml-0.5">{statusText}</span>

                            {isFailed ? (
                              <>
                                <span>•</span>
                                <button
                                  type="button"
                                  onClick={() => handleSend(m.body_text)}
                                  className="underline underline-offset-2"
                                >
                                  Retry
                                </button>
                              </>
                            ) : null}
                          </>
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {showJump && (
          <button
            type="button"
            onClick={() => {
              scrollToBottom("smooth");
              setNewCount(0);
              setShowJump(false);
              atBottomRef.current = true;
            }}
            className="absolute bottom-4 right-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            <ChevronDown size={16} />
            {newCount > 0 ? `${newCount} new message${newCount > 1 ? "s" : ""}` : "Jump to bottom"}
          </button>
        )}
      </div>

      {/* Composer */}
      <div className="border-t border-slate-200 bg-white p-3">
        <div className="flex items-end gap-2">
          <textarea
            rows={2}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type a message…"
            className="flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />

          <button
            type="button"
            onClick={() => handleSend()}
            disabled={sending || loading || !text.trim()}
            className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
          >
            <Send size={16} />
            {sending ? "Sending…" : "Send"}
          </button>
        </div>

        <div className="mt-1 text-[11px] text-slate-500">
          Phase 1: text only. Media / interactive coming next.
        </div>
      </div>
    </div>
  );
}
