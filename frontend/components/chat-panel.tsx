"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { createConversation, getConversation, listConversations, sendMessage } from "@/lib/api";
import type { ConversationHistory, ConversationListItem, MessageItem } from "@/types";

type Props = {
  initialConversations: ConversationListItem[];
};

function getLatestConversation(conversations: ConversationListItem[]) {
  return conversations.reduce<ConversationListItem | null>((latest, conversation) => {
    if (!latest) return conversation;

    const latestTimestamp = new Date(latest.updated_at || latest.created_at).getTime();
    const conversationTimestamp = new Date(
      conversation.updated_at || conversation.created_at
    ).getTime();

    return conversationTimestamp > latestTimestamp ? conversation : latest;
  }, null);
}

function MessageBubble({ message }: { message: MessageItem }) {
  const isAssistant = message.role === "assistant";

  return (
    <div className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}>
      <div
        className={[
          "max-w-[82%] rounded-3xl px-4 py-3 shadow-glow border",
          isAssistant
            ? "bg-ink-800/90 border-white/10 text-slate-100"
            : "bg-teal-500/15 border-teal-500/20 text-white"
        ].join(" ")}
      >
        <div className="whitespace-pre-wrap text-sm leading-6">{message.content}</div>

        {message.tool_calls?.length ? (
          <div className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-300">
            <div className="mb-2 font-semibold uppercase tracking-[0.18em] text-amber-400">
              Tool execution
            </div>
            <ul className="space-y-1">
              {message.tool_calls.map((call, index) => (
                <li key={`${message.message_id}-tool-${index}`}>
                  {call.tool}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {message.citations?.length ? (
          <div className="mt-3 space-y-2">
            <div className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
              Sources
            </div>
            <div className="grid gap-2">
              {message.citations.map((citation, index) => (
                <div
                  key={`${message.message_id}-citation-${index}`}
                  className="rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-slate-300"
                >
                  <span className="font-medium text-slate-100">{citation.source}</span>
                  {citation.page_number ? <span className="ml-2 text-slate-400">p. {citation.page_number}</span> : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ChatPanel({ initialConversations }: Props) {
  const [conversationList, setConversationList] = useState<ConversationListItem[]>(initialConversations);
  const [conversationId, setConversationId] = useState<string | null>(
    getLatestConversation(initialConversations)?.conversation_id ?? null
  );
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("Ready");
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setConversationList(initialConversations);
    setConversationId(getLatestConversation(initialConversations)?.conversation_id ?? null);
  }, [initialConversations]);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }

    let ignore = false;
    setStatus("Loading conversation");

    getConversation(conversationId)
      .then((data: ConversationHistory) => {
        if (!ignore) {
          setMessages(data.messages);
          setStatus("Ready");
        }
      })
      .catch(() => {
        if (!ignore) {
          setMessages([]);
          setStatus("Unable to load conversation");
        }
      });

    return () => {
      ignore = true;
    };
  }, [conversationId]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function handleNewConversation() {
    setConversationId(null);
    setMessages([]);
    setInput("");
    setStatus("Ready");
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    setInput("");
    setStatus("Thinking...");

    const userMessage: MessageItem = {
      message_id: `temp-${Date.now()}`,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString()
    };
    setMessages((current) => (conversationId ? [...current, userMessage] : [userMessage]));

    try {
      if (!conversationId) {
        const created = await createConversation(trimmed);
        setConversationId(created.conversation_id);
        setConversationList(await listConversations());
        const conversation = await getConversation(created.conversation_id);
        setMessages(conversation.messages);
      } else {
        const result = await sendMessage(conversationId, trimmed);
        setMessages((current) => [
          ...current,
          {
            message_id: result.message_id,
            role: "assistant",
            content: result.content,
            created_at: result.created_at,
            citations: result.citations,
            tool_calls: result.tool_calls
          }
        ]);
        setConversationList(await listConversations());
      }
      setStatus("Ready");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Something went wrong");
    }
  }

  const selectedConversation = conversationList.find((conversation) => conversation.conversation_id === conversationId);

  return (
    <div className="grid min-h-0 flex-1 grid-rows-[auto_minmax(0,1fr)] overflow-hidden rounded-[32px] border border-white/10 bg-ink-950/80 shadow-glow">
      <div className="flex flex-none items-center justify-between border-b border-white/10 px-6 py-4">
        <div>
          <div className="text-xs uppercase tracking-[0.28em] text-teal-500">Enterprise IT Support Agent</div>
          <h1 className="mt-1 text-xl font-semibold text-white">
            {selectedConversation?.title ?? "New support conversation"}
          </h1>
        </div>
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
          {status}
        </div>
      </div>

      <div className="grid min-h-0 grid-rows-[minmax(0,auto)_minmax(0,1fr)] gap-6 overflow-hidden px-6 py-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:grid-rows-1">
        <aside className="min-h-0 max-h-[24vh] overflow-y-auto rounded-[28px] border border-white/10 bg-black/15 p-4 lg:max-h-none">
          <div className="mb-4 text-xs uppercase tracking-[0.28em] text-slate-400">Conversation list</div>
          <button
            type="button"
            onClick={handleNewConversation}
            className="mb-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-teal-500/30 bg-teal-500/10 px-4 py-3 text-sm font-semibold text-teal-300 transition hover:bg-teal-500/20"
          >
            <span aria-hidden="true" className="text-lg leading-none">+</span>
            New Conversation
          </button>
          <div className="space-y-2">
            {conversationList.length ? (
              conversationList.map((conversation) => (
                <button
                  key={conversation.conversation_id}
                  onClick={() => setConversationId(conversation.conversation_id)}
                  className={[
                    "w-full rounded-2xl border px-4 py-3 text-left transition",
                    conversation.conversation_id === conversationId
                      ? "border-teal-500/30 bg-teal-500/10"
                      : "border-white/10 bg-white/5 hover:bg-white/8"
                  ].join(" ")}
                >
                  <div className="text-sm font-medium text-white">
                    {conversation.title ?? "Untitled conversation"}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">{conversation.status}</div>
                </button>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">
                Start a new conversation using the composer below.
              </div>
            )}
          </div>
        </aside>

        <section className="flex min-h-0 flex-col rounded-[28px] border border-white/10 bg-black/15">
          <div ref={messagesContainerRef} className="scrollbar min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain p-5">
            {messages.length ? (
              messages.map((message) => <MessageBubble key={message.message_id} message={message} />)
            ) : (
              <div className="flex h-full items-center justify-center rounded-[24px] border border-dashed border-white/10 p-10 text-center text-slate-400">
                Ask about VPN, printers, software access, or request a ticket.
              </div>
            )}
          </div>

          <form onSubmit={handleSend} className="border-t border-white/10 p-4">
            <div className="flex gap-3 rounded-[24px] border border-white/10 bg-ink-900/80 p-3">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                rows={2}
                placeholder="Ask a question or request help..."
                className="min-h-[52px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-white outline-none placeholder:text-slate-500"
              />
              <button
                type="submit"
                disabled={!input.trim()}
                className="rounded-2xl bg-teal-500 px-5 py-3 text-sm font-semibold text-ink-950 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Send
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
}
