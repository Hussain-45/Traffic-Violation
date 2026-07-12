export const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface CustomFetchOptions extends RequestInit {
  timeout?: number;
}

export async function fetchWithTimeout(
  url: string,
  options: CustomFetchOptions = {}
): Promise<Response> {
  const { timeout = 10000, ...restOptions } = options;

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...restOptions,
      signal: controller.signal,
    });
    clearTimeout(id);
    return response;
  } catch (error: any) {
    clearTimeout(id);
    if (error.name === "AbortError") {
      throw new Error("Request timed out. Please check your network connection.");
    }
    throw error;
  }
}

export function getErrorMessage(status: number): string {
  switch (status) {
    case 401:
      return "Unauthorized. Please login again.";
    case 403:
      return "Access denied. Administrative clearance required.";
    case 404:
      return "Requested resource not found on backend services.";
    case 500:
      return "Internal server error. Please inspect backend logs.";
    default:
      return "Backend unavailable. Check if the server is offline.";
  }
}
