import { create } from "zustand";
import type { LeadStatus } from "../types/lead";

interface FilterStore {
  activeStatus: LeadStatus | undefined;
  page: number;
  orgaoJulgador: string | undefined;
  valorMin: number | undefined;
  valorMax: number | undefined;
  dataAudienciaDe: string | undefined;
  dataAudienciaAte: string | undefined;
  setStatus: (s: LeadStatus | undefined) => void;
  setPage: (p: number) => void;
  setOrgaoJulgador: (v: string | undefined) => void;
  setValorMin: (v: number | undefined) => void;
  setValorMax: (v: number | undefined) => void;
  setDataAudienciaDe: (v: string | undefined) => void;
  setDataAudienciaAte: (v: string | undefined) => void;
  clearFilters: () => void;
}

export const useFilterStore = create<FilterStore>((set) => ({
  activeStatus: undefined,
  page: 1,
  orgaoJulgador: undefined,
  valorMin: undefined,
  valorMax: undefined,
  dataAudienciaDe: undefined,
  dataAudienciaAte: undefined,
  setStatus: (s) => set({ activeStatus: s, page: 1 }),
  setPage: (p) => set({ page: p }),
  setOrgaoJulgador: (v) => set({ orgaoJulgador: v, page: 1 }),
  setValorMin: (v) => set({ valorMin: v, page: 1 }),
  setValorMax: (v) => set({ valorMax: v, page: 1 }),
  setDataAudienciaDe: (v) => set({ dataAudienciaDe: v, page: 1 }),
  setDataAudienciaAte: (v) => set({ dataAudienciaAte: v, page: 1 }),
  clearFilters: () => set({
    activeStatus: undefined,
    orgaoJulgador: undefined,
    valorMin: undefined,
    valorMax: undefined,
    dataAudienciaDe: undefined,
    dataAudienciaAte: undefined,
    page: 1,
  }),
}));
