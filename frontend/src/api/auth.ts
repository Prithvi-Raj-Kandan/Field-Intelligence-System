import { apiFetch, saveUser, setToken } from "./client";
import type { TokenResponse } from "../types/api";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  saveUser(data.user);
  return data;
}

export async function register(
  email: string,
  password: string,
  role: "field_worker" | "manager" = "field_worker",
): Promise<TokenResponse> {
  const data = await apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, role }),
  });
  setToken(data.access_token);
  saveUser(data.user);
  return data;
}

export async function fetchMe() {
  return apiFetch<{ id: number; email: string; role: string }>("/auth/me");
}
