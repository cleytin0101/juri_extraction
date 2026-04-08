import {
  BarChart as ReBarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { DayCount } from "../../types/metrics";

interface Props {
  data: DayCount[];
}

export function BarChart({ data }: Props) {
  return (
    <div className="bg-surface-800 rounded-xl p-5 border border-surface-600">
      <h3 className="text-sm font-medium text-gray-400 mb-4">
        Audiências por Dia da Semana
      </h3>
      <ResponsiveContainer width="100%" height={180}>
        <ReBarChart data={data} barSize={14}>
          <XAxis
            dataKey="dia"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            contentStyle={{
              background: "#252836",
              border: "1px solid #2d3148",
              borderRadius: 8,
              color: "#fff",
              fontSize: 12,
            }}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 11, color: "#9ca3af" }}
          />
          <Bar dataKey="multiplas" name="Múltiplas" fill="#4f8ef7" radius={[3, 3, 0, 0]} stackId="a" />
          <Bar dataKey="unica" name="Única" fill="#a855f7" radius={[3, 3, 0, 0]} stackId="a" />
        </ReBarChart>
      </ResponsiveContainer>
    </div>
  );
}
