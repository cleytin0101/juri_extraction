import client from "./client";
import type { DashboardMetrics } from "../types/metrics";

export async function fetchMetrics(): Promise<DashboardMetrics> {
  const { data } = await client.get<DashboardMetrics>("/metrics");
  return data;
}
