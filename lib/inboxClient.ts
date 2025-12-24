const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

export type Conversation = {
  contact_id: number;
  contact_full_name: string;
  contact_phone: string;
  last_message_text: string;
  last_message_at: string;
  last_direction: "IN" | "OUT";
  unread_count: number;
};

export type Message = {
  id: number;
  direction: "IN" | "OUT";
  msg_type: string;
  status: string;
  contact: number | null;
  contact_full_name: string | null;
  contact_phone: string;
  body_text: string;
  created_at: string;
};

export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE}/inbox/conversations/`, {
    credentials: "include",
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load conversations: ${res.status}`);
  }
  return res.json();
}

export async function getMessages(contactId: number): Promise<Message[]> {
  const res = await fetch(
    `${API_BASE}/inbox/messages/?contact=${contactId}`,
    {
      credentials: "include",
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new Error(`Failed to load messages: ${res.status}`);
  }
  return res.json();
}
