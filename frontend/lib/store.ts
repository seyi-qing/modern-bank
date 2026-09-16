/**
 * Lightweight global state for current user.
 */
import { create } from "zustand";

interface UserState {
  user: any | null;
  setUser: (u: any | null) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    set({ user: null });
  },
}));
