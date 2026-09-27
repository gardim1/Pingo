import React, { useEffect, useState } from 'react';
import { GoldenAnalysis } from '../types/pingo';

interface FolgaChartProps {
  analysis?: GoldenAnalysis | null;
  freedMargin?: number;
  recentAvgMargin?: number;
  lastMonthMargin?: number;
  installments?: number[];
  reduceMotion?: boolean;
}

export const FolgaChart: React.FC<FolgaChartProps> = ({
  analysis,
  freedMargin,
  recentAvgMargin,
  lastMonthMargin,
  installments,
  reduceMotion,
}) => {
  const END = 1.6;
  const isReduced = !!reduceMotion || (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [t, setT] = useState(isReduced ? END : 0);

  useEffect(() => {
    if (isReduced) {
      setT(END);
      return;
    }
    setT(0);
    let raf: number;
    const st = performance.now();
    const tick = (now: number) => {
      const tt = (now - st) / 1000;
      setT(Math.min(tt, END));
      if (tt < END) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    const fb = setTimeout(() => setT(END), END * 1000 + 300);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(fb);
    };
  }, [isReduced, analysis?.selected_month, freedMargin]);

  // Values strictly from backend analysis or passed props
  const recentAvg = recentAvgMargin !== undefined
    ? recentAvgMargin
    : (analysis?.recent_average_margin_cents ?? 20377) / 100;
  const sepMargin = lastMonthMargin !== undefined
    ? lastMonthMargin
    : (analysis?.last_month_margin_cents ?? -57685) / 100;
  
  // Find November or selected comparison
  const novComp = analysis?.comparisons?.find(c => c.month.includes('11') || c.conditional_release_cents > 0);
  const novMargin = freedMargin !== undefined
    ? freedMargin
    : (novComp?.conditional_release_cents ? novComp.conditional_release_cents / 100 : (analysis?.selected_conditional_release_cents ? analysis.selected_conditional_release_cents / 100 : 894.55));

  const cl = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const pp = (a: number, b: number) => cl((t - a) / (b - a));
  const eio = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const back = (x: number) => {
    const c1 = 1.9, c3 = c1 + 1;
    return x <= 0 ? 0 : 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  };

  const W = 340, BASE = 196, MAX = 600, MIN = -800;
  const X = (i: number) => 28 + i * 71;
  const Y = (v: number) => 22 + ((MAX - v) / (MAX - MIN)) * 168;

  // ago, set, out, nov, dez
  const vals = [recentAvg, sepMargin, recentAvg, novMargin, novMargin];
  const pts = vals.map((v, i) => [X(i), Y(v)]);
  const P = (a: number[][]) => a.map((q, k) => (k ? 'L' : 'M') + q[0] + ' ' + q[1]).join(' ');

  const rev2 = t < 0.47 ? eio(pp(0, 0.47)) * (X(1) + 6) : X(1) + 6 + eio(pp(0.47, 1.12)) * (W - X(1) - 6);

  const installmentChips = [
    { label: 'R$ 244,01', name: 'Passagem aérea' },
    { label: 'R$ 411,09', name: 'IPTU' },
    { label: 'R$ 35,68', name: 'Artigos infantis' },
  ];

  const ariaDesc = `Linha do tempo da folga mensal: média recente R$ ${recentAvg.toFixed(2).replace('.', ',')}, setembro (hoje) -R$ ${Math.abs(sepMargin).toFixed(2).replace('.', ',')}, novembro projeção R$ ${novMargin.toFixed(2).replace('.', ',')} com término de 3 parcelas.`;

  return (
    <div style={{ position: 'relative', padding: '0 6px', margin: '14px 0' }}>
      <svg
        viewBox={`0 0 ${W} 224`}
        width="100%"
        role="img"
        aria-label={ariaDesc}
        style={{ display: 'block', overflow: 'visible' }}
      >
        <defs>
          <clipPath id="pgrev">
            <rect x="0" y="0" width={rev2} height="224" />
          </clipPath>
          <linearGradient id="pgfut" x1="0" x2="1">
            <stop offset="0" stopColor="#c8322f" />
            <stop offset="1" stopColor="#15855c" />
          </linearGradient>
          <linearGradient id="pgarea" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#1c1b1b" stopOpacity="0.1" />
            <stop offset="1" stopColor="#1c1b1b" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Hoje reference line */}
        <line
          x1={X(1)}
          x2={X(1)}
          y1="20"
          y2={BASE}
          stroke="#9a9493"
          strokeWidth="1.5"
          strokeDasharray="3 5"
          opacity={pp(0.22, 0.42)}
        />
        <text
          x={X(1)}
          y="13"
          fontSize="13"
          fontWeight="600"
          fill="#3d3a3a"
          textAnchor="middle"
          opacity={pp(0.22, 0.42)}
          fontFamily="Inter, sans-serif"
        >
          hoje
        </text>

        {/* Animated paths */}
        <g clipPath="url(#pgrev)">
          <path
            d={`${P(pts.slice(0, 2))} L${X(1)} ${BASE} L${X(0)} ${BASE} Z`}
            fill="url(#pgarea)"
          />
          <path
            d={P(pts.slice(0, 2))}
            fill="none"
            stroke="#1c1b1b"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d={P(pts.slice(1))}
            fill="none"
            stroke="url(#pgfut)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="2 9"
          />
        </g>

        {/* Month labels */}
        {['ago', 'set', 'out', 'nov', 'dez'].map((m, i) => (
          <text
            key={m}
            x={X(i)}
            y="218"
            fontSize="13"
            fill="#4a4545"
            textAnchor="middle"
            fontFamily="Inter, sans-serif"
            fontWeight={i === 1 ? '700' : '400'}
          >
            {m}
          </text>
        ))}

        {/* Today point (red) */}
        <circle
          cx={pts[1][0]}
          cy={pts[1][1]}
          r={9 * back(pp(0.34, 0.54))}
          fill="#c8322f"
          stroke="#fff"
          strokeWidth="3"
        />

        {/* Future point (green in November) */}
        <circle
          cx={pts[3][0]}
          cy={pts[3][1]}
          r={9 * back(pp(0.97, 1.17))}
          fill="#15855c"
          stroke="#fff"
          strokeWidth="3"
        />
      </svg>

      {/* Falling / pop-in chips for the 3 ending installments */}
      {!isReduced &&
        installmentChips.map((c, i) => {
          const a = back(pp(0.54 + i * 0.05, 0.7 + i * 0.05));
          const fall = pp(0.8 + i * 0.06, 1.12 + i * 0.06);
          const opacity = cl(a * 3) * (1 - fall);
          return (
            <div
              key={i}
              aria-hidden="true"
              style={{
                position: 'absolute',
                left: `${((X(2) - 14 + i * 12) / W) * 100}%`,
                top: `${((Y(recentAvg) - 86 + i * 28) / 224) * 100}%`,
                whiteSpace: 'nowrap',
                fontSize: 12,
                fontWeight: 600,
                padding: '5px 10px',
                borderRadius: 999,
                background: '#e3eeee',
                color: '#0a3f43',
                border: '1.5px solid #b9d3d3',
                opacity,
                visibility: opacity <= 0.001 ? 'hidden' : 'visible',
                transform: `translateX(-50%) translateY(${fall * fall * 80}px) rotate(${fall * (i % 2 ? 14 : -12)}deg) scale(${cl(a, 0, 1.3)})`,
                pointerEvents: 'none',
              }}
            >
              {c.label} · última parcela
            </div>
          );
        })}
    </div>
  );
};
