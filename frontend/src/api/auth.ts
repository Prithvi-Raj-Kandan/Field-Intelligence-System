import { apiFetch } from "./client";
import type { TokenResponse, User } from "../types/api";

export async function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(
  email: string,
  password: string,
  name: string,
  role: "field_worker" | "manager" = "field_worker",
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name, role }),
  });
}

export async function fetchMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export async function logoutApi(): Promise<void> {
  await apiFetch<void>("/auth/logout", { method: "POST" });
}
