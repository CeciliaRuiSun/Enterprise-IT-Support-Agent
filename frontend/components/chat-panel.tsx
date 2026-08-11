"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import {
  closeConversation,
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  pinConversation,
  sendMessage,
  unpinConversation
} from "@/lib/api";
import type { ConversationHistory, ConversationListItem, MessageItem } from "@/types";

type Props = {
  initialConversations: ConversationListItem[];
};

function getLatestConversation(conversations: ConversationListItem[]) {
  return conversations.reduce<ConversationListItem | null>((latest, conversation) => {
    if (!latest) return conversation;
    if (conversation.is_pinned !== latest.is_pinned) {
      return conversation.is_pinned ? conversation : latest;
    }

    const latestTimestamp = new Date(latest.updated_at || latest.created_at).getTime();
    const conversationTimestamp = new Date(
      conversation.updated_at || conversation.created_at
    ).getTime();

    return conversationTimestamp > latestTimestamp ? conversation : latest;
  }, null);
}

function PinIcon({ filled = false }: { filled?: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill={filled ? "currentColor" : "none"}>
      <path d="m14 3 7 7-2.5 2.5-2-2-3.75 3.75 1 4.25-1.5 1.5-4.25-1-3.75 3.75-1.5-1.5 3.75-3.75-1-4.25 1.5-1.5 4.25 1L15 8.5l-2-2L14 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="m5 19 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill="none">
      <path d="M4 7.5h16v11H4v-11Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M3 4h18v3.5H3V4Zm6 7h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill="none">
      <path d="M5 7h14M10 4h4l1 3H9l1-3Zm-2 3 1 13h6l1-13M10 11v5m4-5v5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function getUniqueCitations(citations: MessageItem["citations"]) {
  const unique = new Map<string, NonNullable<MessageItem["citations"]>[number]>();

  for (const citation of citations ?? []) {
    const sourceKey = citation.source.trim().toLowerCase();
    if (!unique.has(sourceKey)) {
      unique.set(sourceKey, citation);
    }
  }

  return [...unique.values()];
}

function cleanAssistantContent(content: string, citations: MessageItem["citations"]) {
  let cleaned = content;
  for (const citation of citations ?? []) {
    const source = citation.source.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    cleaned = cleaned
      .replace(new RegExp(`\\([^\\n)]*${source}\\s*:[^\\n)]*\\)`, "gi"), "")
      .replace(new RegExp(`${source}\\s*:[^\\n)]*\\)`, "gi"), "")
      .replace(new RegExp(`\\(?${source}\\)?\\s*:\\s*`, "gi"), "");
  }

  return cleaned.replace(/^\s*ticket\)\s*$/gim, "").replace(/\n{3,}/g, "\n\n").trim();
}

function MessageBubble({
  message,
  showWorkflowActions,
  workflowAction,
  onWorkflowDecision
}: {
  message: MessageItem;
  showWorkflowActions: boolean;
  workflowAction: "confirm" | "cancel" | null;
  onWorkflowDecision: (decision: "confirm" | "cancel") => void;
}) {
  const isAssistant = message.role === "assistant";
  const citations = getUniqueCitations(message.citations);
  const content = isAssistant ? cleanAssistantContent(message.content, citations) : message.content;
  const isTicketSummary = message.tool_calls?.some((call) => call.tool === "ticket_summary");

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
        <div className="whitespace-pre-wrap text-sm leading-6">{content}</div>

        {showWorkflowActions && isAssistant && isTicketSummary ? (
          <div className="mt-4 flex gap-2 border-t border-white/10 pt-4">
            <button
              type="button"
              onClick={() => onWorkflowDecision("confirm")}
              disabled={workflowAction !== null}
              className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-ink-950 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {workflowAction === "confirm" ? "Submitting..." : "Confirm"}
            </button>
            <button
              type="button"
              onClick={() => onWorkflowDecision("cancel")}
              disabled={workflowAction !== null}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {workflowAction === "cancel" ? "Cancelling..." : "Cancel"}
            </button>
          </div>
        ) : null}

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

        {citations.length ? (
          <div className="mt-3 space-y-2">
            <div className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
              Sources
            </div>
            <div className="grid gap-2">
              {citations.map((citation, index) => (
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
  const [conversationActionId, setConversationActionId] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<ConversationListItem | null>(null);
  const [pendingClose, setPendingClose] = useState<ConversationListItem | null>(null);
  const [workflowAction, setWorkflowAction] = useState<"confirm" | "cancel" | null>(null);
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

  async function refreshConversations(selectReplacement = false) {
    const refreshed = await listConversations();
    setConversationList(refreshed);
    if (selectReplacement) {
      setConversationId(getLatestConversation(refreshed)?.conversation_id ?? null);
    }
  }

  async function handlePin(conversation: ConversationListItem) {
    setConversationActionId(conversation.conversation_id);
    try {
      if (conversation.is_pinned) {
        await unpinConversation(conversation.conversation_id);
      } else {
        await pinConversation(conversation.conversation_id);
      }
      await refreshConversations();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to update pin status");
    } finally {
      setConversationActionId(null);
    }
  }

  function handleClose(conversation: ConversationListItem) {
    setPendingClose(conversation);
  }

  async function confirmClose() {
    if (!pendingClose) return;

    const conversation = pendingClose;
    setConversationActionId(conversation.conversation_id);
    try {
      await closeConversation(conversation.conversation_id);
      await refreshConversations();
      setPendingClose(null);
      setStatus("Ready");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to close conversation");
    } finally {
      setConversationActionId(null);
    }
  }

  async function handleDelete(conversation: ConversationListItem) {
    setPendingDelete(conversation);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;

    const conversation = pendingDelete;
    setConversationActionId(conversation.conversation_id);
    try {
      await deleteConversation(conversation.conversation_id);
      await refreshConversations(conversation.conversation_id === conversationId);
      setPendingDelete(null);
      setStatus("Ready");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to delete conversation");
    } finally {
      setConversationActionId(null);
    }
  }

  async function handleWorkflowDecision(decision: "confirm" | "cancel") {
    if (!conversationId || workflowAction) return;

    setWorkflowAction(decision);
    setStatus(decision === "confirm" ? "Submitting ticket..." : "Cancelling ticket...");
    setMessages((current) => [
      ...current,
      {
        message_id: `temp-workflow-${Date.now()}`,
        role: "user",
        content: decision,
        created_at: new Date().toISOString()
      }
    ]);

    try {
      const result = await sendMessage(conversationId, decision);
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
      setStatus("Ready");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setWorkflowAction(null);
    }
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    const currentConversation = conversationList.find(
      (conversation) => conversation.conversation_id === conversationId
    );
    if (!trimmed || currentConversation?.status === "closed") return;

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
                <div
                  key={conversation.conversation_id}
                  className="group relative"
                >
                  <button
                    type="button"
                    onClick={() => setConversationId(conversation.conversation_id)}
                    className={[
                      "w-full rounded-2xl border px-4 py-3 pr-24 text-left transition",
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
                  <div className="pointer-events-none absolute right-2 top-2 flex rounded-xl border border-white/10 bg-ink-900/95 p-1 opacity-0 shadow-lg transition group-hover:pointer-events-auto group-hover:opacity-100 group-focus-within:pointer-events-auto group-focus-within:opacity-100">
                    <button
                      type="button"
                      title={conversation.is_pinned ? "Unpin conversation" : "Pin conversation"}
                      aria-label={conversation.is_pinned ? "Unpin conversation" : "Pin conversation"}
                      disabled={conversationActionId === conversation.conversation_id}
                      onClick={() => void handlePin(conversation)}
                      className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-white disabled:opacity-40"
                    >
                      <PinIcon filled={conversation.is_pinned} />
                    </button>
                    {conversation.status !== "closed" ? (
                      <button
                        type="button"
                        title="Close conversation"
                        aria-label="Close conversation"
                        disabled={conversationActionId === conversation.conversation_id}
                        onClick={() => handleClose(conversation)}
                        className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-white disabled:opacity-40"
                      >
                        <CloseIcon />
                      </button>
                    ) : null}
                    <button
                      type="button"
                      title="Delete conversation"
                      aria-label="Delete conversation"
                      disabled={conversationActionId === conversation.conversation_id}
                      onClick={() => void handleDelete(conversation)}
                      className="rounded-lg p-2 text-slate-400 transition hover:bg-red-500/20 hover:text-red-300 disabled:opacity-40"
                    >
                      <TrashIcon />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">
                Start a new conversation using the composer below.
              </div>
            )}
          </div>
        </aside>

        <section className="relative flex min-h-0 flex-col rounded-[28px] border border-white/10 bg-black/15">
          <div ref={messagesContainerRef} className="scrollbar min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain p-5">
            {messages.length ? (
              messages.map((message, index) => {
                const isPendingTicketSummary = message.tool_calls?.some(
                  (call) => call.tool === "ticket_summary"
                );
                const hasWorkflowResultAfter = messages.slice(index + 1).some((laterMessage) =>
                  laterMessage.tool_calls?.some(
                    (call) => call.tool === "create_ticket" || call.tool === "workflow_cancel"
                  )
                );

                return (
                  <MessageBubble
                    key={message.message_id}
                    message={message}
                    showWorkflowActions={Boolean(isPendingTicketSummary && !hasWorkflowResultAfter)}
                    workflowAction={workflowAction}
                    onWorkflowDecision={handleWorkflowDecision}
                  />
                );
              })
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
                disabled={selectedConversation?.status === "closed"}
                placeholder={selectedConversation?.status === "closed" ? "This conversation is closed." : "Ask a question or request help..."}
                className="min-h-[52px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-white outline-none placeholder:text-slate-500"
              />
              <button
                type="submit"
                disabled={!input.trim() || selectedConversation?.status === "closed"}
                className="rounded-2xl bg-teal-500 px-5 py-3 text-sm font-semibold text-ink-950 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Send
              </button>
            </div>
          </form>

          {pendingDelete || pendingClose ? (
            <div
              className="absolute inset-0 z-20 flex items-center justify-center rounded-[28px] bg-ink-950/70 p-6 backdrop-blur-sm"
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-conversation-title"
            >
              <div className="w-full max-w-md rounded-3xl border border-white/10 bg-ink-900 p-6 shadow-2xl">
                {pendingDelete ? (
                  <>
                    <h2 id="delete-conversation-title" className="text-lg font-semibold text-white">
                      Delete conversation?
                    </h2>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      “{pendingDelete.title ?? "Untitled conversation"}” will be removed from your conversation list.
                      Its messages will be kept in the backend.
                    </p>
                  </>
                ) : (
                  <>
                    <h2 id="delete-conversation-title" className="text-lg font-semibold text-white">
                      Close conversation?
                    </h2>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      “{pendingClose?.title ?? "Untitled conversation"}” will be marked closed and cannot be reactivated.
                      Its messages will be kept in the backend.
                    </p>
                  </>
                )}
                <div className="mt-6 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setPendingDelete(null);
                      setPendingClose(null);
                    }}
                    disabled={conversationActionId !== null}
                    className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-slate-200 transition hover:bg-white/10 disabled:opacity-40"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => void (pendingDelete ? confirmDelete() : confirmClose())}
                    disabled={conversationActionId !== null}
                    className="rounded-xl bg-red-500/90 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500 disabled:opacity-40"
                  >
                    {conversationActionId !== null
                      ? pendingDelete
                        ? "Deleting..."
                        : "Closing..."
                      : pendingDelete
                        ? "Delete"
                        : "Close"}
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
