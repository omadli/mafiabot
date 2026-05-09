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
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      authStore.getState().logout();
      if (window.location.pathname.startsWith("/admin") && window.location.pathname !== "/admin/login") {
        window.location.href = "/admin/login";
      }
    }
    return Promise.reject(error);
  },
);
