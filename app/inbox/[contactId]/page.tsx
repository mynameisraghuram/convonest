import InboxShell from "@/components/inbox/InboxShell";

export default async function InboxContactPage({
  params,
}: {
  params: Promise<{ contactId: string }>;
}) {
  const { contactId } = await params;
  return <InboxShell initialContactId={contactId} />;
}
