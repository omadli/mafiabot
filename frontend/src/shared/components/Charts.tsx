/**
 * Lightweight inline-SVG chart components — no external dependency.
 *
 * Used by both the admin Dashboard and the SuperAdmin WebApp dashboard.
 */

// === Bar chart (vertical bars, value labels on top) ===

interface BarChartProps {
  bins: { label: string; count: number }[];
  height?: number;
  color?: string;
}

export function BarChart({ bins, height = 200, color = "var(--accent)" }: BarChartProps) {
  const max = Math.max(...bins.map((b) => b.count), 1);
  return (
    <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-end", height: `${height}px` }}>
      {bins.map((b) => (
        <div
          key={b.label}
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            minWidth: 0,
          }}
        >
          <div
            style={{
              width: "100%",
              height: `${(b.count / max) * (height - 30)}px`,
              background: color,
              borderRadius: "6px 6px 0 0",
              minHeight: b.count > 0 ? "4px" : "0",
              transition: "height 0.3s",
              position: "relative",
            }}
          >
            {b.count > 0 && (
              <div
                style={{
                  position: "absolute",
                  top: "-1.5rem",
                  left: 0,
                  right: 0,
                  textAlign: "center",
                  fontSize: "0.75rem",
                  color: "var(--fg)",
                }}
              >
                {b.count}
              </div>
            )}
          </div>
          <div
            style={{
              fontSize: "0.7rem",
              color: "var(--muted)",
              marginTop: "0.5rem",
              textAlign: "center",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: "100%",
              whiteSpace: "nowrap",
            }}
            title={b.label}
          >
            {b.label}
          </div>
        </div>
      ))}
    </div>
  );
}

// === Horizontal bar chart (label on left, bar fills right) ===

interface HBarChartProps {
  items: { label: string; value: number; subText?: string; color?: string }[];
  max?: number;
  unit?: string;
}

export function HBarChart({ items, max, unit }: HBarChartProps) {
  const m = max ?? Math.max(...items.map((i) => i.value), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {items.map((it, idx) => (
        <div key={`${it.label}-${idx}`}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "0.8rem",
              marginBottom: "0.2rem",
            }}
          >
            <span>{it.label}</span>
            <span style={{ color: "var(--muted)" }}>
              {it.value}
              {unit ?? ""}
              {it.subText ? ` · ${it.subText}` : ""}
            </span>
          </div>
          <div
            style={{
              height: "8px",
              background: "#2a2a45",
              borderRadius: "4px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${Math.min(100, (it.value / m) * 100)}%`,
                height: "100%",
                background: it.color ?? "var(--accent)",
                transition: "width 0.3s",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// === Line chart (single series, time on X, count on Y) ===

interface LineChartProps {
  series: { date: string; count: number }[];
  height?: number;
  color?: string;
}

export function LineChart({ series, height = 180, color = "var(--accent)" }: LineChartProps) {
  if (series.length === 0) return null;

  const max = Math.max(...series.map((s) => s.count), 1);
  const width = 800;
  const padding = 30;

  const points = series.map((s, i) => {
    const x = padding + (i * (width - 2 * padding)) / Math.max(1, series.length - 1);
    const y = height - padding - (s.count / max) * (height - 2 * padding);
    return { x, y, ...s };
  });

  const pathD = points.map((p, i) => (i === 0 ? `M${p.x},${p.y}` : `L${p.x},${p.y}`)).join(" ");

  // Area fill
  const areaD =
    pathD +
    ` L${points[points.length - 1].x},${height - padding}` +
    ` L${points[0].x},${height - padding} Z`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: `${height}px` }}>
      {/* Y-axis gridlines */}
      {[0.25, 0.5, 0.75].map((p) => (
        <line
          key={p}
          x1={padding}
          x2={width - padding}
          y1={height - padding - p * (height - 2 * padding)}
          y2={height - padding - p * (height - 2 * padding)}
          stroke="#2a2a45"
          strokeWidth="1"
          strokeDasharray="3 3"
        />
      ))}
      {/* Area */}
      <path d={areaD} fill={color} opacity="0.15" />
      {/* Line */}
      <path d={pathD} fill="none" stroke={color} strokeWidth="2" />
      {/* Dots */}
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill={color}>
          <title>
            {p.date}: {p.count}
          </title>
        </circle>
      ))}
      {/* X-axis edge labels */}
      <text x={padding} y={height - 5} fill="var(--muted)" fontSize="10">
        {series[0]?.date}
      </text>
      <text x={width - padding - 60} y={height - 5} fill="var(--muted)" fontSize="10">
        {series[series.length - 1]?.date}
      </text>
    </svg>
  );
}
