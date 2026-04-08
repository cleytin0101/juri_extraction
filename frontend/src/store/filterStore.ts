import { create } from "zustand";
import type { LeadStatus } from "../types/lead";

interface FilterStore {
  activeStatus: LeadStatus | undefined;
  page: number;
  setStatus: (s: LeadStatus | undefined) => void;
  setPage: (p: number) => void;
}

export const useFilterStore = create<FilterStore>((set) => ({
  activeStatus: undefined,
  page: 1,
  setStatus: (s) => set({ activeStatus: s, page: 1 }),
  setPage: (p) => set({ page: p }),
}));
