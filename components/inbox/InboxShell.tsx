// frontend/components/inbox/InboxShell.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/src/lib/api";
import ConversationsList from "./ConversationsList";
import ChatPanel from "./ChatPanel";

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
  msg_type: string;
  status: string;
  contact: number | null;
  contact_full_name?: string;
  contact_phone: string;
  body_text: string;
  created_at: string;
};

type ContactHit = {
  id: number;
  full_name: string;
  phone: string;
};

type ConvHeader = {
  contact_id: number;
  contact_full_name: string;
  contact_phone: string;
};

function safeArray(v: any): any[] {
  if (Array.isArray(v)) return v;
  if (v && Array.isArray(v.results)) return v.results;
  return [];
}

function nowIso() {
  return new Date().toISOString();
}

export default function InboxShell({
  initialContactId,
}: {
  initialContactId?: string;
}) {
  const router = useRouter();

  // ----------------------------
  // Inbox search (global)
  // ----------------------------
  const [q, setQ] = useState("");
  const [contactHits, setContactHits] = useState<ContactHit[]>([]);
  const [loadingHits, setLoadingHits] = useState(false);

  // ----------------------------
  // Conversations (left)
  // ----------------------------
  const [convsRaw, setConvsRaw] = useState<any>([]);
  const [loadingConvs, setLoadingConvs] = useState(false);
  const [errConvs, setErrConvs] = useState<string | null>(null);

  const conversations: Conversation[] = useMemo(
    () => safeArray(convsRaw) as Conversation[],
    [convsRaw]
  );

  const [selectedId, setSelectedId] = useState<number | null>(() => {
    const n = initialContactId ? Number(initialContactId) : NaN;
    return Number.isFinite(n) ? n : null;
  });

  async function loadConversations() {
    setLoadingConvs(true);
    setErrConvs(null);
    try {
      const res = await api.listInboxConversations(); // keep as-is (server list)
      setConvsRaw(res);
    } catch (e: any) {
      setErrConvs(e?.message || "Failed to load conversations");
      setConvsRaw([]);
    } finally {
      setLoadingConvs(false);
    }
  }

  useEffect(() => {
    loadConversations();
  }, []);

  // keep selection synced with route param
  useEffect(() => {
    if (!initialContactId) return;
    const n = Number(initialContactId);
    setSelectedId(Number.isFinite(n) ? n : null);
  }, [initialContactId]);

  const selectedConversation = useMemo(() => {
    if (!selectedId) return null;
    return conversations.find((c) => c.contact_id === selectedId) || null;
  }, [selectedId, conversations]);

  // ----------------------------
  // ✅ Fallback header (when contact has no thread yet)
  // ----------------------------
  const [fallbackConv, setFallbackConv] = useState<ConvHeader | null>(null);

  useEffect(() => {
    if (!selectedId) {
      setFallbackConv(null);
      return;
    }

    // If thread exists, we don't need fallback
    if (selectedConversation) {
      setFallbackConv(null);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const c = await api.getContact(selectedId);
        if (cancelled) return;

        setFallbackConv({
          contact_id: selectedId,
          contact_full_name: c?.full_name || "",
          contact_phone: c?.phone || "",
        });
      } catch {
        if (cancelled) return;

        // last-resort fallback to allow UI to open composer
        setFallbackConv({
          contact_id: selectedId,
          contact_full_name: "",
          contact_phone: "",
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedId, selectedConversation]);

  function handleSelect(conv: Conversation) {
    if (!conv?.contact_id) return;
    setSelectedId(conv.contact_id);
    router.push(`/inbox/${conv.contact_id}`);
  }

  function openContactChat(c: ContactHit) {
    setSelectedId(c.id);
    setFallbackConv({
      contact_id: c.id,
      contact_full_name: c.full_name || "",
      contact_phone: c.phone || "",
    });
    router.push(`/inbox/${c.id}`);
    setQ(""); // WhatsApp-like: clear search after open
    setContactHits([]);
  }

  function optimisticUpdateConversation(contactId: number, bodyText: string) {
    const ts = nowIso();

    setConvsRaw((prev: any) => {
      const list = safeArray(prev) as Conversation[];
      const idx = list.findIndex((c) => c.contact_id === contactId);

      if (idx >= 0) {
        const updated: Conversation = {
          ...list[idx],
          last_message_text: bodyText,
          last_message_at: ts,
          last_direction: "OUT",
        };
        return [updated, ...list.slice(0, idx), ...list.slice(idx + 1)];
      }

      // Create minimal thread immediately (so left list updates even if thread didn't exist)
      const header = fallbackConv;
      const fallback: Conversation = {
        contact_id: contactId,
        contact_full_name: header?.contact_full_name || "",
        contact_phone: header?.contact_phone || "",
        last_message_text: bodyText,
        last_message_at: ts,
        last_direction: "OUT",
        unread_count: 0,
      };

      return [fallback, ...list];
    });
  }

  // ----------------------------
  // Messages (right)
  // ----------------------------
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [errMsgs, setErrMsgs] = useState<string | null>(null);

  async function refreshMessages(contactId: number) {
    setLoadingMsgs(true);
    setErrMsgs(null);

    try {
      const res = await api.listInboxMessages({ contactId });
      setMessages(safeArray(res) as Message[]);

      try {
        await api.markInboxRead({ contact_id: contactId });
        await loadConversations();
      } catch {
        // ignore
      }
    } catch (e: any) {
      setErrMsgs(e?.message || "Failed to load messages");
      setMessages([]);
    } finally {
      setLoadingMsgs(false);
    }
  }

  useEffect(() => {
    if (!selectedId) {
      setMessages([]);
      setErrMsgs(null);
      return;
    }
    refreshMessages(selectedId);
  }, [selectedId]);

  async function handleSend(text: string) {
    if (!selectedId) return;

    const body_text = text.trim();
    if (!body_text) return;

    optimisticUpdateConversation(selectedId, body_text);

    try {
      await api.sendInboxMessage({
        contact_id: selectedId,
        body_text,
      });
    } finally {
      await Promise.all([refreshMessages(selectedId), loadConversations()]);
    }
  }

  // ----------------------------
  // Global Contacts Search (WhatsApp-like)
  // ----------------------------
  useEffect(() => {
    const query = q.trim();
    if (!query) {
      setContactHits([]);
      return;
    }

    const t = setTimeout(async () => {
      setLoadingHits(true);
      try {
        const res = await api.listContacts({ q: query, page: 1 });
        const hits = safeArray(res).map((c: any) => ({
          id: Number(c.id),
          full_name: c.full_name || "",
          phone: c.phone || "",
        })) as ContactHit[];

        // Remove contacts that are already visible as threads (optional polish)
        const threadIds = new Set(conversations.map((c) => c.contact_id));
        const filtered = hits.filter((h) => !threadIds.has(h.id));

        setContactHits(filtered);
      } catch {
        setContactHits([]);
      } finally {
        setLoadingHits(false);
      }
    }, 250);

    return () => clearTimeout(t);
  }, [q, conversations]);

  const chatHeaderToShow = (selectedConversation ?? fallbackConv) as any;

  return (
    <div className="h-[calc(100vh-140px)] min-h-[520px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="grid h-full grid-cols-12 overflow-hidden">
        {/* LEFT */}
        <aside className="col-span-12 min-h-0 border-b border-slate-200 md:col-span-4 md:border-b-0 md:border-r">
          <div className="flex items-center justify-between px-4 py-3">
            <div>
              <div className="text-sm font-semibold text-slate-900">Inbox</div>
              <div className="text-xs text-slate-500">
                {loadingConvs ? "Loading…" : `${conversations.length} threads`}
              </div>
            </div>

            <button
              type="button"
              onClick={loadConversations}
              className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
            >
              Refresh
            </button>
          </div>

          {errConvs && (
            <div className="mx-4 mb-2 rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-700">
              {errConvs}
            </div>
          )}

          <ConversationsList
            conversations={conversations}
            selectedId={selectedId}
            onSelect={handleSelect}
            query={q}
            setQuery={setQ}
            contactResults={contactHits}
            loadingContacts={loadingHits}
            onOpenContact={openContactChat}
          />
        </aside>

        {/* RIGHT */}
        <main className="col-span-12 min-h-0 md:col-span-8">
          <ChatPanel
            conversation={chatHeaderToShow}
            messages={messages}
            loading={loadingMsgs}
            error={errMsgs}
            onSend={handleSend}
          />
        </main>
      </div>
    </div>
  );
}
