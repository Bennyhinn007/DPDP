/**
 * Authentication API Service.
 */

import api from "./api";
import type { LoginResponse, User } from "@/types";

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
    return data;
  },

  async register(
    email: string,
    password: string,
    role: string,
    full_name: string
  ): Promise<{ message: string; user: User }> {
    const { data } = await api.post("/auth/register", { email, password, role, full_name });
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<{ user: User }>("/auth/me");
    return data.user;
  },
};
