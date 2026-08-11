export type ConversationStatus = "active" | "closed";
export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface ConversationListItem {
  conversation_id: string;
  title?: string | null;
  status: ConversationStatus;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageItem {
  message_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
  citations?: Citation[] | null;
  tool_calls?: ToolCall[] | null;
}

export interface ConversationHistory {
  conversation_id: string;
  title?: string | null;
  status: ConversationStatus;
  messages: MessageItem[];
}

export interface ConversationCreateResponse {
  conversation_id: string;
  status: ConversationStatus;
  created_at: string;
  message: MessageItem;
}

export interface SendMessageResponse {
  message_id: string;
  content: string;
  conversation_id: string;
  created_at: string;
  citations?: Citation[] | null;
  tool_calls?: ToolCall[] | null;
}

export interface Citation {
  source: string;
  chunk_id: string;
  page_number?: number | null;
  score?: number | null;
}

export interface ToolCall {
  tool: string;
  [key: string]: unknown;
}
