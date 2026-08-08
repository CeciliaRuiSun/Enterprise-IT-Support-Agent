import type {
  ConversationCreateResponse,
  ConversationHistory,
  ConversationListItem,
  SendMessageResponse
} from "@/types";

const publicBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/backend-api";
const baseUrl =
  typeof window === "undefined" && publicBaseUrl.startsWith("/")
    ? process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
    : publicBaseUrl;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      },
      cache: "no-store"
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach the backend at ${baseUrl}. Start the FastAPI server and try again.`);
    }
    throw error;
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function listConversations(): Promise<ConversationListItem[]> {
  const data = await request<{ conversations: ConversationListItem[] }>("/conversations");
  return data.conversations;
}

export async function getConversation(conversationId: string): Promise<ConversationHistory> {
  return request<ConversationHistory>(`/conversations/${conversationId}`);
}

export async function createConversation(messageContent: string): Promise<ConversationCreateResponse> {
  return request<ConversationCreateResponse>("/conversations", {
    method: "POST",
    body: JSON.stringify({ message_content: messageContent })
  });
}

export async function sendMessage(
  conversationId: string,
  messageContent: string
): Promise<SendMessageResponse> {
  return request<SendMessageResponse>(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ role: "user", message_content: messageContent })
  });
}
