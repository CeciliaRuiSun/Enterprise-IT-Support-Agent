import type {
  ConversationCreateResponse,
  ConversationHistory,
  ConversationListItem,
  SendMessageResponse
} from "@/types";

type AccessTokenProvider = (forceRefresh?: boolean) => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;
let meRequest: Promise<MeResponse> | null = null;

export function registerAccessTokenProvider(provider: AccessTokenProvider) {
  accessTokenProvider = provider;
  return () => {
    if (accessTokenProvider === provider) accessTokenProvider = null;
  };
}

const publicBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/backend-api";
const baseUrl =
  typeof window === "undefined" && publicBaseUrl.startsWith("/")
    ? process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
    : publicBaseUrl;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  let accessToken = accessTokenProvider ? await accessTokenProvider() : null;

  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(init?.headers ?? {})
      },
      cache: "no-store"
    });

    if (response.status === 401 && accessTokenProvider && accessToken) {
      accessToken = await accessTokenProvider(true);
      if (accessToken) {
        response = await fetch(`${baseUrl}${path}`, {
          ...init,
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
            ...(init?.headers ?? {})
          },
          cache: "no-store"
        });
      }
    }
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

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export type MeResponse = {
  entra_object_id: string;
  tenant_id: string;
  email: string | null;
  display_name: string | null;
  scopes: string[];
};

export async function getMe(): Promise<MeResponse> {
  if (!meRequest) {
    meRequest = request<MeResponse>("/me").finally(() => {
      meRequest = null;
    });
  }
  return meRequest;
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

export async function pinConversation(conversationId: string): Promise<ConversationListItem> {
  return request<ConversationListItem>(`/conversations/${conversationId}/pin`, { method: "POST" });
}

export async function unpinConversation(conversationId: string): Promise<ConversationListItem> {
  return request<ConversationListItem>(`/conversations/${conversationId}/pin`, { method: "DELETE" });
}

export async function closeConversation(conversationId: string): Promise<ConversationListItem> {
  return request<ConversationListItem>(`/conversations/${conversationId}/close`, { method: "POST" });
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await request<void>(`/conversations/${conversationId}`, { method: "DELETE" });
}
