import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { TipoCount } from "../../types/metrics";

interface Props {
  data: TipoCount[];
}

export function DonutChart({ data }: Props) {
  const total = data.reduce((s, d) => s + d.count, 0);

  return (
    <div className="bg-surface-800 rounded-xl p-5 border border-surface-600">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Tipo de Audiência</h3>
      {total === 0 ? (
        <div className="flex items-center justify-center h-40 text-gray-500 text-sm">
          Sem dados
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="tipo"
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={75}
              paddingAngle={3}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
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
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
