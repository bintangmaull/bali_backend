import React, { useState, useEffect, useRef } from 'react';
import html2canvas from 'html2canvas';
import { useTheme } from '../context/ThemeContext';
import { createPortal } from 'react-dom';
import { TrendingUp, TrendingDown, Info, Maximize2, Minimize2, MapPin, X, BarChart2, Check, ExternalLink, Filter, Shield, Layers, Calendar, ChevronDown, ChevronLeft, ChevronRight, Table2 as TableIcon, Layout, Download } from 'lucide-react';
import { MANUAL_GEMPA_DATA } from '../src/lib/manual_gempa_data';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { DROUGHT_CURVE } from '../src/lib/drought_curve';

const formatUSD = (v) => {
  if (!v && v !== 0) return '-';
  if (typeof v !== 'number') return v;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v * 0.00006);
};

const colorsAAL = ['#1a9850', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027', '#7f0000'];

function jenks(data, n_classes) {
  if (!Array.isArray(data) || data.length === 0) return [];
  if (data.length <= n_classes) return [...new Set(data)].sort((a, b) => a - b);
  data = data.slice().sort((a, b) => a - b);
  const matrices = Array(data.length + 1).fill(0).map(() => Array(n_classes + 1).fill(0));
  const variances = Array(data.length + 1).fill(0).map(() => Array(n_classes + 1).fill(0));
  for (let i = 1; i <= n_classes; i++) {
    matrices[0][i] = 1;
    variances[0][i] = 0;
    for (let j = 1; j <= data.length; j++) {
      variances[j][i] = Infinity;
    }
  }
  for (let l = 1; l <= data.length; l++) {
    let sum = 0, sumSquares = 0, w = 0;
    for (let m = 1; m <= l; m++) {
      const i3 = l - m + 1;
      const val = data[i3 - 1];
      w++;
      sum += val;
      sumSquares += val * val;
      const variance = sumSquares - (sum * sum) / w;
      if (i3 !== 1) {
        for (let j = 2; j <= n_classes; j++) {
          if (variances[l][j] >= (variance + variances[i3 - 1][j - 1])) {
            matrices[l][j] = i3;
            variances[l][j] = variance + variances[i3 - 1][j - 1];
          }
        }
      }
    }
    matrices[l][1] = 1;
    variances[l][1] = sumSquares - (sum * sum) / w;
  }
  const k = data.length;
  const kclass = Array(n_classes + 1).fill(0);
  kclass[n_classes] = data[data.length - 1];
  kclass[0] = data[0];
  let countNum = n_classes;
  let kTmp = k;
  while (countNum > 1) {
    if (matrices[kTmp] && matrices[kTmp][countNum] !== undefined) {
      kclass[countNum - 1] = data[matrices[kTmp][countNum] - 2];
      kTmp = matrices[kTmp][countNum] - 1;
    }
    countNum--;
  }
  return kclass;
}

// ΓöÇΓöÇ AAL Chart Sub-Component ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
const HAZARD_KEYS = [
  { key: 'pga', label: 'Gempa\nBumi', color: '#ef4444' },
  { key: 'inundansi', label: 'Tsunami', color: '#8b5cf6' },
  { key: 'r', label: 'Banjir\n(R)', color: '#3b82f6' },
  { key: 'rc', label: 'Banjir\n(RC)', color: '#0ea5e9' },
];

const PML_RP_KEYS = [
  { key: '100', label: '100 TH', color: '#6366f1' },
  { key: '200', label: '200 TH', color: '#818cf8' },
  { key: '250', label: '250 TH', color: '#a5b4fc' },
  { key: '500', label: '500 TH', color: '#c7d2fe' },
  { key: '1000', label: '1000 TH', color: '#e0e7ff' },
];

const formatYAxisShort = (val, isPercentage = false) => {
  if (isPercentage) return `${val.toFixed(2)}%`;
  if (val >= 1e12) return `Rp${(val / 1e12).toFixed(1)}T`;
  if (val >= 1e9) return `Rp${(val / 1e9).toFixed(0)}M`;
  if (val >= 1e6) return `Rp${(val / 1e6).toFixed(0)}Jt`;
  return val.toLocaleString('id-ID');
};

const ComparisonTooltip = ({ active, payload, label }) => {
  const { darkMode } = useTheme();
  if (active && payload && payload.length) {
    return (
      <div className={`backdrop-blur border p-2 rounded-lg shadow-lg transition-colors duration-300 ${darkMode ? 'bg-gray-900 border-gray-700' : 'bg-white/95 border-slate-200'
        }`}>
        <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-800' : 'text-slate-800 border-slate-100'}`}>{label}</p>
        <div className="flex flex-col gap-1">
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
              <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                <span>{entry.name.replace('\n', ' ')}</span>
              </div>
              <div className="flex flex-col items-end">
                <span className={`font-bold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(entry.value)}</span>
                <span className={`text-[7px] font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>({formatUSD(entry.value)})</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};
const EXPOSURE_GROUPS = [
  { exp: 'total', label: 'All Buildings' },
  { exp: 'fs', label: 'Healthcare Facilities', layerKey: 'healthcare' },
  { exp: 'fd', label: 'Educational Facilities', layerKey: 'educational' },
  { exp: 'electricity', label: 'Electricity', layerKey: 'electricity' },
  { exp: 'hotel', label: 'Hotel', layerKey: 'hotel' },
  { exp: 'airport', label: 'Airport', layerKey: 'airport' },
  { exp: 'residential', aalSuffix: 'res', label: 'Residential', layerKey: 'residential', gempaOnly: true },
  { exp: 'bmn', label: 'BMN', layerKey: 'bmn', gempaOnly: true },
];

// Manual Gempa Data is now handled by the backend rekap-aset-kota API

const getManualGempaAddition = (cityName, type) => {
  return { count: 0, asset: 0 };
};

function MiniBarChart({ data, maxVal, expAsset = 0 }) {
  const W = 230, H = 84, PAD = { l: 26, r: 8, t: 10, b: 24 };
  const chartW = W - PAD.l - PAD.r;
  const chartH = H - PAD.t - PAD.b;
  const { darkMode } = useTheme();
  const barW = Math.floor(chartW / data.length) - 8;
  const fmtM = v => {
    if (v >= 1e9) return (v / 1e9).toFixed(1) + 'T';
    if (v >= 1e6) return (v / 1e6).toFixed(0) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(0) + 'K';
    if (v >= 1) return v % 1 === 0 ? v.toString() : v.toFixed(1);
    // Small ratio value (likely a loss ratio in percentage form, e.g. 0.03)
    if (v > 0) return v.toFixed(3) + '%';
    return '0';
  };
  const [hoverData, setHoverData] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = React.useRef(null);

  const fmtFull = v => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);
  const formatUSD = (v) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v * 0.00006);

  return (
    <div className="relative inline-block" ref={containerRef} onMouseLeave={() => setHoverData(null)}>
      <svg width={W} height={H} style={{ overflow: 'visible' }}>
        {[0, 0.5, 1].map(t => {
          const y = PAD.t + chartH * (1 - t);
          return (
            <g key={t}>
              <line x1={PAD.l} x2={PAD.l + chartW} y1={y} y2={y} stroke={darkMode ? 'rgba(255,255,255,0.1)' : '#e2e8f0'} strokeWidth="1" strokeDasharray="3,3" />
              <text x={PAD.l - 4} y={y + 3} textAnchor="end" fontSize="8" fill={darkMode ? '#64748b' : '#94a3b8'}>{fmtM(maxVal * t)}</text>
            </g>
          );
        })}
        {data.map((d, i) => {
          const x = PAD.l + i * (chartW / data.length) + 4;
          const barH = maxVal > 0 ? Math.max(1, (d.value / maxVal) * chartH) : 0;
          const y = PAD.t + chartH - barH;
          return (
            <g key={i} className="group cursor-pointer">
              <rect
                x={x} y={y} width={barW} height={barH} rx="2"
                fill={d.color} opacity="0.85" className="hover:opacity-100 transition-opacity"
                onMouseEnter={(e) => {
                  setHoverData(d);
                }}
                onMouseMove={(e) => {
                  if (containerRef.current) {
                    const rect = containerRef.current.getBoundingClientRect();
                    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top - 10 });
                  }
                }}
                onMouseLeave={() => setHoverData(null)}
              />
              {d.label.split('\n').map((line, li) => {
                if (line.trim() === '') return null;
                return (
                  <text key={li} x={x + barW / 2} y={PAD.t + chartH + 11 + li * 9} textAnchor="middle" fontSize="6.5" fill={darkMode ? '#94a3b8' : '#64748b'} fontWeight="600">{line}</text>
                );
              })}
            </g>
          );
        })}
      </svg>
      {hoverData && (
        <div
          className="absolute z-50 bg-slate-900 text-white text-[10px] p-2 rounded shadow-lg pointer-events-none transform -translate-x-1/2 -translate-y-full whitespace-nowrap"
          style={{ left: mousePos.x, top: mousePos.y }}
        >
          <div className="font-bold mb-1 border-b border-slate-700 pb-1">{hoverData.label.replace('\n', ' ')}</div>
          <div>{hoverData.isRatio ? 'Loss Ratio' : 'Direct Loss'}: <span className="font-semibold text-orange-300">{hoverData.isRatio ? (hoverData.value).toFixed(4) + '%' : fmtFull(hoverData.value)}</span></div>
          {!hoverData.isRatio && (
            <div>Direct Loss (USD): <span className="font-semibold text-green-300">{formatUSD(hoverData.value)}</span></div>
          )}
          {expAsset > 0 && !hoverData.isRatio && (
            <div>Loss Ratio: <span className="font-semibold text-blue-300">{((hoverData.value / expAsset) * 100).toFixed(4)}%</span></div>
          )}
          {hoverData.isRatio && (
            <div>Value: <span className="font-semibold text-blue-300">{(hoverData.value).toFixed(6)}%</span></div>
          )}
        </div>
      )}
    </div>
  );
}

function DroughtSawahChartPanel({ selectedGroup, selectedCityFeature, onOpenDownload }) {
  const { darkMode } = useTheme();
  const [droughtData, setDroughtData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [zoomedChart, setZoomedChart] = React.useState(null); // { cc, rp } | null

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  React.useEffect(() => {
    if (selectedGroup !== 'kekeringan') return;
    setLoading(true);
    fetch(`${BACKEND_URL}/api/drought-sawah-loss`)
      .then(r => r.json())
      .then(data => setDroughtData(data))
      .catch(e => console.error('Drought sawah fetch failed:', e))
      .finally(() => setLoading(false));
  }, [selectedGroup, BACKEND_URL]);

  if (selectedGroup !== 'kekeringan') return null;

  const formatRupiah = (v) => {
    if (!v && v !== 0) return '-';
    if (v >= 1e12) return `Rp ${(v / 1e12).toFixed(1)} T`;
    if (v >= 1e9) return `Rp ${(v / 1e9).toFixed(0)} M`;
    if (v >= 1e6) return `Rp ${(v / 1e6).toFixed(0)} Jt`;
    return `Rp ${v.toLocaleString('id-ID')}`;
  };

  const yearColors = { loss_2022: '#2d6a4f', loss_2025: '#52b788', loss_2028: '#b7e4c7' };
  const yearLabels = { loss_2022: '2022', loss_2025: '2025', loss_2028: '2028' };
  const sortedRps = (droughtData?.return_periods || []).sort((a, b) => a - b);

  // ΓöÇΓöÇ PER-CITY MODE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  const selectedKota = selectedCityFeature?.properties?.nama_kota || selectedCityFeature?.properties?.id_kota;
  if (selectedCityFeature && selectedKota) {

    const years = [
      { key: 'loss_2022', label: 'Sawah 2022' },
      { key: 'loss_2025', label: 'Sawah 2025' },
      { key: 'loss_2028', label: 'Sawah 2028' },
    ];

    // NCC (green shades) and CC (blue shades) colors per RP
    const rpSeriesConfig = sortedRps.flatMap(rp => [
      { dataKey: `ncc_${rp}`, label: `NCC ${rp}TH`, color: ({ 25: '#1a7c50', 50: '#40916c', 100: '#74c69d', 250: '#b7e4c7' }[rp] || '#52b788') },
      { dataKey: `cc_${rp}`, label: `CC ${rp}TH`, color: ({ 25: '#1e3a8a', 50: '#1d4ed8', 100: '#60a5fa', 250: '#bfdbfe' }[rp] || '#93c5fd') },
    ]);

    // Building year-comparison data: [{ year:'Sawah 2022', ncc_25: v, cc_25: v, ncc_50: v, ... }]
    const yearComparisonData = years.map(({ key, label }) => {
      const row = { year: label };
      sortedRps.forEach(rp => {
        const rpKey = String(rp);
        const gRow = (droughtData?.gpm?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        const mRow = (droughtData?.mme?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        row[`ncc_${rp}`] = gRow?.[key] || 0;
        row[`cc_${rp}`] = mRow?.[key] || 0;
      });
      return row;
    });

    // Per-return-period data: [{ rp: '25 TH', ncc: v, cc: v }]
    const buildPerCityYear = (yearKey) =>
      sortedRps.map(rp => {
        const rpKey = String(rp);
        const gRow = (droughtData?.gpm?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        const mRow = (droughtData?.mme?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        return { rp: `${rp} TH`, ncc: gRow?.[yearKey] || 0, cc: mRow?.[yearKey] || 0 };
      });

    const tooltipContent = ({ active, payload, label }) => {
      if (!active || !payload?.length) return null;
      return (
        <div className="bg-white/95 backdrop-blur border border-slate-200 p-3 rounded-xl shadow-xl text-xs max-w-xs">
          <p className="font-bold text-slate-800 mb-2 border-b pb-1">{label}</p>
          {payload.map((entry, i) => (
            <div key={i} className="flex items-center justify-between gap-4 mb-0.5">
              <div className="flex items-center gap-1.5 text-slate-600">
                <span className="w-2 h-2 rounded-full" style={{ background: entry.fill || entry.color }} />
                <span className={darkMode ? 'text-gray-300' : 'text-slate-600'}>{entry.name}</span>
              </div>
              <span className="font-bold" style={{ color: entry.fill || entry.color }}>{formatRupiah(entry.value)}</span>
            </div>
          ))}
        </div>
      );
    };

    const renderYearComparison = (height = 170) => (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={yearComparisonData} margin={{ top: 4, right: 6, bottom: 6, left: -4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
          <XAxis dataKey="year" tick={{ fontSize: 7, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }} axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }} tickLine={false} />
          <YAxis tickFormatter={formatRupiah} tick={{ fontSize: 6, fill: darkMode ? '#64748b' : '#94a3b8' }} axisLine={false} tickLine={false} width={52} domain={[0, 'auto']} />
          <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241,245,249,0.4)' }} content={tooltipContent} />
          {rpSeriesConfig.map(({ dataKey, label, color }) => (
            <Bar key={dataKey} dataKey={dataKey} name={label} fill={color} radius={[2, 2, 0, 0]} maxBarSize={12} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );

    const renderGroupedBar = (data, height = 140) => (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 4, right: 6, bottom: 6, left: -4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis dataKey="rp" tick={{ fontSize: 7, fill: '#64748b', fontWeight: 700 }} axisLine={{ stroke: '#cbd5e1' }} tickLine={false} />
          <YAxis tickFormatter={formatRupiah} tick={{ fontSize: 6, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={52} />
          <Tooltip cursor={{ fill: 'rgba(241,245,249,0.5)' }} content={tooltipContent} />
          <Bar dataKey="ncc" name="Non CC" fill="#52b788" radius={[3, 3, 0, 0]} maxBarSize={26} />
          <Bar dataKey="cc" name="CC" fill="#60a5fa" radius={[3, 3, 0, 0]} maxBarSize={26} />
        </BarChart>
      </ResponsiveContainer>
    );

    const dotLegend = (
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {rpSeriesConfig.map(({ dataKey, label, color }) => (
          <div key={dataKey} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
            <span className="text-[6px] text-slate-600 font-medium">{label}</span>
          </div>
        ))}
      </div>
    );

    return (
      <div className="px-4 pt-3 pb-2 flex flex-col gap-3">
        <div className="text-[8px] font-extrabold text-slate-500 tracking-widest uppercase flex items-center gap-1">
          <BarChart2 size={10} className="text-green-600" />
          Direct Loss Sawah ΓÇö {selectedKota}
        </div>
        {loading && <div className="text-[9px] text-slate-400 py-4 text-center">Memuat data...</div>}

        {!loading && droughtData && (
          <>
            {/* ΓöÇΓöÇ Chart 1: Per Sawah Year (all RPs) ΓöÇΓöÇ */}
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className={`text-[7px] font-bold ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>Semua Return Period per Tahun Eksposur</span>
                <span className={`text-[6px] cursor-pointer transition-colors ${darkMode ? 'text-gray-500 hover:text-green-400' : 'text-slate-400 hover:text-green-600'}`}
                  onClick={() => setZoomedChart({ type: 'year' })}>Perbesar</span>
              </div>
              {dotLegend}
              <div className={`border rounded-lg p-1.5 shadow-sm cursor-pointer transition-colors ${darkMode ? 'bg-gray-800 border-gray-700 hover:border-green-500/50' : 'bg-white border-slate-200 hover:border-green-300'
                }`}
                onClick={() => setZoomedChart({ type: 'year' })}>
                {renderYearComparison(170)}
              </div>
            </div>

            {/* ΓöÇΓöÇ Charts 2-4: Per Year, NCC vs CC by RP ΓöÇΓöÇ */}
            <div className="flex gap-4 mt-1">
              <div className="flex items-center gap-1.5"><span className="w-3 h-2 rounded-sm bg-[#52b788]" /><span className="text-[7px] text-slate-600 font-semibold">Non CC</span></div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-2 rounded-sm bg-[#60a5fa]" /><span className="text-[7px] text-slate-600 font-semibold">Climate Change</span></div>
            </div>
            {years.map(({ key, label }) => {
              const data = buildPerCityYear(key);
              return (
                <div key={key} className="flex flex-col gap-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[7px] font-bold text-slate-600">{label}</span>
                    <span className="text-[6px] text-slate-400 cursor-pointer hover:text-green-600 transition-colors"
                      onClick={() => setZoomedChart({ type: 'rp', key, label })}>Perbesar</span>
                  </div>
                  <div className="bg-white border border-slate-200 rounded-lg p-1.5 shadow-sm cursor-pointer hover:border-green-300 transition-colors"
                    onClick={() => setZoomedChart({ type: 'rp', key, label })}>
                    {renderGroupedBar(data, 130)}
                  </div>
                </div>
              );
            })}
          </>
        )}

        {/* Zoomed modal */}
        {zoomedChart && createPortal(
          <div className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex items-center justify-center p-6" onClick={() => setZoomedChart(null)}>
            <div className={`rounded-2xl shadow-2xl p-6 w-full max-w-3xl ${darkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white'}`} onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-3 border-b pb-2">
                <h3 className={`font-bold text-sm ${darkMode ? 'text-white' : 'text-slate-800'}`}>
                  Direct Loss Sawah ΓÇö {selectedKota || 'Bali'} ΓÇö {zoomedChart.type === 'year' ? 'Perbandingan per Tahun' : zoomedChart.label}
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={async (e) => {
                      e.stopPropagation();
                      const el = document.getElementById('zoomed-drought-capture');
                      if (!el) return;
                      const canvas = await html2canvas(el, {
                        backgroundColor: darkMode ? '#111827' : '#ffffff',
                        scale: 2,
                        useCORS: true,
                        onclone: (clonedDoc) => {
                          const styleTags = clonedDoc.getElementsByTagName('style');
                          for (let style of styleTags) {
                            style.innerHTML = style.innerHTML.replace(/(oklch|oklab|lab)\([^)]+\)/g, '#00000000');
                          }
                        }
                      });
                      const link = document.createElement('a');
                      const title = `Direct Loss Sawah ΓÇö ${selectedKota || 'Bali'} ΓÇö ${zoomedChart.type === 'year' ? 'Comparison' : zoomedChart.label}`;
                      link.download = `${title.replace(/\s+/g, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.png`;
                      link.href = canvas.toDataURL('image/png');
                      link.click();
                    }}
                    className={`p-1.5 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800 text-blue-400' : 'hover:bg-blue-50 text-blue-600'}`}
                    title="Unduh Gambar"
                  >
                    <Download size={20} />
                  </button>
                  <button onClick={() => setZoomedChart(null)} className="text-slate-400 hover:text-slate-700 p-1.5"><X size={20} /></button>
                </div>
              </div>

              <div id="zoomed-drought-capture" className={`flex-1 p-2 ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
                <div className="mb-4">
                  <h3 className={`font-bold text-lg ${darkMode ? 'text-white' : 'text-slate-800'}`}>
                    Direct Loss Sawah ΓÇö {selectedKota || 'Bali'} ΓÇö {zoomedChart.type === 'year' ? 'Perbandingan per Tahun' : zoomedChart.label}
                  </h3>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Analisis Risiko Sawah Kekerigan</p>
                </div>
                {zoomedChart.type === 'year' ? (
                  <>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mb-4">{rpSeriesConfig.map(({ dataKey, label, color }) => (
                      <div key={dataKey} className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                        <span className="text-[8px] text-slate-600 font-medium">{label}</span>
                      </div>
                    ))}</div>
                    {renderYearComparison(400)}
                  </>
                ) : (
                  <>
                    <div className="flex gap-4 mb-4">
                      <div className="flex items-center gap-1.5"><span className="w-3 h-2.5 rounded-sm bg-[#52b788]" /><span className="text-[8px] text-slate-600 font-semibold">Non Climate Change</span></div>
                      <div className="flex items-center gap-1.5"><span className="w-3 h-2.5 rounded-sm bg-[#60a5fa]" /><span className="text-[8px] text-slate-600 font-semibold">Climate Change</span></div>
                    </div>
                    {renderGroupedBar(buildPerCityYear(zoomedChart.key), 400)}
                  </>
                )}
              </div>
            </div>
          </div>,
          document.body
        )}
      </div>
    );
  }

  // ΓöÇΓöÇ ALL-CITIES MODE (existing bar charts) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

  const renderChart = (data, height = 130) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 2, right: 4, bottom: 32, left: -4 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0fdf4" />
        <XAxis
          dataKey="kota"
          tick={{ fontSize: 5, fill: '#64748b', fontWeight: 700 }}
          axisLine={{ stroke: '#cbd5e1' }}
          tickLine={false}
          interval={0}
          angle={-35}
          textAnchor="end"
          height={42}
        />
        <YAxis
          tickFormatter={formatRupiah}
          tick={{ fontSize: 5.5, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip
          cursor={{ fill: 'rgba(209,250,229,0.4)' }}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            return (
              <div className="bg-white/95 backdrop-blur border border-green-200 p-3 rounded-xl shadow-xl text-xs">
                <p className="font-bold text-slate-800 mb-2 border-b border-slate-100 pb-1">{label}</p>
                {payload.map((entry, i) => (
                  <div key={i} className="flex items-center justify-between gap-6 mb-1">
                    <div className="flex items-center gap-1.5 text-slate-600">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ background: entry.fill }} />
                      <span>Sawah {yearLabels[entry.dataKey]}</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="font-bold text-green-800">{formatRupiah(entry.value)}</span>
                      <span className="text-[10px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                    </div>
                  </div>
                ))}
              </div>
            );
          }}
        />
        {Object.entries(yearColors).map(([key, color]) => (
          <Bar key={key} dataKey={key} fill={color} radius={[2, 2, 0, 0]} maxBarSize={14} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );

  const legend = (
    <div className="flex gap-3 flex-wrap mb-1">
      {Object.entries(yearColors).map(([key, color]) => (
        <div key={key} className="flex items-center gap-1">
          <span className="w-3 h-2 rounded-sm" style={{ background: color }} />
          <span className={`text-[7px] font-semibold ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>Sawah {yearLabels[key]}</span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="px-4 pt-3 pb-2 flex flex-col gap-3">
      <div className="text-[9px] font-bold text-slate-400 tracking-widest uppercase mb-1 flex items-center justify-between group">
        <div className="flex items-center gap-2">
          <BarChart2 size={10} className="text-green-600" />
          Direct Loss Sawah ΓÇö Kekeringan
        </div>
        <button
          onClick={() => onOpenDownload('map_chart')}
          className={`p-1 rounded-md transition-all opacity-0 group-hover:opacity-100 ${darkMode ? 'hover:bg-white/10 text-gray-400 hover:text-green-400' : 'hover:bg-slate-100 text-slate-400 hover:text-green-600'}`}
          title="Download Gambar"
        >
          <Download size={10} strokeWidth={2.5} />
        </button>
      </div>

      {loading && <div className="text-[9px] text-slate-400 py-4 text-center">Memuat data...</div>}

      {!loading && droughtData && (
        <>
          {/* RP dot legend */}
          {(() => {
            const rpColors = {
              ncc_25: '#1a7c50', cc_25: '#1e3a8a',
              ncc_50: '#40916c', cc_50: '#1d4ed8',
              ncc_100: '#74c69d', cc_100: '#60a5fa',
              ncc_250: '#b7e4c7', cc_250: '#bfdbfe',
            };
            const rpLabels = {
              ncc_25: 'NCC 25TH', cc_25: 'CC 25TH',
              ncc_50: 'NCC 50TH', cc_50: 'CC 50TH',
              ncc_100: 'NCC 100TH', cc_100: 'CC 100TH',
              ncc_250: 'NCC 250TH', cc_250: 'CC 250TH',
            };

            // Build per-year chart data: [{kota, ncc_25, cc_25, ncc_50, ...}]
            const buildData = (yearKey) => {
              const cityMap = {};
              sortedRps.forEach(rp => {
                ['gpm', 'mme'].forEach(cc => {
                  (droughtData[cc]?.[String(rp)] || []).forEach(row => {
                    if (!cityMap[row.kota]) cityMap[row.kota] = { kota: row.kota };
                    const k = `${cc === 'gpm' ? 'ncc' : 'cc'}_${rp}`;
                    cityMap[row.kota][k] = row[yearKey] || 0;
                  });
                });
              });
              return Object.values(cityMap).sort((a, b) => a.kota.localeCompare(b.kota));
            };

            const tooltipContent = ({ active, payload, label: l }) => {
              if (!active || !payload?.length) return null;
              return (
                <div className={`backdrop-blur border p-3 rounded-xl shadow-xl text-xs max-w-xs ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-green-200'}`}>
                  <p className={`font-bold border-b mb-2 pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{l}</p>
                  {payload.map((entry, i) => (
                    <div key={i} className="flex items-center justify-between gap-4 mb-0.5">
                      <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                        <span className="w-2 h-2 rounded-full" style={{ background: entry.fill }} />
                        <span>{rpLabels[entry.dataKey]}</span>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="font-bold" style={{ color: !darkMode ? entry.fill : '' }}>{formatRupiah(entry.value)}</span>
                        <span className="text-[10px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                      </div>
                    </div>
                  ))}
                </div>
              );
            };

            const renderMultiRpChart = (data, height = 130) => (
              <ResponsiveContainer width="100%" height={height}>
                <BarChart data={data} margin={{ top: 2, right: 4, bottom: 32, left: -4 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f0fdf4'} />
                  <XAxis dataKey="kota" tick={{ fontSize: 5, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }} axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }} tickLine={false} interval={0} angle={-35} textAnchor="end" height={42} />
                  <YAxis tickFormatter={formatRupiah} tick={{ fontSize: 5.5, fill: darkMode ? '#64748b' : '#94a3b8' }} axisLine={false} tickLine={false} width={48} />
                  <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(209,250,229,0.4)' }} content={tooltipContent} />
                  {Object.entries(rpColors).map(([key, color]) => (
                    <Bar key={key} dataKey={key} name={rpLabels[key]} fill={color} radius={[2, 2, 0, 0]} maxBarSize={9} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            );

            return (
              <>
                {/* Dot legend */}
                <div className="flex flex-wrap gap-x-3 gap-y-1 mb-1">
                  {Object.entries(rpColors).map(([key, color]) => (
                    <div key={key} className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
                      <span className={`text-[6px] font-medium ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>{rpLabels[key]}</span>
                    </div>
                  ))}
                </div>

                {/* 3 charts ΓÇö one per sawah year */}
                {[
                  { yearKey: 'loss_2022', label: 'Sawah 2022' },
                  { yearKey: 'loss_2025', label: 'Sawah 2025' },
                  { yearKey: 'loss_2028', label: 'Sawah 2028' },
                ].map(({ yearKey, label }) => {
                  const data = buildData(yearKey);
                  return (
                    <div key={yearKey} className="flex flex-col gap-0.5">
                      <div className="flex items-center justify-between">
                        <span className={`text-[7px] font-bold ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>{label}</span>
                        <span className={`text-[6px] cursor-pointer transition-colors ${darkMode ? 'text-gray-500 hover:text-green-400' : 'text-slate-400 hover:text-green-600'}`}
                          onClick={() => setZoomedChart({ yearKey, label, data, rpColors, rpLabels, tooltipContent, renderMultiRpChart })}>Perbesar</span>
                      </div>
                      <div className={`border rounded-lg p-1.5 shadow-sm cursor-pointer transition-colors ${darkMode ? 'bg-gray-800 border-gray-700 hover:border-green-500/50' : 'bg-white border-green-100/50 hover:border-green-300'}`}
                        onClick={() => setZoomedChart({ yearKey, label, data, rpColors, rpLabels, tooltipContent, renderMultiRpChart })}>
                        {data.length === 0
                          ? <div className="text-[8px] text-slate-400 text-center py-3">Tidak ada data</div>
                          : renderMultiRpChart(data, 130)
                        }
                      </div>
                    </div>
                  );
                })}
              </>
            );
          })()}
        </>
      )}

      {/* Zoomed modal */}
      {zoomedChart && createPortal(
        <div className={`fixed inset-0 z-[9999] backdrop-blur-sm flex items-center justify-center p-4 lg:p-12 animate-in fade-in duration-200 ${darkMode ? 'bg-black/60' : 'bg-slate-900/60'}`} onClick={() => setZoomedChart(null)}>
          <div className={`rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 ${darkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white'}`} onClick={e => e.stopPropagation()}>
            <div className={`px-6 py-4 flex items-center justify-between border-b ${darkMode ? 'border-gray-800 bg-gray-900/50' : 'border-slate-100 bg-slate-50/50'}`}>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${darkMode ? 'bg-green-900/30' : 'bg-green-100'}`}>
                  <BarChart2 size={24} className={darkMode ? 'text-green-400' : 'text-green-600'} />
                </div>
                <div>
                  <h3 className={`text-lg font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-800'}`}>Direct Loss Sawah ΓÇö {zoomedChart.label}</h3>
                  <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Semua Kota ΓÇö Kekeringan</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    const el = document.getElementById('zoomed-drought-capture');
                    if (!el) return;
                    const canvas = await html2canvas(el, {
                      backgroundColor: darkMode ? '#111827' : '#ffffff',
                      scale: 2,
                      useCORS: true,
                      onclone: (clonedDoc) => {
                        const styleTags = clonedDoc.getElementsByTagName('style');
                        for (let style of styleTags) {
                          style.innerHTML = style.innerHTML.replace(/(oklch|oklab|lab)\([^)]+\)/g, '#00000000');
                        }
                      }
                    });
                    const link = document.createElement('a');
                    const title = `Direct Loss Sawah ΓÇö ${zoomedChart.label} ΓÇö Kekeringan`;
                    link.download = `${title.replace(/\s+/g, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                  }}
                  className={`p-2 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800 text-blue-400' : 'hover:bg-blue-50 text-blue-600'}`}
                  title="Unduh Gambar"
                >
                  <Download size={24} />
                </button>
                <button onClick={() => setZoomedChart(null)} className={`p-2 rounded-full transition-colors ${darkMode ? 'hover:bg-gray-800 text-gray-400 hover:text-gray-200' : 'hover:bg-slate-100 text-slate-400 hover:text-slate-600'}`}>
                  <X size={24} />
                </button>
              </div>
            </div>

            <div id="zoomed-drought-capture" className={`flex-1 p-8 overflow-y-auto ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
              <div className="mb-6">
                <h3 className={`text-2xl font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-800'}`}>
                  Direct Loss Sawah ΓÇö {zoomedChart.label}
                </h3>
                <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Analisis Risiko Sawah Kekeringan ΓÇö Semua Kota</p>
              </div>
              <div className="flex flex-wrap gap-x-6 gap-y-2 mb-6">
                {zoomedChart.rpColors && Object.entries(zoomedChart.rpColors).map(([key, color]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ background: color }} />
                    <span className={`text-xs font-semibold ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>{zoomedChart.rpLabels?.[key]}</span>
                  </div>
                ))}
              </div>
              <div className="h-[500px] w-full">
                {zoomedChart.renderMultiRpChart?.(zoomedChart.data, 500)}
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

function FloodSawahChartPanel({ selectedCityFeature, floodData, selectedSawahYear, setSelectedSawahYear, onOpenDownload }) {
  const { darkMode } = useTheme();
  const [loading] = React.useState(false);
  const [zoomedChart, setZoomedChart] = React.useState(null);

  const YEAR_OPTIONS = [
    { key: 'loss_2022', label: '2022' },
    { key: 'loss_2025', label: '2025' },
    { key: 'loss_2028', label: '2028' },
  ];

  const selectedYearLabel = YEAR_OPTIONS.find(y => y.key === selectedSawahYear)?.label || '2022';

  const formatRupiah = (v) => {
    if (!v && v !== 0) return '-';
    if (v >= 1e12) return `Rp ${(v / 1e12).toFixed(1)} T`;
    if (v >= 1e9) return `Rp ${(v / 1e9).toFixed(0)} M`;
    if (v >= 1e6) return `Rp ${(v / 1e6).toFixed(0)} Jt`;
    return `Rp ${v.toLocaleString('id-ID')}`;
  };

  const sortedRps = (floodData?.return_periods || []).sort((a, b) => a - b);

  // NCC (blue shades for r), CC (orange/amber shades for rc)
  const nccColors = { 2: '#1e3a8a', 5: '#1d4ed8', 10: '#3b82f6', 25: '#60a5fa', 50: '#93c5fd', 100: '#bfdbfe', 250: '#dbeafe' };
  const ccColors = { 2: '#7c2d12', 5: '#c2410c', 10: '#ea580c', 25: '#f97316', 50: '#fb923c', 100: '#fdba74', 250: '#fed7aa' };


  // ΓöÇΓöÇ PER-CITY MODE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  const selectedKota = selectedCityFeature?.properties?.nama_kota || selectedCityFeature?.properties?.id_kota;
  if (selectedCityFeature && selectedKota) {
    const years = [
      { key: 'loss_2022', label: 'Sawah 2022' },
      { key: 'loss_2025', label: 'Sawah 2025' },
      { key: 'loss_2028', label: 'Sawah 2028' },
    ];

    const rpSeriesConfig = sortedRps.flatMap(rp => [
      { dataKey: `ncc_${rp}`, label: `NCC ${rp}TH`, color: nccColors[rp] || '#3b82f6' },
      { dataKey: `cc_${rp}`, label: `CC ${rp}TH`, color: ccColors[rp] || '#f97316' },
    ]);

    const buildPerCityYear = (yearKey) =>
      sortedRps.map(rp => {
        const rpKey = String(rp);
        const rRow = (floodData?.r?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        const rcRow = (floodData?.rc?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        return { rp: `${rp} TH`, ncc: rRow?.[yearKey] || 0, cc: rcRow?.[yearKey] || 0 };
      });

    const yearComparisonData = years.map(({ key, label }) => {
      const row = { year: label, key };
      sortedRps.forEach(rp => {
        const rpKey = String(rp);
        const rRow = (floodData?.r?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        const rcRow = (floodData?.rc?.[rpKey] || []).find(r => r.kota.toUpperCase() === selectedKota.toUpperCase());
        row[`ncc_${rp}`] = rRow?.[key] || 0;
        row[`cc_${rp}`] = rcRow?.[key] || 0;
      });
      return row;
    });

    const tooltipContent = ({ active, payload, label }) => {
      if (!active || !payload?.length) return null;
      return (
        <div className={`backdrop-blur border p-3 rounded-xl shadow-xl text-xs max-w-xs ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
          <p className={`font-bold border-b mb-2 pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
          {payload.map((entry, i) => (
            <div key={i} className="flex items-center justify-between gap-4 mb-0.5">
              <div className="flex items-center gap-1.5 text-slate-600">
                <span className="w-2 h-2 rounded-full" style={{ background: entry.fill || entry.color }} />
                <span className={darkMode ? 'text-gray-300' : 'text-slate-600'}>{entry.name}</span>
              </div>
              <div className="flex flex-col items-end">
                <span className="font-bold" style={{ color: !darkMode ? (entry.fill || entry.color) : '' }}>{formatRupiah(entry.value)}</span>
                <span className="text-[10px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
              </div>
            </div>
          ))}
        </div>
      );
    };

    const renderGroupedBar = (data, height = 130) => (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 4, right: 6, bottom: 6, left: -4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
          <XAxis dataKey="rp" tick={{ fontSize: 7, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }} axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }} tickLine={false} />
          <YAxis tickFormatter={formatRupiah} tick={{ fontSize: 6, fill: darkMode ? '#64748b' : '#94a3b8' }} axisLine={false} tickLine={false} width={52} />
          <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241,245,249,0.5)' }} content={tooltipContent} />
          <Bar dataKey="ncc" name="Non CC" fill="#3b82f6" radius={[3, 3, 0, 0]} maxBarSize={26} />
          <Bar dataKey="cc" name="CC" fill="#f97316" radius={[3, 3, 0, 0]} maxBarSize={26} />
        </BarChart>
      </ResponsiveContainer>
    );

    const perCity2022 = floodData ? buildPerCityYear('loss_2022') : [];
    const perCity2025 = floodData ? buildPerCityYear('loss_2025') : [];
    const perCity2028 = floodData ? buildPerCityYear('loss_2028') : [];
    const perCityMaps = { loss_2022: perCity2022, loss_2025: perCity2025, loss_2028: perCity2028 };

    return (
      <div className="px-4 pt-3 pb-2 flex flex-col gap-3">
        <div className={`text-[8px] font-extrabold tracking-widest uppercase flex items-center gap-1 ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
          <BarChart2 size={10} className={darkMode ? 'text-blue-400' : 'text-blue-600'} />
          Direct Loss Sawah ΓÇö {selectedKota}
        </div>

        {loading && <div className="text-[9px] text-slate-400 py-4 text-center">Memuat data...</div>}

        {!loading && floodData && (
          <div className="flex flex-col gap-3">
            {/* NCC vs CC legend */}
            <div className="flex gap-4 mb-1">
              <div className="flex items-center gap-1.5"><span className="w-3 h-2 rounded-sm bg-[#3b82f6]" /><span className={`text-[7px] font-semibold ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>Non CC</span></div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-2 rounded-sm bg-[#f97316]" /><span className={`text-[7px] font-semibold ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>Climate Change</span></div>
            </div>

            {/* Multiple charts for 2022, 2025, 2028 */}
            {YEAR_OPTIONS.map(({ key, label }) => {
              const isActive = selectedSawahYear === key;
              const data = perCityMaps[key];
              return (
                <div key={key} className={`flex flex-col gap-0.5 rounded-lg p-1.5 transition-colors ${isActive ? 'bg-white border border-green-100/50' : ''}`}>
                  <div className="flex items-center justify-between">
                    <span className={`text-[9px] font-bold ${isActive ? 'text-green-700' : 'text-slate-600'}`}>Sawah {label}</span>
                    <span className="text-[6px] text-slate-400 cursor-pointer hover:text-blue-600 transition-colors"
                      onClick={() => setZoomedChart({ label: `Sawah ${label} ΓÇö ${selectedKota}`, data })}>Perbesar</span>
                  </div>
                  <div className={`border rounded-lg p-1.5 shadow-sm cursor-pointer transition-colors ${darkMode ? 'bg-gray-800 border-gray-700 hover:border-blue-500/50' : 'bg-white border-slate-200 hover:border-blue-300'
                    }`}
                    onClick={() => setZoomedChart({ label: `Sawah ${label} ΓÇö ${selectedKota}`, data })}>
                    {renderGroupedBar(data, 130)}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Zoomed modal */}
        {zoomedChart && createPortal(
          <div className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex items-center justify-center p-6" onClick={() => setZoomedChart(null)}>
            <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-3xl" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-slate-800 text-sm">{zoomedChart.label}</h3>
                <button onClick={() => setZoomedChart(null)} className="text-slate-400 hover:text-slate-700"><X size={18} /></button>
              </div>
              <div className="flex gap-4 mb-4">
                <div className="flex items-center gap-1.5"><span className="w-3 h-2.5 rounded-sm bg-[#3b82f6]" /><span className="text-[8px] text-slate-600 font-semibold">Non Climate Change</span></div>
                <div className="flex items-center gap-1.5"><span className="w-3 h-2.5 rounded-sm bg-[#f97316]" /><span className="text-[8px] text-slate-600 font-semibold">Climate Change</span></div>
              </div>
              {renderGroupedBar(zoomedChart.data, 400)}
            </div>
          </div>,
          document.body
        )}
      </div>
    );
  }

  // ΓöÇΓöÇ ALL-CITIES MODE ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
  const rpColors = {};
  const rpLabels = {};
  sortedRps.forEach(rp => {
    rpColors[`ncc_${rp}`] = nccColors[rp] || '#3b82f6';
    rpColors[`cc_${rp}`] = ccColors[rp] || '#f97316';
    rpLabels[`ncc_${rp}`] = `NCC ${rp}TH`;
    rpLabels[`cc_${rp}`] = `CC ${rp}TH`;
  });

  const buildAllCitiesData = (yearKey) => {
    if (!floodData) return [];
    const cityMap = {};
    sortedRps.forEach(rp => {
      ['r', 'rc'].forEach(cc => {
        (floodData[cc]?.[String(rp)] || []).forEach(row => {
          if (!cityMap[row.kota]) cityMap[row.kota] = { kota: row.kota };
          const k = `${cc === 'r' ? 'ncc' : 'cc'}_${rp}`;
          cityMap[row.kota][k] = row[yearKey] || 0;
        });
      });
    });
    return Object.values(cityMap).sort((a, b) => a.kota.localeCompare(b.kota));
  };

  const tooltipAllCities = ({ active, payload, label: l }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className={`backdrop-blur border p-3 rounded-xl shadow-xl text-xs max-w-xs ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-blue-200'}`}>
        <p className={`font-bold border-b mb-2 pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{l}</p>
        {payload.map((entry, i) => (
          <div key={i} className="flex items-center justify-between gap-4 mb-0.5">
            <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
              <span className="w-2 h-2 rounded-full" style={{ background: entry.fill }} />
              <span>{rpLabels[entry.dataKey]}</span>
            </div>
            <div className="flex flex-col items-end">
              <span className="font-bold" style={{ color: !darkMode ? entry.fill : '' }}>{formatRupiah(entry.value)}</span>
              <span className="text-[10px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderMultiRpChart = (data, height = 130) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 2, right: 4, bottom: 32, left: -4 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#eff6ff'} />
        <XAxis dataKey="kota" tick={{ fontSize: 5, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }} axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }} tickLine={false} interval={0} angle={-35} textAnchor="end" height={42} />
        <YAxis tickFormatter={formatRupiah} tick={{ fontSize: 5.5, fill: darkMode ? '#64748b' : '#94a3b8' }} axisLine={false} tickLine={false} width={48} domain={[0, 'auto']} />
        <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(219,234,254,0.4)' }} content={tooltipAllCities} />
        {Object.entries(rpColors).map(([key, color]) => (
          <Bar key={key} dataKey={key} name={rpLabels[key]} fill={color} radius={[2, 2, 0, 0]} maxBarSize={9} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );

  const allCitiesMaps = {
    loss_2022: buildAllCitiesData('loss_2022'),
    loss_2025: buildAllCitiesData('loss_2025'),
    loss_2028: buildAllCitiesData('loss_2028')
  };

  return (
    <div className="px-4 pt-3 pb-2 flex flex-col gap-3">
      <div className="text-[9px] font-bold text-slate-400 tracking-widest uppercase mb-1 flex items-center justify-between group">
        <div className="flex items-center gap-2">
          <BarChart2 size={10} className={darkMode ? 'text-blue-400' : 'text-blue-600'} />
          Direct Loss Sawah ΓÇö Banjir
        </div>
        <button
          onClick={() => onOpenDownload('map_chart')}
          className={`p-1 rounded-md transition-all opacity-0 group-hover:opacity-100 ${darkMode ? 'hover:bg-white/10 text-gray-400 hover:text-blue-400' : 'hover:bg-slate-100 text-slate-400 hover:text-blue-600'}`}
          title="Download Gambar"
        >
          <Download size={10} strokeWidth={2.5} />
        </button>
      </div>

      {loading && <div className="text-[9px] text-slate-400 py-4 text-center">Memuat data...</div>}

      {!loading && floodData && (
        <div className="flex flex-col gap-3">
          {/* Legend dots */}
          <div className="flex flex-wrap gap-x-3 gap-y-1 mb-1">
            {Object.entries(rpColors).map(([key, color]) => (
              <div key={key} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
                <span className={`text-[6px] font-medium ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>{rpLabels[key]}</span>
              </div>
            ))}
          </div>

          {/* Multiple charts for 2022, 2025, 2028 */}
          {YEAR_OPTIONS.map(({ key, label }) => {
            const isActive = selectedSawahYear === key;
            const data = allCitiesMaps[key];
            return (
              <div key={key} className={`flex flex-col gap-0.5 rounded-lg p-1.5 transition-colors ${isActive ? (darkMode ? 'bg-blue-900/20 border border-blue-800/50' : 'bg-white border border-green-100/50') : ''}`}>
                <div className="flex items-center justify-between">
                  <span className={`text-[9px] font-bold ${isActive ? (darkMode ? 'text-blue-400' : 'text-green-700') : (darkMode ? 'text-gray-400' : 'text-slate-600')}`}>Sawah {label} ΓÇö Semua Kota</span>
                  <span className={`text-[6px] cursor-pointer transition-colors ${darkMode ? 'text-gray-500 hover:text-blue-400' : 'text-slate-400 hover:text-blue-600'}`}
                    onClick={() => setZoomedChart({ label: `Sawah ${label} ΓÇö Semua Kota`, data })}>Perbesar</span>
                </div>
                <div className={`border rounded-lg p-1.5 shadow-sm cursor-pointer transition-colors ${darkMode ? 'bg-gray-800/40 border-gray-700 hover:border-blue-500/50' : 'bg-white border-blue-100 hover:border-blue-300'}`}
                  onClick={() => setZoomedChart({ label: `Sawah ${label} ΓÇö Semua Kota`, data })}>
                  {renderMultiRpChart(data, 160)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Zoomed modal */}
      {zoomedChart && createPortal(
        <div className={`fixed inset-0 z-[9999] backdrop-blur-sm flex items-center justify-center p-4 lg:p-12 animate-in fade-in duration-200 ${darkMode ? 'bg-black/60' : 'bg-slate-900/60'}`} onClick={() => setZoomedChart(null)}>
          <div className={`rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 ${darkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white'}`} onClick={e => e.stopPropagation()}>
            <div className={`px-6 py-4 flex items-center justify-between border-b ${darkMode ? 'border-gray-800 bg-gray-900/50' : 'border-slate-100 bg-slate-50/50'}`}>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${darkMode ? 'bg-blue-900/30' : 'bg-blue-100'}`}>
                  <BarChart2 size={24} className={darkMode ? 'text-blue-400' : 'text-blue-600'} />
                </div>
                <div>
                  <h3 className={`text-lg font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-800'}`}>Direct Loss Sawah ΓÇö {zoomedChart.label}</h3>
                  <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Semua Kota ΓÇö Banjir</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    const el = document.getElementById('zoomed-flood-capture');
                    if (!el) return;
                    const canvas = await html2canvas(el, {
                      backgroundColor: darkMode ? '#111827' : '#ffffff',
                      scale: 2,
                      useCORS: true,
                      onclone: (clonedDoc) => {
                        const styleTags = clonedDoc.getElementsByTagName('style');
                        for (let style of styleTags) {
                          style.innerHTML = style.innerHTML.replace(/(oklch|oklab|lab)\([^)]+\)/g, '#00000000');
                        }
                      }
                    });
                    const link = document.createElement('a');
                    const title = `Direct Loss Sawah ΓÇö ${zoomedChart.label} ΓÇö Banjir`;
                    link.download = `${title.replace(/\s+/g, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                  }}
                  className={`p-2 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800 text-blue-400' : 'hover:bg-blue-50 text-blue-600'}`}
                  title="Unduh Gambar"
                >
                  <Download size={24} />
                </button>
                <button onClick={() => setZoomedChart(null)} className={`p-2 rounded-full transition-colors ${darkMode ? 'hover:bg-gray-800 text-gray-400 hover:text-gray-200' : 'hover:bg-slate-100 text-slate-400 hover:text-slate-600'}`}>
                  <X size={24} />
                </button>
              </div>
            </div>

            <div id="zoomed-flood-capture" className={`flex-1 p-8 overflow-y-auto ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
              <div className="mb-6">
                <h3 className={`text-2xl font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-800'}`}>
                  Direct Loss Sawah ΓÇö {zoomedChart.label}
                </h3>
                <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Analisis Risiko Sawah Banjir ΓÇö Semua Kota</p>
              </div>
              <div className="flex flex-wrap gap-x-6 gap-y-2 mb-6">
                {Object.entries(rpColors).map(([key, color]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ background: color }} />
                    <span className={`text-xs font-semibold ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>{rpLabels[key]}</span>
                  </div>
                ))}
              </div>
              <div className="h-[500px] w-full">
                {renderMultiRpChart(zoomedChart.data, 500)}
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}




function DirectLossChartPanel({ boundaryData, selectedCityFeature, selectedGroup, onOpenTable, onOpenDownload }) {
  const { darkMode } = useTheme();
  const [zoomedChart, setZoomedChart] = useState(null);

  // Kekeringan uses its own dedicated sawah chart, not boundary data

  const rpsConfig = React.useMemo(() => {
    if (selectedGroup === 'earthquake') return ['100', '200', '250', '500', '1000'].map(rp => ({ key: `pga_${rp}`, label: `PGA ${rp}` }));
    if (selectedGroup === 'tsunami') return [{ key: 'inundansi', label: 'Inundansi' }];
    if (selectedGroup === 'banjir') return ['2', '5', '10', '25', '50', '100', '250'].flatMap(rp => [{ key: `r_${rp}`, label: `R ${rp}` }, { key: `rc_${rp}`, label: `RC ${rp}` }]);
    return [];
  }, [selectedGroup]);

  const cityChartData = React.useMemo(() => {
    if (selectedCityFeature) return [];
    if (!boundaryData?.features) return [];

    const getHazardVal = (feat, group, key, exposureKey) => {
      if (group === 'earthquake') {
        const dlExp = feat.properties.dl_exposure || {};
        let catData = dlExp[exposureKey] || {};
        if (typeof catData === 'string') {
          try { catData = JSON.parse(catData); } catch { catData = {}; }
        }
        const val = catData[key] || 0;
        return val * 100; // Return as percentage for chart
      }
      return feat.properties[`dl_sum_${key}`] || 0;
    };

    // For city comparison, we're comparing 'total' exposure
    const exposureKey = 'total';

    return boundaryData.features.map(f => {
      const item = {
        kota: f.properties.nama_kota || f.properties.id_kota,
        isRatio: selectedGroup === 'earthquake'
      };

      let valSum = 0;
      rpsConfig.forEach(rp => {
        const val = getHazardVal(f, selectedGroup, rp.key, exposureKey);
        item[rp.key] = val;
        valSum += val;
      });
      item._sortVal = rpsConfig.length > 0 ? valSum / rpsConfig.length : 0;

      return item;
    }).sort((a, b) => b._sortVal - a._sortVal);
  }, [boundaryData, selectedGroup, rpsConfig]);

  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b', '#f97316', '#84cc16', '#fb7185', '#2dd4bf', '#a3e635', '#c084fc'];

  let totalCount = 0;
  let totalAsset = 0;

  if (selectedCityFeature) {
    totalCount = selectedCityFeature.properties.count_total || 0;
    totalAsset = selectedCityFeature.properties.total_asset_total || 0;
  } else {
    totalCount = boundaryData.features.reduce((sum, f) => sum + (f.properties.count_total || 0), 0);
    totalAsset = boundaryData.features.reduce((sum, f) => sum + (f.properties.total_asset_total || 0), 0);

    // Manual Gempa additions are now handled centrally in the enriched boundary properties
  }

  // Add manual Gempa data for Total
  if (selectedGroup === 'earthquake') {
    const cityName = selectedCityFeature ? (selectedCityFeature.properties.nama_kota || selectedCityFeature.properties.id_kota) : null;
    const manualAdd = getManualGempaAddition(cityName, 'total');
    totalCount += manualAdd.count;
    totalAsset += manualAdd.asset;
  }

  const formatRupiah = (v) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);

  // Retrieve values across all RPs for a specific exposure group (or 'total')
  const getValuesForHazard = (exposureKey) => {
    const getValue = (rpSuffix) => {
      const metric = `dl_sum_${rpSuffix}`;

      const getLoss = (feature) => {
        if (exposureKey === 'total') return feature.properties[metric] || 0;
        let dlExp = feature.properties.dl_exposure || {};
        if (typeof dlExp === 'string') {
          try { dlExp = JSON.parse(dlExp); } catch { dlExp = {}; }
        }
        let expData = dlExp[exposureKey] || {};
        if (typeof expData === 'string') {
          try { expData = JSON.parse(expData); } catch { expData = {}; }
        }
        if (process.env.NODE_ENV !== 'production' && feature.properties.id_kota === 'BADUNG') {
          console.log('[DL DATA]', exposureKey, rpSuffix, expData[rpSuffix], typeof expData[rpSuffix]);
        }
        return expData[rpSuffix] || 0;
      };

      if (selectedCityFeature) {
        return getLoss(selectedCityFeature);
      } else {
        return boundaryData.features.reduce((sum, f) => sum + getLoss(f), 0);
      }
    };

    if (selectedGroup === 'earthquake') {
      const rps = ['100', '200', '250', '500', '1000'];

      const getRatio = (feat) => {
        let dlExp = feat.properties.dl_exposure || {};
        if (typeof dlExp === 'string') {
          try { dlExp = JSON.parse(dlExp); } catch { dlExp = {}; }
        }
        const catData = dlExp[exposureKey] || {};
        if (typeof catData === 'string') {
          try { return JSON.parse(catData); } catch { return {}; }
        }
        return catData || {};
      };

      let sourceRatios = {};
      if (selectedCityFeature) {
        sourceRatios = getRatio(selectedCityFeature);
      } else {
        // Use provincial aggregate if available
        sourceRatios = (boundaryData.provincial_gempa_loss_ratios && boundaryData.provincial_gempa_loss_ratios[exposureKey]) || {};
      }

      return rps.map(rp => ({
        label: `${rp} TH`,
        color: '#ef4444',
        value: (sourceRatios[`pga_${rp}`] || 0) * 100,
        isRatio: true
      }));
    } else if (selectedGroup === 'tsunami') {
      return [{ label: `Inundansi`, color: '#8b5cf6', value: getValue('inundansi') }];
    } else if (selectedGroup === 'banjir') {
      const rps = ['2', '5', '10', '25', '50', '100', '250'];
      let result = [];
      rps.forEach(rp => {
        result.push({ label: `${rp}\nTH`, color: '#3b82f6', value: getValue(`r_${rp}`) }); // R
        result.push({ label: ` \n `, color: '#f97316', value: getValue(`rc_${rp}`) }); // RC
      });
      return result;
    }
    return [];
  };

  const exposureChartData = React.useMemo(() => {
    if (!boundaryData?.features) return [];

    return EXPOSURE_GROUPS.filter(g => g.exp !== 'total' && !(g.gempaOnly && selectedGroup !== 'earthquake')).map(group => {
      const item = { exposure_name: group.label };

      rpsConfig.forEach(rp => {
        if (selectedGroup === 'earthquake') {
          if (selectedCityFeature) {
            let dlExp = selectedCityFeature.properties.dl_exposure || {};
            if (typeof dlExp === 'string') { try { dlExp = JSON.parse(dlExp); } catch { dlExp = {}; } }
            const catData = dlExp[group.exp] || {};
            item[rp.key] = (catData[rp.key] || 0) * 100;
          } else {
            // Use provincial aggregate
            const provExp = (boundaryData.provincial_gempa_loss_ratios && boundaryData.provincial_gempa_loss_ratios[group.exp]) || {};
            item[rp.key] = (provExp[rp.key] || 0) * 100;
          }
        } else {
          let sum = 0;
          boundaryData.features.forEach(feature => {
            let dlExp = feature.properties.dl_exposure || {};
            if (typeof dlExp === 'string') {
              try { dlExp = JSON.parse(dlExp); } catch { dlExp = {}; }
            }
            let expData = dlExp[group.exp] || {};
            if (typeof expData === 'string') {
              try { expData = JSON.parse(expData); } catch { expData = {}; }
            }
            sum += (expData[rp.key] || 0);
          });
          item[rp.key] = sum;
        }
      });

      return item;
    });
  }, [boundaryData, rpsConfig]);

  if (selectedGroup === 'kekeringan') return null;
  if (!boundaryData?.features?.length || !selectedGroup) return null;

  const renderCharts = (groups) => {
    // Collect all data first to find the global max for scaling
    const groupData = groups.map(group => {
      const data = getValuesForHazard(group.exp);
      const max = Math.max(...data.map(d => d.value), 0);
      return { ...group, data, max };
    });

    const globalMax = Math.max(...groupData.map(g => g.max), 1);

    return groupData.map(group => {
      if (group.data.length === 0) return null;

      let expCount = 0;
      let expAsset = 0;
      if (selectedCityFeature) {
        expCount = selectedCityFeature.properties[`count_${group.exp}`] || 0;
        expAsset = selectedCityFeature.properties[`total_asset_${group.exp}`] || 0;
      } else {
        expCount = boundaryData.features.reduce((sum, f) => sum + (f.properties[`count_${group.exp}`] || 0), 0);
        expAsset = boundaryData.features.reduce((sum, f) => sum + (f.properties[`total_asset_${group.exp}`] || 0), 0);

        // Manual Gempa additions are already handled in the enriched boundary properties
      }

      // Manual Gempa additions are now handled centrally in CogHazardMap aggregator

      return (
        <div key={group.exp} className={`rounded-xl p-3 mb-3 border relative transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700/50 shadow-lg' : 'bg-white border-slate-100/50'}`}>
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className={`text-[10px] font-bold tracking-wide text-center ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>{group.label}</div>
            {group.exp !== 'total' && (
              <button
                onClick={() => onOpenTable && onOpenTable(group.layerKey)}
                title="Lihat Data Tabel"
                className={`transition-all rounded p-1 shadow-sm border ${darkMode ? 'text-gray-400 hover:text-blue-400 bg-gray-700 border-gray-600 hover:border-blue-900/50' : 'text-slate-400 hover:text-blue-500 bg-white hover:bg-blue-50 border-slate-200 hover:border-blue-200'}`}
              >
                <TableIcon size={12} strokeWidth={2.5} />
              </button>
            )}
          </div>
          {group.exp !== 'total' && expCount > 0 && (
            <div className={`flex justify-between items-center text-[9px] mb-3 px-2 border-b pb-2 ${darkMode ? 'border-gray-700' : 'border-slate-200'}`}>
              <div className="flex flex-col">
                <span className={`uppercase tracking-wider font-semibold ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Bangunan</span>
                <span className={`font-bold ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>{expCount.toLocaleString('id-ID')}</span>
              </div>
              <div className="flex flex-col text-right">
                <span className={`uppercase tracking-wider font-semibold ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Nilai Aset</span>
                <div className="flex flex-col items-end">
                  <span className={`font-bold ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>{formatRupiah(expAsset)}</span>
                  <span className="text-[8px] text-green-600 font-bold">({formatUSD(expAsset)})</span>
                </div>
              </div>
            </div>
          )}
          <div className="flex justify-center flex-wrap gap-4 overflow-visible">
            <MiniBarChart data={group.data} maxVal={group.max > 0 ? group.max : 1} expAsset={expAsset} />
          </div>
        </div>
      );
    });
  };

  return (
    <div className={`px-4 pb-4 border-t flex flex-col items-center ${darkMode ? 'border-gray-800' : 'border-slate-100'}`}>
      <div className={`w-full border rounded-xl p-3 mt-3 mb-1 shadow-sm flex justify-between items-center transition-all ${darkMode ? 'bg-gray-800/60 border-gray-700 shadow-black/20' : 'bg-white border-slate-100'}`}>
        <div className="flex flex-col">
          <span className={`text-[8px] font-bold tracking-widest uppercase ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Total Bangunan</span>
          <span className={`text-[12px] font-extrabold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{totalCount.toLocaleString('id-ID')}</span>
        </div>
        <div className={`w-[1px] h-6 ${darkMode ? 'bg-gray-700' : 'bg-slate-200'}`}></div>
        <div className="flex flex-col text-right">
          <span className={`text-[8px] font-bold tracking-widest uppercase ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Total Nilai Aset</span>
          <div className="flex flex-col items-end">
            <span className={`text-[12px] font-extrabold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{formatRupiah(totalAsset)}</span>
            <span className="text-[10px] text-green-600 font-bold">({formatUSD(totalAsset)})</span>
          </div>
        </div>
      </div>

      {/* City Comparison Chart (Only when 'Semua Kota') */}
      {!selectedCityFeature && cityChartData.length > 0 && (
        <div className={`w-full h-[180px] border rounded-xl p-2 mt-2 shadow-sm relative z-0 flex flex-col transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700 shadow-black/20' : 'bg-white border-slate-200'}`}>
          <div className="text-[8px] font-extrabold tracking-widest uppercase mb-1 flex items-center justify-between">
            <div className={`flex items-center gap-1 ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
              <BarChart2 size={10} className={darkMode ? 'text-blue-400' : 'text-blue-500'} />
              Perbandingan Direct Loss Antar Kota
            </div>
            <div className="flex items-center gap-2">
              <span className={darkMode ? 'text-gray-500' : 'text-slate-400'}>Klik untuk perbesar</span>
              <button
                onClick={(e) => { e.stopPropagation(); onOpenDownload('map_chart'); }}
                className={`p-1 rounded-md transition-all ${darkMode ? 'hover:bg-white/10 text-gray-400 hover:text-blue-400' : 'hover:bg-slate-100 text-slate-400 hover:text-blue-600'}`}
                title="Download Gambar"
              >
                <Download size={10} strokeWidth={2.5} />
              </button>
            </div>
          </div>
          <div
            id="city-comparison-chart"
            className={`flex-1 w-full relative cursor-pointer group rounded border transition-colors ${darkMode ? 'border-transparent hover:border-blue-900/50 hover:bg-gray-700/50' : 'border-transparent hover:border-blue-200 hover:bg-slate-50/50'}`}
            onClick={() => setZoomedChart({ type: 'city', title: 'Perbandingan Direct Loss Antar Kota', data: cityChartData, xKey: "kota" })}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cityChartData} margin={{ top: 5, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
                <XAxis
                  dataKey="kota"
                  tick={{ fontSize: 6, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }}
                  axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }}
                  tickLine={false}
                  interval={0}
                  angle={-35}
                  textAnchor="end"
                  height={40}
                />
                <YAxis
                  tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                  tick={{ fontSize: 7, fill: darkMode ? '#64748b' : '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 'auto']}
                />
                <Tooltip
                  cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }}
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className={`backdrop-blur border p-2 rounded-lg shadow-lg ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                          <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                          <div className="flex flex-col gap-1">
                            {payload.map((entry, index) => (
                              <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
                                <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                  <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                                  <span>{entry.name}</span>
                                </div>
                                <div className="flex flex-col items-end">
                                  <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                  <span className="text-[7px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {rpsConfig.map((col, idx) => (
                  <Bar key={col.key} dataKey={col.key} name={col.label} fill={colors[idx % colors.length]} radius={[2, 2, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 flex items-center justify-center transition-all opacity-0 group-hover:opacity-100 backdrop-blur-[1px]">
              <div className="bg-slate-900/80 text-white rounded-full p-2 shadow-lg transform scale-95 group-hover:scale-100 transition-all">
                <Maximize2 size={16} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Exposure Comparison Chart */}
      {exposureChartData.length > 0 && (
        <div className={`w-full h-[180px] border rounded-xl p-2 mt-2 shadow-sm relative z-0 flex flex-col transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700 shadow-black/20' : 'bg-white border-slate-200'}`}>
          <div className="text-[8px] font-extrabold tracking-widest uppercase mb-1 flex items-center justify-between">
            <div className={`flex items-center gap-1 ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
              <BarChart2 size={10} className={darkMode ? 'text-orange-400' : 'text-orange-500'} />
              Perbandingan Direct Loss Antar Eksposur
            </div>
            <div className="flex items-center gap-2">
              <span className={darkMode ? 'text-gray-500' : 'text-slate-400'}>Klik untuk perbesar</span>
              <button
                onClick={(e) => { e.stopPropagation(); onOpenDownload('map_chart'); }}
                className={`p-1 rounded-md transition-all ${darkMode ? 'hover:bg-white/10 text-gray-400 hover:text-orange-400' : 'hover:bg-slate-100 text-slate-400 hover:text-orange-600'}`}
                title="Download Gambar"
              >
                <Download size={10} strokeWidth={2.5} />
              </button>
            </div>
          </div>
          <div
            id="exposure-comparison-chart"
            className={`flex-1 w-full relative cursor-pointer group rounded border transition-colors ${darkMode ? 'border-transparent hover:border-orange-900/50 hover:bg-gray-700/50' : 'border-transparent hover:border-orange-200 hover:bg-slate-50/50'}`}
            onClick={() => setZoomedChart({ type: 'exposure', title: 'Perbandingan Direct Loss Antar Eksposur', data: exposureChartData, xKey: "exposure_name" })}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={exposureChartData} margin={{ top: 5, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
                <XAxis
                  dataKey="exposure_name"
                  tick={{ fontSize: 6, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }}
                  axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }}
                  tickLine={false}
                  interval={0}
                  angle={-25}
                  textAnchor="end"
                  height={40}
                />
                <YAxis
                  tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                  tick={{ fontSize: 7, fill: darkMode ? '#64748b' : '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 'auto']}
                />
                <Tooltip
                  cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }}
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className={`backdrop-blur border p-2 rounded-lg shadow-lg ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                          <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                          <div className="flex flex-col gap-1">
                            {payload.map((entry, index) => (
                              <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
                                <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                  <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                                  <span>{entry.name}</span>
                                </div>
                                <div className="flex flex-col items-end">
                                  <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                  <span className="text-[7px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {rpsConfig.map((col, idx) => (
                  <Bar key={col.key} dataKey={col.key} name={col.label} fill={colors[idx % colors.length]} radius={[2, 2, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 flex items-center justify-center transition-all opacity-0 group-hover:opacity-100 backdrop-blur-[1px]">
              <div className="bg-slate-900/80 text-white rounded-full p-2 shadow-lg transform scale-95 group-hover:scale-100 transition-all">
                <Maximize2 size={16} />
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedGroup !== 'earthquake' && (
        <div className="text-[9px] font-bold text-slate-400 tracking-widest uppercase my-3 w-full flex justify-between items-center group">
          <div className="flex items-center gap-2">
            <span>Distribusi Direct Loss per Eksposur</span>
            <button
              onClick={() => onOpenDownload('map_chart')}
              className={`p-1 rounded-md transition-all opacity-0 group-hover:opacity-100 ${darkMode ? 'hover:bg-white/10 text-gray-400 hover:text-blue-400' : 'hover:bg-slate-100 text-slate-400 hover:text-blue-600'}`}
              title="Download Gambar"
            >
              <Download size={10} strokeWidth={2.5} />
            </button>
          </div>
          {selectedGroup === 'banjir' && (
            <div className="flex gap-2 text-[8px] font-semibold text-slate-500">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-[2px] bg-[#3b82f6]"></span> R</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-[2px] bg-[#f97316]"></span> RC</span>
            </div>
          )}
        </div>
      )}
      <div className="flex flex-col w-full px-1 pt-1 pb-2">
        {renderCharts(EXPOSURE_GROUPS.filter(g => {
          if (selectedGroup === 'earthquake') {
            return g.exp !== 'total' && !g.gempaOnly;
          }
          return !g.gempaOnly;
        }))}
      </div>

      {/* Zoomed Chart Modal */}
      {zoomedChart && typeof document !== 'undefined' && createPortal(
        <div className={`fixed inset-0 z-[9999] backdrop-blur-sm flex items-center justify-center p-4 lg:p-12 animate-in fade-in duration-200 ${darkMode ? 'bg-black/60' : 'bg-slate-900/60'}`}>
          <div className={`rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
            {/* Modal Header */}
            <div className={`px-6 py-4 flex items-center justify-between border-b ${darkMode ? 'border-gray-800 bg-gray-900/50' : 'border-slate-100 bg-slate-50/50'}`}>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${darkMode ? 'bg-blue-900/30' : 'bg-blue-100'}`}>
                  <BarChart2 size={24} className={darkMode ? 'text-blue-400' : 'text-blue-600'} />
                </div>
                <div>
                  <h3 className={`text-lg font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-800'}`}>{zoomedChart.title}</h3>
                  <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Semua Return Period</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    const el = document.getElementById(zoomedChart.type === 'aal' ? 'zoomed-aal-capture' : 'zoomed-direct-loss-capture');
                    if (!el) return;
                    const canvas = await html2canvas(el, {
                      backgroundColor: darkMode ? '#111827' : '#ffffff',
                      scale: 2,
                      useCORS: true,
                      onclone: (clonedDoc) => {
                        const styleTags = clonedDoc.getElementsByTagName('style');
                        for (let style of styleTags) {
                          style.innerHTML = style.innerHTML.replace(/(oklch|oklab|lab)\([^)]+\)/g, '#00000000');
                        }
                      }
                    });
                    const link = document.createElement('a');
                    link.download = `${zoomedChart.title.replace(/\s+/g, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                  }}
                  className={`p-2 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800 text-blue-400' : 'hover:bg-blue-50 text-blue-600'}`}
                  title="Unduh Gambar"
                >
                  <Download size={24} />
                </button>
                <button
                  onClick={() => setZoomedChart(null)}
                  className={`p-2 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800' : 'hover:bg-slate-200'}`}
                  title="Tutup Modal"
                >
                  <X size={24} className={`${darkMode ? 'text-gray-500 group-hover:text-gray-300' : 'text-slate-400 group-hover:text-slate-600'}`} />
                </button>
              </div>
            </div>

            <div id={zoomedChart.type === 'aal' ? 'zoomed-aal-capture' : 'zoomed-direct-loss-capture'} className={`flex-1 w-full p-6 relative flex flex-col ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
              {selectedGroup !== 'earthquake' && (
                <div className="mb-4 text-left">
                  <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{zoomedChart.title}</h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>{zoomedChart.type === 'aal' ? 'Analisis Average Annual Loss (AAL)' : 'Analisis Risiko Direct Loss ΓÇö Semua Return Period'}</p>
                </div>
              )}

              <div className="flex-1 min-h-0 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={zoomedChart.data} margin={{ top: 20, right: 30, bottom: 60, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#e2e8f0'} />
                    <XAxis
                      dataKey={zoomedChart.xKey}
                      tick={{ fontSize: 11, fill: darkMode ? '#94a3b8' : '#475569', fontWeight: 700 }}
                      axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1', strokeWidth: 2 }}
                      tickLine={false}
                      interval={0}
                      angle={-35}
                      textAnchor="end"
                      tickMargin={15}
                    />
                    <YAxis
                      tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                      tick={{ fontSize: 11, fill: darkMode ? '#64748b' : '#64748b', fontWeight: 600 }}
                      axisLine={false}
                      tickLine={false}
                      tickMargin={10}
                      domain={[0, 'auto']}
                    />
                  {zoomedChart.type !== 'aal' && (
                    <Legend
                      verticalAlign="top"
                      height={36}
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ paddingBottom: '12px' }}
                      formatter={(value) => <span className="text-slate-600 font-medium text-xs ml-1">{value}</span>}
                    />
                  )}
                  <Tooltip
                    cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }}
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className={`backdrop-blur border p-4 rounded-xl shadow-xl ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                            <p className={`font-bold text-sm mb-3 border-b pb-2 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                            <div className="flex flex-col gap-2">
                              {payload.map((entry, index) => (
                                <div key={index} className="flex items-center justify-between gap-8 text-xs font-medium">
                                  <div className={`flex items-center gap-2 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }}></span>
                                    <span>{entry.name}</span>
                                  </div>
                                  <span className={`font-bold text-right leading-tight ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>
                                    <div className="flex flex-col items-end">
                                      <span>{selectedGroup === 'earthquake' ? `${entry.value.toFixed(4)}%` : formatRupiah(entry.value)}</span>
                                      {selectedGroup !== 'earthquake' && <span className="text-[8px] text-green-600 font-bold">({formatUSD(entry.value)})</span>}
                                    </div>
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  {rpsConfig.map((col, idx) => (
                    <Bar
                      key={col.key}
                      dataKey={col.key}
                      name={col.label}
                      fill={colors[idx % colors.length]}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={80}
                      animationDuration={1500}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>,
      document.body
    )}
  </div>
);
}

function AALChartPanel({ boundaryData, selectedCityFeature, rekapData, onOpenTable, selectedGroup, onOpenDownload }) {
  const { darkMode } = useTheme();
  const [zoomedChart, setZoomedChart] = useState(null);
  const [pmlData, setPmlData] = useState([]);

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

  useEffect(() => {
    if (selectedGroup === 'earthquake') {
      const kota = selectedCityFeature ? (selectedCityFeature.properties.nama_kota || selectedCityFeature.properties.id_kota) : '';
      fetch(`${BACKEND_URL}/api/pml-gempa${kota ? `?kota=${kota}` : ''}`)
        .then(r => {
          if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
          return r.json();
        })
        .then(data => setPmlData(data))
        .catch(e => {
          console.error('PML fetch failed:', e);
          setPmlData([]);
        });
    }
  }, [selectedGroup, selectedCityFeature, BACKEND_URL]);

  const getPmlChartData = (group) => {
    const suffix = group.aalSuffix || group.exp;
    const isTotal = group.exp === 'total';
    const aggregated = (pmlData || []).reduce((acc, curr) => {
      const rp = curr.return_period;
      if (!acc[rp]) acc[rp] = 0;
      if (isTotal) {
        // Sum all PML categories
        const val = (curr.pml_airport || 0) + (curr.pml_res || 0) + (curr.pml_hotel || 0) +
          (curr.pml_bmn || 0) + (curr.pml_fd || 0) + (curr.pml_fs || 0) + (curr.pml_electricity || 0);
        acc[rp] += val;
      } else {
        const key = `pml_${suffix}`;
        acc[rp] += curr[key] || 0;
      }
      return acc;
    }, {});
    return Object.keys(aggregated).sort((a, b) => Number(a) - Number(b)).map(rp => ({
      label: `${rp} TH`,
      color: '#6366f1',
      value: aggregated[rp]
    }));
  };

  let totalCount = 0;
  let totalAsset = 0;

  if (rekapData?.features?.length) {
    if (selectedCityFeature) {
      const rekapFeature = rekapData.features.find(f => f.properties.id_kota === selectedCityFeature.properties.id_kota);
      if (rekapFeature) {
        totalCount = rekapFeature.properties.count_total || 0;
        totalAsset = rekapFeature.properties.total_asset_total || 0;
      }
    } else {
      totalCount = rekapData.features.reduce((sum, f) => sum + (f.properties.count_total || 0), 0);
      totalAsset = rekapData.features.reduce((sum, f) => sum + (f.properties.total_asset_total || 0), 0);
    }
  }

  // Add manual Gempa data for Total
  // (Note: AAL panel only shows active boundary data, but AAL panel is not visible for Kekeringan. 
  // It is visible for Gempa though. We still apply the manual gempa fix.)
  if (selectedGroup === 'earthquake') {
    const cityName = selectedCityFeature ? (selectedCityFeature.properties.nama_kota || selectedCityFeature.properties.id_kota) : null;
    const manualAdd = getManualGempaAddition(cityName, 'total');
    totalCount += manualAdd.count;
    totalAsset += manualAdd.asset;
  }

  const formatRupiah = (v) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);

  const getVal = (group, hazKey) => {
    const suffix = group.aalSuffix || group.exp;
    const metric = `aal_${hazKey}_${suffix}`;
    if (selectedCityFeature) return selectedCityFeature.properties[metric] || 0;
    return boundaryData.features.reduce((sum, f) => sum + (f.properties[metric] || 0), 0);
  };

  const renderCharts = (groups) => groups.map(group => {
    const data = HAZARD_KEYS.map(hk => ({ label: hk.label, color: hk.color, value: getVal(group, hk.key) }));
    const groupMax = Math.max(...data.map(d => d.value), 1);

    let expCount = 0;
    let expAsset = 0;
    if (rekapData?.features?.length) {
      if (selectedCityFeature) {
        const rekapFeature = rekapData.features.find(f => f.properties.id_kota === selectedCityFeature.properties.id_kota);
        if (rekapFeature) {
          expCount = rekapFeature.properties[`count_${group.exp}`] || 0;
          expAsset = rekapFeature.properties[`total_asset_${group.exp}`] || 0;
        }
      } else {
        expCount = rekapData.features.reduce((sum, f) => sum + (f.properties[`count_${group.exp}`] || 0), 0);
        expAsset = rekapData.features.reduce((sum, f) => sum + (f.properties[`total_asset_${group.exp}`] || 0), 0);
      }
    }

    // Add manual Gempa data for specific exposures
    if (selectedGroup === 'earthquake' && (group.exp === 'bmn' || group.exp === 'residential')) {
      const cityName = selectedCityFeature ? (selectedCityFeature.properties.nama_kota || selectedCityFeature.properties.id_kota) : null;
      const manualExpAdd = getManualGempaAddition(cityName, group.exp);
      expCount += manualExpAdd.count;
      expAsset += manualExpAdd.asset;
    }

    return (
      <div key={group.exp} className={`rounded-xl p-3 mb-3 border relative transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700/50 shadow-lg' : 'bg-slate-50 border-slate-100/50'}`}>
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className={`text-[10px] font-bold tracking-wide text-center ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>{group.label}</div>
          {group.exp !== 'total' && (
            <button
              onClick={() => onOpenTable && onOpenTable(group.layerKey)}
              title="Lihat Data Tabel"
              className={`transition-all rounded p-1 shadow-sm border ${darkMode ? 'text-gray-400 hover:text-blue-400 bg-gray-700 border-gray-600 hover:border-blue-900/50' : 'text-slate-400 hover:text-blue-500 bg-white hover:bg-blue-50 border-slate-200 hover:border-blue-200'}`}
            >
              <TableIcon size={12} strokeWidth={2.5} />
            </button>
          )}
        </div>
        {group.exp !== 'total' && expCount > 0 && (
          <div className={`flex justify-between items-center text-[9px] mb-3 px-2 border-b pb-2 ${darkMode ? 'border-gray-700' : 'border-slate-200'}`}>
            <div className="flex flex-col">
              <span className={`uppercase tracking-wider font-semibold ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Bangunan</span>
              <span className={`font-bold ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>{expCount.toLocaleString('id-ID')}</span>
            </div>
            <div className="flex flex-col text-right">
              <span className={`uppercase tracking-wider font-semibold ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Nilai Aset</span>
              <div className="flex flex-col items-end">
                <span className={`font-bold ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>{formatRupiah(expAsset)}</span>
                <span className="text-[8px] text-green-600 font-bold">({formatUSD(expAsset)})</span>
              </div>
            </div>
          </div>
        )}
        <div className="flex justify-center flex-wrap gap-4 overflow-visible">
          <MiniBarChart data={data} maxVal={groupMax} expAsset={expAsset} />
        </div>

        {selectedGroup === 'earthquake' && pmlData.length > 0 && (
          <div className={`mt-4 pt-3 border-t text-center ${darkMode ? 'border-gray-700/60' : 'border-slate-200/60'}`}>
            <div className={`text-[8px] font-bold tracking-widest uppercase mb-2 ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>PML Gempa (Probabilistic Loss)</div>
            <div className="flex justify-center">
              <MiniBarChart
                data={getPmlChartData(group)}
                maxVal={Math.max(...getPmlChartData(group).map(d => d.value), 1)}
                expAsset={expAsset}
              />
            </div>
          </div>
        )}
      </div>
    );
  });

  const cityChartData = React.useMemo(() => {
    if (selectedCityFeature) return [];
    if (!boundaryData?.features) return [];
    return boundaryData.features.map(f => {
      const item = { kota: f.properties.nama_kota || f.properties.id_kota || 'Unknown' };
      HAZARD_KEYS.forEach(hk => {
        item[hk.key] = f.properties[`aal_${hk.key}_total`] || 0;
      });
      return item;
    }).sort((a, b) => a.kota.localeCompare(b.kota));
  }, [boundaryData, selectedCityFeature]);

  const exposureChartData = React.useMemo(() => {
    if (!boundaryData?.features) return [];
    return EXPOSURE_GROUPS.filter(g => g.exp !== 'total').map(group => {
      const item = { exposure_name: group.label };
      HAZARD_KEYS.forEach(hk => {
        let sum = 0;
        boundaryData.features.forEach(f => {
          const suffix = group.aalSuffix || group.exp;
          sum += (f.properties[`aal_${hk.key}_${suffix}`] || 0);
        });
        item[hk.key] = sum;
      });
      return item;
    });
  }, [boundaryData]);

  const pmlCityChartData = React.useMemo(() => {
    if (selectedGroup !== 'earthquake' || !pmlData || pmlData.length === 0) return [];
    if (selectedCityFeature) return [];
    const byCity = pmlData.reduce((acc, curr) => {
      const city = curr.id_kota;
      if (!acc[city]) acc[city] = { kota: city };
      acc[city][curr.return_period] = (curr.pml_res || 0) + (curr.pml_bmn || 0) + (curr.pml_hotel || 0) +
        (curr.pml_fd || 0) + (curr.pml_fs || 0) + (curr.pml_electricity || 0) + (curr.pml_airport || 0);
      return acc;
    }, {});
    return Object.values(byCity).sort((a, b) => a.kota.localeCompare(b.kota));
  }, [pmlData, selectedGroup, selectedCityFeature]);

  const pmlExposureChartData = React.useMemo(() => {
    if (selectedGroup !== 'earthquake' || !pmlData || pmlData.length === 0) return [];
    return EXPOSURE_GROUPS.filter(g => g.exp !== 'total').map(group => {
      const item = { exposure_name: group.label };
      const suffix = group.aalSuffix || group.exp;
      const key = `pml_${suffix}`;
      [100, 200, 250, 500, 1000].forEach(rp => {
        const filtered = pmlData.filter(p => p.return_period === rp);
        item[rp.toString()] = filtered.reduce((sum, p) => sum + (p[key] || 0), 0);
      });
      return item;
    });
  }, [pmlData, selectedGroup]);

  if (!boundaryData?.features?.length) return null;

  return (
    <div className={`px-4 pb-4 border-t flex flex-col items-center relative ${darkMode ? 'border-gray-800' : 'border-slate-100'}`}>
      {/* Zoomed Chart Modal */}
      {zoomedChart && typeof document !== 'undefined' && createPortal(
        <div className={`fixed inset-0 z-[9999] backdrop-blur-sm flex items-center justify-center p-4 lg:p-12 animate-in fade-in duration-200 ${darkMode ? 'bg-black/60' : 'bg-slate-900/60'}`}>
          <div className={`rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 ${darkMode ? 'bg-gray-900 border border-gray-800' : 'bg-white'}`}>
            <div className={`px-6 py-4 flex items-center justify-between border-b ${darkMode ? 'border-gray-800 bg-gray-900/50' : 'border-slate-100 bg-slate-50/50'}`}>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${darkMode ? 'bg-blue-900/30' : 'bg-blue-100'}`}>
                  <BarChart2 size={24} className={darkMode ? 'text-blue-400' : 'text-blue-600'} />
                </div>
                <div>
                  <h3 className={`text-lg font-bold tracking-tight ${darkMode ? 'text-white' : 'text-slate-800'}`}>{zoomedChart.title}</h3>
                  <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Nilai Average Annual Loss</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    const el = document.getElementById('zoomed-aal-capture');
                    if (!el) return;
                    const canvas = await html2canvas(el, {
                      backgroundColor: darkMode ? '#111827' : '#ffffff',
                      scale: 2,
                      useCORS: true,
                      onclone: (clonedDoc) => {
                        const styleTags = clonedDoc.getElementsByTagName('style');
                        for (let style of styleTags) {
                          style.innerHTML = style.innerHTML.replace(/(oklch|oklab|lab)\([^)]+\)/g, '#00000000');
                        }
                      }
                    });
                    const link = document.createElement('a');
                    link.download = `${zoomedChart.title.replace(/\s+/g, '_').toLowerCase()}_${new Date().toISOString().split('T')[0]}.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                  }}
                  className={`p-2 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800 text-blue-400' : 'hover:bg-blue-50 text-blue-600'}`}
                  title="Unduh Gambar"
                >
                  <Download size={24} />
                </button>
                <button
                  onClick={() => setZoomedChart(null)}
                  className={`p-2 rounded-full transition-colors group ${darkMode ? 'hover:bg-gray-800' : 'hover:bg-slate-200'}`}
                  title="Tutup Modal"
                >
                  <X size={24} className={`${darkMode ? 'text-gray-500 group-hover:text-gray-300' : 'text-slate-400 group-hover:text-slate-600'}`} />
                </button>
              </div>
            </div>

            <div id="zoomed-aal-capture" className={`flex-1 w-full p-6 relative flex flex-col ${darkMode ? 'bg-gray-900' : 'bg-white'}`}>
              {selectedGroup !== 'earthquake' && (
                <div className="mb-4 text-left">
                  <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{zoomedChart.title}</h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Analisis Average Annual Loss (AAL)</p>
                </div>
              )}
              <div className="flex-1 min-h-0 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={zoomedChart.data} margin={{ top: 20, right: 30, bottom: 60, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#e2e8f0'} />
                    <XAxis
                      dataKey={zoomedChart.xKey}
                      tick={{ fontSize: 11, fill: darkMode ? '#94a3b8' : '#475569', fontWeight: 700 }}
                      axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1', strokeWidth: 2 }}
                      tickLine={false}
                      interval={0}
                      angle={-35}
                      textAnchor="end"
                      tickMargin={15}
                    />
                    <YAxis
                      tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                      tick={{ fontSize: 11, fill: darkMode ? '#64748b' : '#64748b', fontWeight: 600 }}
                      axisLine={false}
                      tickLine={false}
                      tickMargin={10}
                      domain={[0, 'auto']}
                    />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ paddingBottom: '12px' }}
                    formatter={(value) => <span className={`font-medium text-xs ml-1 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>{value.replace('\n', ' ')}</span>}
                  />
                  <Tooltip
                    cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }}
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className={`backdrop-blur border p-4 rounded-xl shadow-xl ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                            <p className={`font-bold text-sm mb-3 border-b pb-2 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                            <div className="flex flex-col gap-2">
                              {payload.map((entry, index) => (
                                <div key={index} className="flex items-center justify-between gap-8 text-xs font-medium">
                                  <div className={`flex items-center gap-2 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }}></span>
                                    <span>{entry.name.replace('\n', ' ')}</span>
                                  </div>
                                  <div className="flex flex-col items-end">
                                    <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                    <span className="text-[8px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                    {(zoomedChart.isPml ? PML_RP_KEYS : HAZARD_KEYS).map((col) => (
                      <Bar
                        key={col.key}
                        dataKey={col.key}
                        name={col.label}
                        fill={col.color}
                        radius={[4, 4, 0, 0]}
                        maxBarSize={80}
                        animationDuration={1500}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {rekapData?.features?.length > 0 && (
        <div className={`w-full border rounded-xl p-3 mt-3 mb-1 shadow-sm flex justify-between items-center transition-all ${darkMode ? 'bg-gray-800/60 border-gray-700 shadow-black/20' : 'bg-slate-50 border-slate-100'}`}>
          <div className="flex flex-col">
            <span className={`text-[8px] font-bold tracking-widest uppercase ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Total Bangunan</span>
            <span className={`text-[12px] font-extrabold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{totalCount.toLocaleString('id-ID')}</span>
          </div>
          <div className={`w-[1px] h-6 ${darkMode ? 'bg-gray-700' : 'bg-slate-200'}`}></div>
          <div className="flex flex-col text-right">
            <span className={`text-[8px] font-bold tracking-widest uppercase ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Total Nilai Aset</span>
            <div className="flex flex-col items-end">
              <span className={`text-[12px] font-extrabold ${darkMode ? 'text-white' : 'text-slate-800'}`}>{formatRupiah(totalAsset)}</span>
              <span className="text-[10px] text-green-600 font-bold">({formatUSD(totalAsset)})</span>
            </div>
          </div>
        </div>
      )}

      {/* City Comparison Chart */}
      {!selectedCityFeature && cityChartData.length > 0 && (
        <div className={`w-full h-[180px] border rounded-xl p-2 mt-2 shadow-sm relative z-0 flex flex-col transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700 shadow-black/20' : 'bg-white border-slate-200'}`}>
          <div className="text-[8px] font-extrabold tracking-widest uppercase mb-1 flex items-center justify-between">
            <div className={`flex items-center gap-1 ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
              <BarChart2 size={10} className={darkMode ? 'text-blue-400' : 'text-blue-500'} />
              Perbandingan AAL Antar Kota
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-[7px] font-medium ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Klik untuk perbesar</span>
              <button
                onClick={(e) => { e.stopPropagation(); onOpenDownload('map_chart'); }}
                className={`p-1 rounded-md transition-all ${darkMode ? 'hover:bg-white/10 text-gray-400 hover:text-blue-400' : 'hover:bg-slate-100 text-slate-400 hover:text-blue-600'}`}
                title="Download Gambar"
              >
                <Download size={10} strokeWidth={2.5} />
              </button>
            </div>
          </div>
          <div
            className={`flex-1 w-full relative cursor-pointer group rounded border border-transparent transition-colors ${darkMode ? 'hover:border-blue-900/50 hover:bg-gray-800/60' : 'hover:border-blue-200 hover:bg-slate-50'}`}
            onClick={() => setZoomedChart({ type: 'city', title: 'Perbandingan AAL Antar Kota', data: cityChartData, xKey: "kota" })}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cityChartData} margin={{ top: 5, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
                <XAxis
                  dataKey="kota"
                  tick={{ fontSize: 6, fill: darkMode ? '#94a3b8' : '#64748b', fontWeight: 700 }}
                  axisLine={{ stroke: darkMode ? '#475569' : '#cbd5e1' }}
                  tickLine={false}
                  interval={0}
                  angle={-35}
                  textAnchor="end"
                  height={40}
                />
                <YAxis
                  tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                  tick={{ fontSize: 7, fill: darkMode ? '#64748b' : '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 'auto']}
                />
                <Tooltip
                  cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }}
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className={`backdrop-blur border p-2 rounded-lg shadow-lg ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                          <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                          <div className="flex flex-col gap-1">
                            {payload.map((entry, index) => (
                              <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
                                <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                  <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                                  <span>{entry.name.replace('\n', ' ')}</span>
                                </div>
                                <div className="flex flex-col items-end">
                                  <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                  <span className="text-[7px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {HAZARD_KEYS.map((col) => (
                  <Bar key={col.key} dataKey={col.key} name={col.label} fill={col.color} radius={[2, 2, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
            <div className={`absolute inset-0 group-hover:opacity-100 backdrop-blur-[1px] flex items-center justify-center transition-all opacity-0 ${darkMode ? 'bg-gray-900/10' : 'bg-white/10'}`}>
              <div className={`rounded-full p-2 shadow-lg transform scale-95 group-hover:scale-100 transition-all ${darkMode ? 'bg-blue-600 text-white' : 'bg-slate-900/80 text-white'}`}>
                <Maximize2 size={16} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Exposure Comparison Chart (AAL) */}
      {exposureChartData.length > 0 && (
        <div className={`w-full h-[180px] border rounded-xl p-2 mt-2 shadow-sm relative z-0 flex flex-col transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700 shadow-black/20' : 'bg-white border-slate-200'}`}>
          <div className="text-[8px] font-extrabold tracking-widest uppercase mb-1 flex items-center justify-between">
            <div className={`flex items-center gap-1 ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
              <BarChart2 size={10} className={darkMode ? 'text-orange-400' : 'text-orange-500'} />
              Perbandingan AAL Antar Eksposur
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-[7px] font-medium ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Klik untuk perbesar</span>
              <button
                onClick={(e) => { e.stopPropagation(); onOpenDownload('map_chart'); }}
                className={`p-1 rounded-md transition-all ${darkMode ? 'hover:bg-white/10 text-orange-400 hover:text-blue-400' : 'hover:bg-slate-100 text-slate-400 hover:text-blue-600'}`}
                title="Download Gambar"
              >
                <Download size={10} strokeWidth={2.5} />
              </button>
            </div>
          </div>
          <div
            className={`flex-1 w-full relative cursor-pointer group rounded border border-transparent transition-colors ${darkMode ? 'hover:border-orange-900/50 hover:bg-gray-800/60' : 'hover:border-orange-200 hover:bg-slate-50'}`}
            onClick={() => setZoomedChart({ type: 'exposure', title: 'Perbandingan AAL Antar Eksposur', data: exposureChartData, xKey: "exposure_name" })}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={exposureChartData} margin={{ top: 5, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
                <XAxis dataKey="exposure_name" tick={{ fontSize: 6, fill: darkMode ? '#94a3b8' : '#64748b' }} interval={0} angle={-25} textAnchor="end" height={40} />
                <YAxis
                  tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                  tick={{ fontSize: 7, fill: darkMode ? '#64748b' : '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 'auto']}
                />
                <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }} content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className={`backdrop-blur border p-2 rounded-lg shadow-lg ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                        <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                        <div className="flex flex-col gap-1">
                          {payload.map((entry, index) => (
                            <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
                              <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                                <span>{entry.name.replace('\n', ' ')}</span>
                              </div>
                              <div className="flex flex-col items-end">
                                <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                <span className="text-[7px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }} />
                {HAZARD_KEYS.map((col) => <Bar key={col.key} dataKey={col.key} name={col.label} fill={col.color} radius={[2, 2, 0, 0]} />)}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* PML Comparison Charts */}
      {selectedGroup === 'earthquake' && pmlCityChartData.length > 0 && (
        <div className={`w-full h-[180px] border rounded-xl p-2 mt-2 shadow-sm relative z-0 flex flex-col transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700 shadow-black/20' : 'bg-white border-slate-200'}`}>
          <div className="text-[8px] font-extrabold tracking-widest uppercase mb-1 flex items-center justify-between">
            <div className={`flex items-center gap-1 ${darkMode ? 'text-indigo-400' : 'text-indigo-500'}`}>
              <BarChart2 size={10} />
              Perbandingan PML Antar Kota
            </div>
          </div>
          <div
            className="flex-1 cursor-pointer"
            onClick={() => setZoomedChart({ type: 'pml_city', title: 'Perbandingan PML Antar Kota', data: pmlCityChartData, xKey: "kota", isPml: true })}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pmlCityChartData} margin={{ top: 5, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
                <XAxis dataKey="kota" tick={{ fontSize: 6, fill: darkMode ? '#94a3b8' : '#64748b' }} interval={0} angle={-35} textAnchor="end" height={40} />
                <YAxis
                  tickFormatter={(val) => formatYAxisShort(val, selectedGroup === 'earthquake')}
                  tick={{ fontSize: 7, fill: darkMode ? '#64748b' : '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 'auto']}
                />
                <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }} content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className={`backdrop-blur border p-2 rounded-lg shadow-lg ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                        <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                        <div className="flex flex-col gap-1">
                          {payload.map((entry, index) => (
                            <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
                              <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                                <span>{entry.name.replace('\n', ' ')}</span>
                              </div>
                              <div className="flex flex-col items-end">
                                <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                <span className="text-[7px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }} />
                {PML_RP_KEYS.map(rp => <Bar key={rp.key} dataKey={rp.key} name={rp.label} fill={rp.color} radius={[2, 2, 0, 0]} />)}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {selectedGroup === 'earthquake' && pmlExposureChartData.length > 0 && (
        <div className={`w-full h-[180px] border rounded-xl p-2 mt-2 shadow-sm relative z-0 flex flex-col transition-all ${darkMode ? 'bg-gray-800/40 border-gray-700 shadow-black/20' : 'bg-white border-slate-200'}`}>
          <div className="text-[8px] font-extrabold tracking-widest uppercase mb-1 flex items-center justify-between">
            <div className={`flex items-center gap-1 ${darkMode ? 'text-violet-400' : 'text-violet-500'}`}>
              <BarChart2 size={10} />
              Perbandingan PML Antar Eksposur
            </div>
          </div>
          <div
            className="flex-1 cursor-pointer"
            onClick={() => setZoomedChart({ type: 'pml_exposure', title: 'Perbandingan PML Antar Eksposur', data: pmlExposureChartData, xKey: "exposure_name", isPml: true })}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pmlExposureChartData} margin={{ top: 5, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={darkMode ? 'rgba(148, 163, 184, 0.1)' : '#f1f5f9'} />
                <XAxis dataKey="exposure_name" tick={{ fontSize: 6, fill: darkMode ? '#94a3b8' : '#64748b' }} interval={0} angle={-25} textAnchor="end" height={40} />
                <YAxis tickFormatter={(val) => val >= 1e12 ? `Rp${(val / 1e12).toFixed(1)}T` : val >= 1e9 ? `Rp${(val / 1e9).toFixed(0)}M` : `Rp${(val / 1e6).toFixed(0)}Jt`} tick={{ fontSize: 7, fill: darkMode ? '#64748b' : '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: darkMode ? 'rgba(255,255,255,0.05)' : 'rgba(241, 245, 249, 0.5)' }} content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className={`backdrop-blur border p-2 rounded-lg shadow-lg ${darkMode ? 'bg-gray-900/95 border-gray-700' : 'bg-white/95 border-slate-200'}`}>
                        <p className={`font-bold text-[9px] mb-1.5 border-b pb-1 ${darkMode ? 'text-white border-gray-700' : 'text-slate-800 border-slate-100'}`}>{label}</p>
                        <div className="flex flex-col gap-1">
                          {payload.map((entry, index) => (
                            <div key={index} className="flex items-center justify-between gap-4 text-[8px]">
                              <div className={`flex items-center gap-1.5 ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>
                                <span className="w-2 h-2 rounded-[2px]" style={{ backgroundColor: entry.color }}></span>
                                <span>{entry.name.replace('\n', ' ')}</span>
                              </div>
                              <div className="flex flex-col items-end">
                                <span className={`font-bold ${darkMode ? 'text-gray-200' : 'text-slate-800'}`}>{formatRupiah(entry.value)}</span>
                                <span className="text-[7px] text-green-600 font-bold">({formatUSD(entry.value)})</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }} />
                {PML_RP_KEYS.map(rp => <Bar key={rp.key} dataKey={rp.key} name={rp.label} fill={rp.color} radius={[2, 2, 0, 0]} />)}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {selectedGroup !== 'earthquake' && (
        <div className={`text-[9px] font-bold tracking-widest uppercase my-3 w-full text-left ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Distribusi AAL per Eksposur</div>
      )}
      <div className="flex flex-col w-full px-1 pt-1 pb-2">
        {renderCharts(EXPOSURE_GROUPS.filter(g => {
          if (selectedGroup === 'earthquake') {
            return g.exp !== 'total' && !g.gempaOnly;
          }
          return !g.gempaOnly;
        }))}
      </div>
    </div>
  );
}

// ΓöÇΓöÇ Main Component ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
const ReactLegendOverlay = ({
  rasterStats,
  infraLayers,
  selectedData,
  curveData,
  calculateDamage,
  HAZARD_INFO,
  EXPOSURE_COLORS,
  activeAalExposure,
  onInputModeChange,
  boundaryDataAAL,
  boundaryDataDL,
  selectedGroup,
  selectedRpId,
  selectedCityFeature,
  onSelectCity,
  onClearCity,
  onOpenTable,
  onOpenDownload,
  floodView,
  setFloodView,
  floodSawahYear,
  setFloodSawahYear,
  floodSawahData,
  droughtLossYear,
  setDroughtLossYear,
  droughtSawahData,
}) => {
  const { darkMode } = useTheme();
  const [inputMode, setInputMode] = useState('pick'); // 'pick' or 'manual'
  const [manualIntensity, setManualIntensity] = useState('');
  const [isAalSidebarOpen, setIsAalSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const isResizingRef = React.useRef(false);

  React.useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizingRef.current) return;
      // Calculate new width: viewport width - mouse X position
      const newWidth = window.innerWidth - e.clientX;
      // Clamp width between 280px (minimum) and 800px (maximum)
      setSidebarWidth(Math.max(280, Math.min(newWidth, 800)));
    };

    const handleMouseUp = () => {
      isResizingRef.current = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const handleModeChange = (mode) => {
    setInputMode(mode);
    if (onInputModeChange) {
      onInputModeChange(mode);
    }
  };

  const hazardKey = rasterStats?.hazardKey;
  const hazardInfo = hazardKey ? HAZARD_INFO[hazardKey] : null;
  const hasHazard = !!hazardInfo;
  const activeExposures = Object.keys(infraLayers).filter(k => k !== 'boundaries' && k !== 'aal' && infraLayers[k]);
  const hasExposure = activeExposures.length > 0;
  const hasAAL = infraLayers.aal && selectedGroup && boundaryDataAAL;
  const hasDirectLoss = infraLayers.directLoss && selectedGroup && boundaryDataDL;
  const showBoundaryPanel = hasAAL || hasDirectLoss;
  const activeBoundaryData = hasAAL ? boundaryDataAAL : boundaryDataDL;

  if (!hasHazard && !hasExposure && !showBoundaryPanel) return null;

  const format = (v) => Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 3 });

  // Determine intensity to use
  let displayIntensity = null;
  let displayDamageRatio = null;

  if (inputMode === 'manual') {
    displayIntensity = manualIntensity !== '' ? parseFloat(manualIntensity) : null;
    if (displayIntensity != null && !isNaN(displayIntensity)) {
      const curveMap = {
        flood: 'banjir',
        flood_comp: 'banjir',
        earthquake: 'gempa',
        tsunami: 'tsunami',
        drought_gpm: 'kekeringan',
        drought_mme: 'kekeringan'
      };
      const curveKey = curveMap[hazardKey] || hazardKey;
      displayDamageRatio = calculateDamage(curveKey, displayIntensity);
    }
  } else {
    displayIntensity = selectedData.intensity;
    displayDamageRatio = selectedData.damageRatio;
  }

  const renderInteractionPanel = () => {
    if (!hasHazard) return null;
    const curveMap = {
      flood: 'banjir',
      flood_comp: 'banjir',
      earthquake: 'gempa',
      tsunami: 'tsunami',
      drought_gpm: 'kekeringan',
      drought_mme: 'kekeringan'
    };
    const curveKey = curveMap[hazardKey] || hazardKey;
    const isDrought = curveKey === 'kekeringan';
    const isEarthquake = curveKey === 'gempa';
    const hasCurve = !!(curveKey && (isDrought || isEarthquake || (curveData && curveData[curveKey])));
    const showCurve = hasCurve && !isEarthquake; // Hide curve for earthquake as requested

    let config = null;
    let hazardCurves = null;
    let availableTaxos = [];
    let legendItems = [];
    let polylines = [];
    let svgW = 0, svgH = 0, padding = {}, chartW = 0, chartH = 0, getX = null, getY = null, maxX = 1, maxY = 1;

    let availableGroups = [];

    if (hasCurve) {
      config = {
        'banjir': {
          groups: [
            {
              title: 'Building Vulnerability',
              taxos: ['1.0', '1', '2.0', '2'],
              colors: { '1.0': '#fbbf24', '1': '#fbbf24', '2.0': '#ef4444', '2': '#ef4444' },
              labels: { '1.0': 'Lantai 1', '1': 'Lantai 1', '2.0': 'Lantai 2+', '2': 'Lantai 2+' }
            },
            {
              title: 'Sawah Vulnerability',
              taxos: ['sawah'],
              colors: { 'sawah': '#10b981' },
              labels: { 'sawah': 'Sawah' }
            }
          ],
          title: 'Banjir', xTitle: 'Kedalaman (m)'
        },
        'tsunami': {
          taxos: ['cr', 'mcf'],
          colors: { 'cr': '#8b5cf6', 'mcf': '#ec4899' },
          labels: { 'cr': 'CR', 'mcf': 'MCF' },
          title: 'Tsunami', xTitle: 'Inundansi (m)'
        },
        'gempa': {
          taxos: ['cr', 'mcf'],
          colors: { 'cr': '#8b5cf6', 'mcf': '#ec4899' },
          labels: { 'cr': 'CR', 'mcf': 'MCF' },
          title: 'Gempa', xTitle: 'Intensitas'
        },
        'kekeringan': {
          groups: [
            {
              title: 'Sawah Vulnerability',
              taxos: ['sawah'],
              colors: { 'sawah': '#10b981' },
              labels: { 'sawah': 'Sawah' }
            }
          ],
          title: 'Kekeringan', xTitle: 'GPM Index'
        }
      }[curveKey];

      if (isDrought) {
        hazardCurves = { 'sawah': { x: DROUGHT_CURVE.map(p => p.x), y: DROUGHT_CURVE.map(p => p.y) } };
      } else {
        hazardCurves = curveData[curveKey];
      }

      let groups = config?.groups || (config ? [{
        title: 'Vulnerability Curve',
        taxos: config.taxos,
        colors: config.colors,
        labels: config.labels
      }] : []);

      // NEW: Filter groups by floodView toggle for Banjir
      if (curveKey === 'banjir') {
        if (floodView === 'building') {
          groups = groups.filter(g => g.title.toLowerCase().includes('building'));
        } else if (floodView === 'sawah') {
          groups = groups.filter(g => g.title.toLowerCase().includes('sawah'));
        }
      }

      // Calculate global maxX for all groups
      let allPtsX = [];
      groups.forEach(group => {
        group.taxos.forEach(t => {
          const cKey = Object.keys(hazardCurves).find(k => k.toLowerCase() === t.toLowerCase() || k.toLowerCase() === (t + '.0'));
          if (hazardCurves[cKey]) allPtsX.push(...hazardCurves[cKey].x);
        });
      });

      if (allPtsX.length > 0) {
        maxX = Math.max(...allPtsX, 1);
        const isSmallHazard = curveKey === 'banjir' || curveKey === 'kekeringan';
        chartW = isSmallHazard ? 50 : (availableGroups.length > 1 ? 75 : 110);
        chartH = isSmallHazard ? 36 : 50;
        padding = { top: 10, right: 8, bottom: 15, left: isSmallHazard ? 14 : 20 };
        svgW = chartW + padding.left + padding.right;
        svgH = chartH + padding.top + padding.bottom;
        getX = (val) => (val / maxX) * chartW + padding.left;
        getY = (val) => chartH - (val / maxY) * chartH + padding.top;

        availableGroups = groups.map((group, gIdx) => {
          let groupPolylines = [];
          let groupLegendItems = [];
          let seenLabels = new Set();

          group.taxos.forEach(t => {
            const cKey = Object.keys(hazardCurves).find(k => k.toLowerCase() === t.toLowerCase() || k.toLowerCase() === (t + '.0'));
            const curve = hazardCurves[cKey], label = group.labels[t];
            if (curve && curve.x.length > 1) {
              const points = curve.x.map((x, i) => `${getX(x)},${getY(curve.y[i])}`).join(' ');
              groupPolylines.push(
                <polyline key={t} points={points} fill="none" stroke={group.colors[t]} strokeWidth="1.5" strokeLinejoin="round" />
              );
              if (!seenLabels.has(label)) {
                groupLegendItems.push(
                  <div key={label} className="flex items-center gap-1.5 text-[8px] text-slate-500 font-medium whitespace-nowrap">
                    <div style={{ backgroundColor: group.colors[t] }} className="w-2.5 h-[2px] rounded-full"></div>
                    <span>{label}</span>
                  </div>
                );
                seenLabels.add(label);
              }
            }
          });

          return { ...group, polylines: groupPolylines, legendItems: groupLegendItems };
        }).filter(g => g.polylines.length > 0);
      }
    }

    return (
      <div className={`flex flex-row items-center ${availableGroups.length > 1 ? 'gap-2' : 'gap-5'}`}>
        {/* Vulnerability Curve Section */}
        {showCurve && availableGroups.length > 0 && availableGroups.map((group, idx) => (
          <div key={idx} className="flex flex-col items-center">
            <h4 className={`text-[10px] font-bold mb-2 truncate max-w-[90px] ${darkMode ? 'text-gray-300' : 'text-slate-800'}`}>{group.title}</h4>
            <div className={`flex flex-row items-center ${availableGroups.length > 1 ? 'gap-1' : 'gap-6'}`}>
              {/* Chart SVG */}
              <div className="flex flex-col items-center">
                <svg width={svgW} height={svgH} style={{ fontFamily: 'inherit', overflow: 'visible' }}>
                  <line x1={padding.left} y1={getY(0)} x2={padding.left + chartW} y2={getY(0)} stroke={darkMode ? 'rgba(255,255,255,0.1)' : '#e2e8f0'} strokeWidth="1" />
                  <line x1={padding.left} y1={getY(0.5)} x2={padding.left + chartW} y2={getY(0.5)} stroke={darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9'} strokeDasharray="2,2" />
                  <line x1={padding.left} y1={getY(1)} x2={padding.left + chartW} y2={getY(1)} stroke={darkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9'} strokeDasharray="2,2" />
                  <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + chartH} stroke={darkMode ? '#475569' : '#cbd5e1'} strokeWidth="1" />
                  <line x1={padding.left} y1={padding.top + chartH} x2={padding.left + chartW} y2={padding.top + chartH} stroke={darkMode ? '#475569' : '#cbd5e1'} strokeWidth="1" />
                  {group.polylines}
                  <text x={padding.left - 3} y={getY(0) + 2} textAnchor="end" fontSize="6px" fill={darkMode ? '#94a3b8' : '#64748b'} fontWeight="600">0</text>
                  <text x={padding.left - 3} y={getY(1) + 2} textAnchor="end" fontSize="6px" fill={darkMode ? '#94a3b8' : '#64748b'} fontWeight="600">1.0</text>
                  <text x={padding.left} y={padding.top + chartH + 8} textAnchor="middle" fontSize="6px" fill={darkMode ? '#94a3b8' : '#64748b'} fontWeight="600">0</text>
                  <text x={padding.left + chartW} y={padding.top + chartH + 8} textAnchor="middle" fontSize="6px" fill={darkMode ? '#94a3b8' : '#64748b'} fontWeight="600">{maxX.toFixed(1)}</text>
                  <text x={padding.left + chartW / 2} y={padding.top + chartH + 16} textAnchor="middle" fontSize="6.5px" fill={darkMode ? '#475569' : '#94a3b8'} fontWeight="700">{config?.xTitle}</text>
                  <text x={6} y={padding.top + chartH / 2} textAnchor="middle" fontSize="6.5px" fill={darkMode ? '#475569' : '#94a3b8'} fontWeight="700" transform={`rotate(-90, 6, ${padding.top + chartH / 2})`}>Damage</text>
                </svg>
              </div>

              {/* Legend Items */}
              <div className={`flex flex-col gap-1 justify-center h-full ${availableGroups.length > 1 ? 'min-w-[35px]' : 'min-w-[50px]'}`}>
                {group.legendItems}
              </div>
            </div>
          </div>
        ))}

        {!isEarthquake && (
          <>
            {/* Divider SVG -> Controls */}
            <div className={`w-[1px] h-12 self-center mx-1 rounded-full ${darkMode ? 'bg-gray-800' : 'bg-slate-200'}`}></div>

            {/* Column 3: Controls & Results */}
            <div className="flex flex-row items-center gap-4">
              {/* Controls sub-column */}
              <div className="flex flex-col w-[100px]">
                <div className={`flex rounded p-0.5 mb-2.5 ${darkMode ? 'bg-gray-800' : 'bg-slate-200'}`}>
                  <button
                    className={`flex-1 text-[7px] font-bold py-1 rounded transition-colors ${inputMode === 'pick' ? (darkMode ? 'bg-gray-700 text-white shadow-sm' : 'bg-white text-slate-800 shadow-sm') : (darkMode ? 'text-gray-500 hover:text-gray-400' : 'text-slate-500 hover:text-slate-700')}`}
                    onClick={() => handleModeChange('pick')}
                  >
                    PICK POINT
                  </button>
                  <button
                    className={`flex-1 text-[7px] font-bold py-1 rounded transition-colors ${inputMode === 'manual' ? (darkMode ? 'bg-gray-700 text-white shadow-sm' : 'bg-white text-slate-800 shadow-sm') : (darkMode ? 'text-gray-500 hover:text-gray-400' : 'text-slate-500 hover:text-slate-700')}`}
                    onClick={() => handleModeChange('manual')}
                  >
                    MANUAL
                  </button>
                </div>

                {inputMode === 'manual' ? (
                  <input
                    type="number"
                    placeholder="Ketik angka..."
                    value={manualIntensity}
                    onChange={(e) => setManualIntensity(e.target.value)}
                    className={`w-full text-[10px] p-1.5 font-bold border rounded outline-none shadow-sm transition-colors ${darkMode ? 'bg-gray-800 border-orange-700 text-white focus:border-orange-500' : 'border-orange-500 text-slate-800 bg-white'
                      }`}
                  />
                ) : (
                  <div className={`w-full text-[9px] p-1.5 font-semibold border border-transparent text-center ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>
                    Klik peta...
                  </div>
                )}
              </div>

              {/* Results sub-column */}
              <div className="flex flex-col gap-1.5 w-[110px]">
                <div className="flex justify-between items-center">
                  <span className={`text-[7.5px] font-semibold ${darkMode ? 'text-gray-500' : 'text-slate-500'}`}>
                    Intensity: {displayIntensity != null ? (inputMode === 'manual' ? '(Manual)' : '') : ''}
                  </span>
                  <span className={`text-[9px] font-bold ${darkMode ? 'text-white' : 'text-slate-800'}`}>
                    {displayIntensity != null ? displayIntensity.toFixed(3) + ' ' + (hazardInfo.unit || '') : '-'}
                  </span>
                </div>

                {hasCurve && availableGroups.length > 0 ? (
                  (() => {
                    const seenLabels = new Set();
                    return availableGroups.flatMap(group => group.taxos).map(tax => {
                      const group = availableGroups.find(g => g.taxos.includes(tax));
                      const label = group?.labels[tax] || tax.toUpperCase();
                      if (seenLabels.has(label)) return null;
                      seenLabels.add(label);

                      let val = 0;
                      if (displayIntensity != null && displayDamageRatio) {
                        if (displayDamageRatio[tax] !== undefined) {
                          val = displayDamageRatio[tax];
                        } else if (displayDamageRatio[tax.toLowerCase()] !== undefined) {
                          val = displayDamageRatio[tax.toLowerCase()];
                        }
                      }
                      return (
                        <div key={tax} className="flex justify-between items-center mt-0.5">
                          <span className={`text-[7.5px] ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>Loss {label}:</span>
                          <span className="text-[9px] font-bold" style={{ color: group?.colors[tax] || (darkMode ? '#e2e8f0' : '#1e293b') }}>
                            {(val * 100).toFixed(2)}%
                          </span>
                        </div>
                      );
                    });
                  })()
                ) : (
                  !hasCurve && <div className="text-[7px] text-slate-400 italic mt-1">Tidak ada kalkulasi damage</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <>
      {(hasHazard || hasExposure) && (
        <div className="absolute bottom-6 left-0 md:left-[280px] right-0 lg:right-[320px] pointer-events-none z-[1010] flex justify-center px-2">
          <div className={`backdrop-blur-sm px-4 lg:px-5 py-3 rounded-[24px] shadow-[0_8px_30px_rgb(0,0,0,0.12)] border pointer-events-auto transition-all duration-300 max-w-full flex flex-row items-center overflow-x-auto custom-scrollbar ${darkMode ? 'bg-gray-900/95 border-gray-800 shadow-black/40' : 'bg-white/95 border-slate-200'
            } ${(hazardKey && (hazardKey.includes('flood') || hazardKey.includes('drought'))) ? 'gap-3 lg:gap-4' : 'gap-4 lg:gap-6'}`}>
            {/* 1. Hazard Base Info */}
            {hasHazard && (
              <div className={`flex flex-col justify-center ${(hazardKey && (hazardKey.includes('flood') || hazardKey.includes('drought'))) ? 'min-w-[90px]' : 'min-w-[140px]'}`}>
                <div className={`font-extrabold mb-1.5 tracking-widest uppercase truncate ${darkMode ? 'text-gray-300' : 'text-slate-700'
                  } ${(hazardKey && (hazardKey.includes('flood') || hazardKey.includes('drought'))) ? 'text-[7px]' : 'text-[8px]'}`}>
                  Hazard: {hazardInfo.label} ({hazardInfo.unit || 'Index'})
                </div>
                <div
                  className={`h-1.5 w-full rounded-full mb-1 shadow-sm border ${darkMode ? 'border-gray-700/50' : 'border-slate-200/50'}`}
                  style={{
                    background: `linear-gradient(to right, ${hazardInfo.colorStops.map(s => s[1]).join(',')})`
                  }}
                ></div>
                <div className={`flex justify-between font-bold ${darkMode ? 'text-white' : 'text-slate-900'
                  } ${(hazardKey && (hazardKey.includes('flood') || hazardKey.includes('drought'))) ? 'text-[8px]' : 'text-[9px]'}`}>
                  <span>{format(rasterStats.min)} {hazardInfo.unit}</span>
                  <span>{format(rasterStats.max)} {hazardInfo.unit}</span>
                </div>
              </div>
            )}

            {/* Divider 1 to 2 */}
            {hasHazard && (
              <div className={`w-[1px] self-stretch my-1 rounded-full ${darkMode ? 'bg-gray-800' : 'bg-slate-200'}`}></div>
            )}

            {/* 2. Curve / Interaction Panel */}
            {hasHazard && (
              <div className="flex shrink-0 min-w-min">
                {renderInteractionPanel()}
              </div>
            )}

            {/* Divider 2 to 3 */}
            {hasHazard && hasExposure && (
              <div className={`w-[1px] self-stretch my-1 rounded-full ${darkMode ? 'bg-gray-800' : 'bg-slate-200'}`}></div>
            )}

            {/* 3. Eksposur */}
            {hasExposure && Object.keys(EXPOSURE_COLORS).some(key => infraLayers[key]) && (
              <div className={`flex flex-col justify-center ${!hasHazard ? 'min-w-[150px] md:min-w-[200px] py-0.5 md:py-1' : 'min-w-[80px]'}`}>
                <div className={`font-black mb-1 md:mb-2 text-[6.5px] md:text-[7.5px] tracking-[0.2em] uppercase flex items-center gap-1.5 ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>
                  {!hasHazard && <Layers size={7} strokeWidth={2.5} />}
                  Eksposur
                </div>
                <div className={`grid ${!hasHazard ? 'grid-cols-2 lg:grid-cols-4 gap-x-3 md:gap-x-4 gap-y-1.5 md:gap-y-2' : 'grid-cols-2 gap-x-2 gap-y-0.5'} ${darkMode ? 'text-gray-200' : 'text-slate-600'}`}>
                  {['healthcare', 'educational', 'electricity', 'airport', 'hotel', 'bmn', 'residential'].map(type => {
                    if (!infraLayers[type]) return null;
                    return (
                      <div key={type} className="flex items-center gap-1 md:gap-1.5 group cursor-default">
                        <div
                          className={`w-1 md:w-1.5 h-1 md:h-1.5 rounded-full border border-white/20 ring-[0.5px] md:ring-[1px] transition-transform group-hover:scale-125 ${darkMode ? 'ring-gray-800' : 'ring-slate-100'}`}
                          style={{ backgroundColor: EXPOSURE_COLORS[type] }}
                        ></div>
                        <span className="text-[6.5px] md:text-[7.5px] font-bold whitespace-nowrap">
                          {type.toLowerCase() === 'bmn' ? 'BMN' : type.charAt(0).toUpperCase() + type.slice(1).toLowerCase()}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Divider 3 to 4 */}
            {hasExposure && showBoundaryPanel && (
              <div className="hidden"></div>
            )}
          </div>
        </div>
      )}

      {showBoundaryPanel && (
        <>
          {/* Toggle Sidebar Button */}
          {!isAalSidebarOpen && (
            <button
              onClick={() => setIsAalSidebarOpen(true)}
              className="absolute right-0 top-6 md:top-4 z-[1015] bg-orange-500 text-white p-1.5 md:p-2 rounded-l-lg shadow-xl hover:bg-orange-600 transition-all animate-in slide-in-from-right duration-300"
            >
              <ChevronLeft className="w-5 h-5 md:w-7 md:h-7" />
            </button>
          )}

          {/* Sidebar Panel */}
          <div
            className={`absolute top-0 right-0 z-[1020] h-full flex flex-col max-w-[85vw] md:max-w-none backdrop-blur-sm shadow-[-4px_0_24px_rgb(0,0,0,0.08)] border-l transition-transform duration-300 ${darkMode ? 'bg-[#1E2023] border-gray-800' : 'bg-white border-slate-200'
              }`}
            style={{
              width: `${sidebarWidth}px`,
              transform: isAalSidebarOpen ? 'translateX(0)' : 'translateX(100%)',
              transitionProperty: isResizingRef.current ? 'none' : 'transform'
            }}
          >
            {/* Drag Handle */}
            <div
              onMouseDown={() => isResizingRef.current = true}
              className="absolute top-0 left-0 w-1.5 h-full cursor-col-resize hover:bg-blue-400/50 transition-colors z-[2010]"
            />

            {/* ΓöÇΓöÇΓöÇ Header ΓöÇΓöÇΓöÇ */}
            <div className={`px-4 py-3 border-b flex items-start justify-between gap-2 ${darkMode ? 'border-gray-800' : 'border-slate-100'}`}>
              <div className="flex-1 pr-1">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsAalSidebarOpen(false)}
                    className={`p-1 rounded-sm transition-colors ${darkMode ? 'text-gray-500 hover:text-gray-300 bg-gray-800 hover:bg-gray-700' : 'text-slate-400 hover:text-slate-700 bg-slate-50 hover:bg-slate-100'
                      }`}
                    title="Sembunyikan Panel AAL"
                  >
                    <ChevronRight size={14} strokeWidth={2.5} />
                  </button>
                  <div className={`font-extrabold text-[10px] tracking-widest uppercase truncate leading-tight mt-0.5 ${darkMode ? 'text-gray-200' : 'text-slate-700'}`}>{hasAAL ? 'Kalkulasi AAL' : 'Direct Loss'}</div>
                </div>
                {selectedCityFeature ? (
                  <div className="flex items-center gap-1 mt-1 flex-wrap">
                    <span className={`text-[10px] font-bold leading-tight mr-1 truncate max-w-[100px] ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>{selectedCityFeature.properties.id_kota || 'Kota'}</span>
                    <button onClick={onClearCity} className={`text-[8px] border px-1.5 py-0.5 rounded transition-colors flex-shrink-0 ${darkMode ? 'text-gray-400 hover:text-red-400 bg-gray-800 border-gray-700 hover:bg-red-900/20 hover:border-red-900/30' : 'text-slate-400 hover:text-red-500 bg-slate-50 border-slate-100 hover:bg-red-50 hover:border-red-100'
                      }`}>Γ£ò Reset</button>
                  </div>
                ) : (
                  <div className={`text-[9px] mt-1 truncate ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>Total Semua Kota/Kabupaten</div>
                )}
              </div>
              <div className="flex flex-col gap-2 flex-shrink-0 items-end">
                <select
                  className={`text-[10px] font-semibold py-1 pl-2.5 pr-6 rounded-md focus:outline-none focus:ring-1 appearance-none cursor-pointer w-full shadow-sm transition-all border ${darkMode
                      ? 'bg-gray-800 border-gray-700 text-gray-200 focus:border-blue-500 focus:ring-blue-500'
                      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-400 focus:ring-blue-400'
                    }`}
                  style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23${darkMode ? '94a3b8' : '64748b'}' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 4px center', backgroundSize: '10px' }}
                  value={selectedCityFeature ? selectedCityFeature.properties.id_kota : ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (!val) {
                      onSelectCity(null);
                    } else {
                      const feature = activeBoundaryData.features.find(f => f.properties.id_kota === val);
                      onSelectCity(feature);
                    }
                  }}
                >
                  <option value="">Pilih Kota...</option>
                  {activeBoundaryData.features
                    .map(f => f.properties.id_kota)
                    .filter(Boolean)
                    .sort()
                    .map(city => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                </select>
              </div>
            </div>

            {/* ΓöÇΓöÇΓöÇ Color Legend ΓöÇΓöÇΓöÇ */}
            <div className="px-4 pt-3 pb-2">
              {(() => {
                let hazPrefix = '';
                let rp = '';

                if (selectedRpId) {
                  const parts = selectedRpId.split('_');
                  rp = parts[parts.length - 1];
                  if (rp === 'default') rp = '';
                }

                let metric = '';
                let vals = [];

                if (hasDirectLoss) {
                  const isFloodSawah = selectedGroup === 'banjir' && floodView === 'sawah';

                  if (isFloodSawah && floodSawahData) {
                    const isCC = selectedRpId && selectedRpId.includes('comp');
                    const ccKey = isCC ? 'rc' : 'r';
                    const rpMatch = selectedRpId ? selectedRpId.match(/(\d+)/) : null;
                    const rpKey = rpMatch ? rpMatch[1] : null;
                    if (rpKey && floodSawahData[ccKey]?.[rpKey]) {
                      const rows = floodSawahData[ccKey][rpKey];
                      vals = rows.map(r => r[floodSawahYear] || 0).filter(v => typeof v === 'number' && !isNaN(v));
                    }
                  } else if (selectedGroup === 'kekeringan' && floodView === 'sawah' && droughtSawahData) {
                    // Sawah Drought - NEW
                    const isCC = selectedRpId && selectedRpId.includes('mme');
                    const ccKey = isCC ? 'mme' : 'gpm';
                    const rpPart = selectedRpId ? selectedRpId.split('_').pop() : null;
                    const rpKey = rpPart && rpPart !== 'default' ? rpPart : null;
                    if (rpKey && droughtSawahData[ccKey]?.[rpKey]) {
                      const rows = droughtSawahData[ccKey][rpKey];
                      vals = rows.map(r => r[droughtLossYear] || 0).filter(v => typeof v === 'number' && !isNaN(v));
                    }
                  } else {
                    if (selectedGroup === 'banjir') {
                      let hz = (selectedRpId && selectedRpId.includes('comp')) ? 'rc' : 'r';
                      if (rp) metric = `dl_sum_${hz}_${rp}`;
                    }
                    else if (selectedGroup === 'earthquake') {
                      if (rp) metric = `pga_${rp}`;
                    }
                    else if (selectedGroup === 'tsunami') {
                      metric = `dl_sum_inundansi`;
                    }

                    if (metric) {
                      const isEq = selectedGroup === 'earthquake';
                      vals = activeBoundaryData.features.map(f => {
                        if (isEq) {
                          let dlExp = f.properties.dl_exposure || {};
                          if (typeof dlExp === 'string') { try { dlExp = JSON.parse(dlExp); } catch { dlExp = {}; } }
                          const catData = dlExp.total || {};
                          return (catData[metric] || 0) * 100;
                        }
                        return f.properties[metric] || 0;
                      }).filter(v => typeof v === 'number' && !isNaN(v));
                    }
                  }
                } else if (hasAAL) {
                  let hazPrefix = '';
                  if (selectedGroup === 'banjir') hazPrefix = (selectedRpId && selectedRpId.includes('comp')) ? 'rc' : 'r';
                  else if (selectedGroup === 'earthquake') hazPrefix = 'pga';
                  else if (selectedGroup === 'tsunami') hazPrefix = 'inundansi';

                  metric = `aal_${hazPrefix}_${activeAalExposure || 'total'}`;
                  vals = activeBoundaryData.features.map(f => f.properties[metric] || 0).filter(v => typeof v === 'number' && !isNaN(v));
                }

                if (vals.length === 0) return (
                  <div className={`flex items-center gap-1.5 ${darkMode ? 'opacity-40' : 'opacity-60'}`}>
                    <span className={`inline-block w-4 h-2 rounded-[2px] ${darkMode ? 'bg-gray-700' : 'bg-slate-200'}`} />
                    <span className={`text-[8px] font-semibold tracking-wider italic ${darkMode ? 'text-gray-500' : 'text-slate-400'}`}>
                      {!selectedRpId ? (darkMode ? 'Pilih Return Period...' : 'Pilih Return Period...') : 'Rp 0 - Rp 0'}
                    </span>
                  </div>
                );

                const colorsAAL = ['#1a9850', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027', '#7f0000'];

                const nClass = vals.length > 30 ? 6 : 5;
                let grades = jenks(vals, nClass).sort((a, b) => a - b);
                const halfCount = Math.ceil(nClass / 2);
                const col1 = [], col2 = [];
                const isEarthquakeRatio = hasDirectLoss && selectedGroup === 'earthquake';

                Array.from({ length: nClass }).forEach((_, i) => {
                  let lowDisplay, highDisplay;
                  if (isEarthquakeRatio) {
                    lowDisplay = grades[i].toFixed(4) + '%';
                    highDisplay = grades[i + 1].toFixed(4) + '%';
                  } else {
                    lowDisplay = `Rp ${(Math.ceil(grades[i] / 1e6)).toLocaleString('id-ID')}M`;
                    highDisplay = `Rp ${(Math.ceil(grades[i + 1] / 1e6)).toLocaleString('id-ID')}M`;
                  }

                  const item = (
                    <div key={i} className="flex items-center gap-2">
                      <span className="inline-block w-5 h-2.5 rounded-[2px] shadow-sm" style={{ background: colorsAAL[i] }} />
                      <span className={`text-[8px] font-semibold tracking-wider whitespace-nowrap ${darkMode ? 'text-gray-400' : 'text-slate-600'}`}>{lowDisplay} - {highDisplay}</span>
                    </div>
                  );
                  if (i < halfCount) col1.push(item); else col2.push(item);
                });
                return (
                  <div className="flex gap-x-6">
                    <div className="flex flex-col gap-1.5">{col1}</div>
                    <div className="flex flex-col gap-1.5">{col2}</div>
                  </div>
                );
              })()}

              {/* Proportional Map Note */}
              {infraLayers?.modelHazard && (hasDirectLoss || hasAAL) && (
                <div className={`mt-3 text-[8px] p-2 rounded border flex items-start gap-1.5 leading-relaxed ${darkMode
                    ? 'text-orange-300/80 bg-orange-950/20 border-orange-900/30'
                    : 'text-slate-500 bg-orange-50/50 border-orange-100/50'
                  }`}>
                  <Info size={10} className={`${darkMode ? 'text-orange-500/70' : 'text-orange-400'} mt-[1px] shrink-0`} />
                  <span>Area kotak batas diubah menjadi transparan. Warna dan ukuran <strong>lingkaran di tengah batas</strong> merepresentasikan besaran nilai AAL/Direct Loss secara proporsional.</span>
                </div>
              )}
            </div>

            {/* ΓöÇΓöÇΓöÇ Bar Charts ΓöÇΓöÇΓöÇ */}
            <div className="overflow-y-auto flex-1 custom-scrollbar">
              {hasDirectLoss && selectedGroup === 'kekeringan' && (
                <DroughtSawahChartPanel
                  selectedGroup={selectedGroup}
                  selectedCityFeature={selectedCityFeature}
                  onOpenDownload={onOpenDownload}
                />
              )}

              {hasDirectLoss && selectedGroup === 'banjir' && floodView === 'sawah' && (
                <FloodSawahChartPanel
                  selectedCityFeature={selectedCityFeature}
                  floodData={floodSawahData}
                  selectedSawahYear={floodSawahYear}
                  setSelectedSawahYear={setFloodSawahYear}
                  onOpenDownload={onOpenDownload}
                />
              )}

              {hasDirectLoss && (selectedGroup !== 'kekeringan' && (selectedGroup !== 'banjir' || floodView === 'building')) && (
                <DirectLossChartPanel
                  boundaryData={boundaryDataDL}
                  selectedGroup={selectedGroup}
                  selectedRpId={selectedRpId}
                  selectedCityFeature={selectedCityFeature}
                  onOpenTable={onOpenTable}
                  onOpenDownload={onOpenDownload}
                />
              )}

              {hasAAL && (
                <AALChartPanel
                  boundaryData={boundaryDataAAL}
                  selectedCityFeature={selectedCityFeature}
                  rekapData={boundaryDataDL}
                  selectedGroup={selectedGroup}
                  onOpenDownload={onOpenDownload}
                  onOpenTable={onOpenTable}
                />
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default ReactLegendOverlay;
