"use client";

import { useState } from "react";

type Props = {
  contactId: number | null;
};

export default function MessageInput({ contactId }: Props) {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  const canSend = !!contactId && text.trim().length > 0 && !sending;

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!canSend || !contactId) return;

    try {
      setSending(true);

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ||
        "http://127.0.0.1:8000/api";

      const res = await fetch(`${apiBase}/inbox/messages/send/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contact_id: contactId,
          body_text: text.trim(),
        }),
      });

      if (!res.ok) {
        console.error("Send failed", await res.text());
      } else {
        setText("");
        // simple approach: reload to show new message
        window.location.reload();
      }
    } catch (err) {
      console.error("Error sending message", err);
    } finally {
      setSending(false);
    }
  }

  return (
    <form
      onSubmit={handleSend}
      className="flex items-center gap-2 border-t border-slate-200 px-4 py-3"
    >
      <input
        className="flex-1 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
        placeholder={
          contactId
            ? "Type a message to send on WhatsApp..."
            : "Select a conversation to start messaging..."
        }
        disabled={!contactId || sending}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button
        type="submit"
        disabled={!canSend}
        className={`rounded-md px-3 py-2 text-xs font-medium ${
          canSend
            ? "bg-sky-600 text-white hover:bg-sky-700"
            : "bg-slate-200 text-slate-400 cursor-not-allowed"
        }`}
      >
        {sending ? "Sending..." : "Send"}
      </button>
    </form>
  );
}
