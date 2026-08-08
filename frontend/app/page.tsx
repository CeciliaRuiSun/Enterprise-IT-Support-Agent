import { ChatPanel } from "@/components/chat-panel";
import { listConversations } from "@/lib/api";

export default async function Page() {
  const conversations = await listConversations().catch(() => []);

  return (
    <main className="mx-auto flex h-dvh w-full max-w-7xl flex-col overflow-hidden px-4 py-4 lg:px-6">
      <div className="flex min-h-0 w-full flex-1 flex-col">
        <div className="mb-4 flex flex-none items-end justify-between gap-4 px-2">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-slate-400">IT Service Desk Automation</div>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">
              A portfolio-grade enterprise support agent with knowledge retrieval, ticket workflows,
              citations, and conversation history.
            </p>
          </div>
          <div className="hidden rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300 md:block">
            Next.js 15 · FastAPI · PostgreSQL · pgvector
          </div>
        </div>
        <ChatPanel initialConversations={conversations} />
      </div>
    </main>
  );
}
