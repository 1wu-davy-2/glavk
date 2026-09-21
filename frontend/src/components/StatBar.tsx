interface StatBarProps {
  total: number;
  enabled: number;
  favorites: number;
}

function formatCount(value: number): string {
  return value.toString().padStart(2, "0");
}

export function StatBar({ total, enabled, favorites }: StatBarProps) {
  const stats = [
    { label: "全部系统", value: total },
    { label: "正常运行", value: enabled },
    { label: "我的收藏", value: favorites },
  ];

  return (
    <section className="stat-bar" aria-label="系统概览">
      {stats.map((stat) => (
        <div className="stat-cell" key={stat.label}>
          <small>{stat.label}</small>
          <strong>{formatCount(stat.value)}</strong>
        </div>
      ))}
    </section>
  );
}
