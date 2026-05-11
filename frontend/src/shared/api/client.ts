import axios, { AxiosError, type AxiosInstance } from "axios";

import { authStore } from "@shared/store/auth";

export const api: AxiosInstance = axios.create({
  baseURL: "/api",
  timeout: 15_000,
});

api.interceptors.request.use((config) => {
  const token = authStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Telegram WebApp auth: attach initData + chat_id when running inside Telegram
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    if (tg.initData) {
      config.headers["X-Telegram-Init-Data"] = tg.initData;
    }
    // Chat ID is encoded in URL (e.g., /webapp/settings/-1001234567890)
    const match = window.location.pathname.match(/\/webapp\/[^/]+\/(-?\d+)/);
    if (match) {
      config.headers["X-Chat-Id"] = match[1];
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Don't auto-logout for WebApp routes
      if (window.location.pathname.startsWith("/admin") && window.location.pathname !== "/admin/login") {
        authStore.getState().logout();
        window.location.href = "/admin/login";
      }
    }
    return Promise.reject(error);
  },
);

// Type augmentation for Telegram WebApp
declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        initDataUnsafe?: {
          start_param?: string;
          user?: { id: number; language_code?: string };
        };
        ready?: () => void;
        expand?: () => void;
        colorScheme?: string;
        HapticFeedback?: { notificationOccurred?: (type: string) => void };
      };
    };
  }
}
