import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, Cell, LineChart, Line
} from 'recharts';
import { ShieldAlert, Activity, DollarSign, TrendingUp, Download, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000/api/crypto';

export default function App() {
  const [data, setData] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'market_cap', direction: 'desc' });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [coinHistory, setCoinHistory] = useState([]);

  const fetchCoinHistory = async (symbol) => {
    try {
      setSelectedCoin(symbol);
      const res = await axios.get(`${API_BASE_URL}/history/${symbol}`);
      const hist = res.data.history.map(pt => ({
        ...pt,
        formattedTime: new Date(pt.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
      }));
      setCoinHistory(hist);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/latest`);
      if (response.data && response.data.data) {
        const filteredData = response.data.data.filter(
          item => item.risk_explanation !== "Flagged as anomalous due to unusual combination of liquidity and volatility."
        );
        setData(filteredData);
        setMetrics(response.data.metrics);
        setLastUpdated(new Date());
      }
      setError(null);
    } catch (err) {
      setError('Failed to fetch data. Ensure backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const downloadCSV = () => {
    window.location.href = `${API_BASE_URL}/history`;
  };

  const sortedData = useMemo(() => {
    let sortableItems = [...data];
    if (sortConfig.key) {
      sortableItems.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Handle nulls
        if (aValue === null) return 1;
        if (bValue === null) return -1;

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sortableItems;
  }, [data, sortConfig]);

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Derive chart data
  const marketCapDistribution = useMemo(() => {
    const counts = { 'Large-Cap': 0, 'Mid-Cap': 0, 'Small-Cap': 0 };
    data.forEach(item => { if (item.cap_category) counts[item.cap_category]++; });
    return Object.keys(counts).map(k => ({ name: k, count: counts[k] }));
  }, [data]);

  const riskDistribution = useMemo(() => {
    const counts = { 'Low': 0, 'Medium': 0, 'High': 0 };
    data.forEach(item => { if (item.ml_risk_category) counts[item.ml_risk_category]++; });
    return [
      { name: 'Low Risk', count: counts['Low'], fill: '#00ff88' },
      { name: 'Medium Risk', count: counts['Medium'], fill: '#ffcc00' },
      { name: 'High Risk', count: counts['High'], fill: '#ff3344' }
    ];
  }, [data]);

  const anomaliesCount = data.filter(d => d.is_anomaly).length;

  return (
    <>
      <div className="mesh-gradient"></div>
      <div className="noise-bg"></div>

      <div className="min-h-screen text-[#e2e8f0] p-6 relative z-10 font-mono">
        <div className="max-w-7xl mx-auto space-y-6">

          {/* Header */}
          <header className="flex flex-col md:flex-row justify-between items-center glass-panel hyper-border p-6 rounded-2xl">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3 tracking-wider uppercase text-white">
                <Activity className="w-8 h-8 text-[#3d5afe]" />
                Kryptos Intelligence
              </h1>
              <p className="text-slate-400 mt-2 text-sm tracking-wide">
                Tactical Market Capitalization Segmentation & ML-Driven Risk Analysis.
              </p>
            </div>
            <div className="flex gap-4 mt-4 md:mt-0 items-center">
              <div className="text-right mr-4 flex flex-col justify-center">
                <span className="text-xs text-[#3d5afe] uppercase tracking-widest font-bold">System Status</span>
                <span className="text-sm flex items-center justify-end gap-2 text-white">
                  <div className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse shadow-[0_0_8px_#00ff88]"></div>
                  {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Awaiting Link...'}
                </span>
              </div>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-black/30 hover:bg-[#3d5afe]/20 border border-white/10 hover:border-[#3d5afe]/50 text-white rounded flex items-center gap-2 transition"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-[#00ff88]' : ''}`} />
                SYNC
              </button>
              <button
                onClick={downloadCSV}
                className="px-4 py-2 bg-[#3d5afe]/20 hover:bg-[#3d5afe]/40 text-[#3d5afe] border border-[#3d5afe]/50 rounded flex items-center gap-2 transition shadow-[0_0_15px_rgba(61,90,254,0.3)] cursor-pointer"
              >
                <Download className="w-4 h-4" />
                DUMP DATA
              </button>
            </div>
          </header>

          {error && (
            <div className="glass-panel border-l-4 border-[#ff3344] text-[#ff3344] p-4 flex items-center gap-3 rounded-lg">
              <AlertTriangle className="w-5 h-5" />
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Main Stat Cards */}
            <div className="glass-panel p-6 flex items-center gap-4 group rounded-xl hover:border-[#3d5afe]/30 transition">
              <div className="p-3 bg-[#3d5afe]/10 border border-[#3d5afe]/30 text-[#3d5afe] rounded animate-pulse">
                <DollarSign className="w-6 h-6" />
              </div>
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">Assets Tracked</p>
                <p className="text-2xl font-bold text-white tracking-widest">{data.length}</p>
              </div>
            </div>

            <div className="glass-panel p-6 flex items-center gap-4 group rounded-xl hover:border-[#ff3344]/30 transition">
              <div className="p-3 bg-[#ff3344]/10 border border-[#ff3344]/30 text-[#ff3344] rounded">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">High Risk Flag</p>
                <p className="text-2xl font-bold text-white tracking-widest">{riskDistribution.find(r => r.name === 'High Risk')?.count || 0}</p>
              </div>
            </div>

            <div className="glass-panel p-6 flex items-center gap-4 group rounded-xl hover:border-[#ffcc00]/30 transition">
              <div className="p-3 bg-[#ffcc00]/10 border border-[#ffcc00]/30 text-[#ffcc00] rounded">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest">Anomalies</p>
                <p className="text-2xl font-bold text-white tracking-widest">{anomaliesCount}</p>
              </div>
            </div>

            {/* Metrics Base */}
            <div className="glass-panel p-6 flex flex-col justify-center rounded-xl">
              <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#00ff88]" />
                RF Model Integrity
              </p>
              {metrics && metrics.accuracy !== undefined ? (
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-black/50 border border-white/5 p-2 rounded flex flex-col">
                    <span className="text-slate-500 text-[10px] uppercase tracking-wider">Accuracy</span>
                    <span className="text-[#00ff88] font-bold">{(metrics.accuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="bg-black/50 border border-white/5 p-2 rounded flex flex-col">
                    <span className="text-slate-500 text-[10px] uppercase tracking-wider">F1-Score</span>
                    <span className="text-[#00ff88] font-bold">{(metrics.f1_score * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ) : (
                <p className="text-[10px] text-slate-500 p-2 bg-black/40 rounded border border-white/5 uppercase tracking-widest">Calculating variance...</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scatter Plot: Liquidity vs Volatility */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-[10px] font-bold uppercase tracking-widest mb-4 text-slate-400 flex items-center gap-2 border-b border-white/10 pb-3">
                <TrendingUp className="w-4 h-4 text-[#3d5afe]" />
                Risk Vector Matrix (Liq/Vol)
              </h3>
              <div className="h-72">
                {data.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis type="number" dataKey="liquidity_ratio" name="Liquidity Ratio" stroke="#64748b" tickFormatter={(v) => v.toExponential(1)} fontSize={10} />
                      <YAxis type="number" dataKey="volatility" name="Volatility" stroke="#64748b" tickFormatter={(v) => v.toFixed(3)} fontSize={10} />
                      <ZAxis type="category" dataKey="symbol" name="Coin" />
                      <RechartsTooltip
                        cursor={{ strokeDasharray: '3 3', stroke: '#3d5afe' }}
                        contentStyle={{ backgroundColor: 'rgba(5, 6, 8, 0.95)', border: '1px solid rgba(61,90,254,0.3)', color: '#e2e8f0', borderRadius: '4px', fontFamily: 'JetBrains Mono' }}
                        itemStyle={{ color: '#e2e8f0' }}
                        labelStyle={{ color: '#3d5afe', fontWeight: 'bold' }}
                        formatter={(val, name) => name === 'Coin' ? val : (typeof val === 'number' ? val.toExponential(3) : val)}
                      />
                      <Scatter name="Assets" data={data} fill="#3d5afe">
                        {data.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.is_anomaly ? '#ff3344' : (entry.ml_risk_category === 'High' ? '#ffcc00' : '#3d5afe')} />
                        ))}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-[10px] uppercase text-slate-600 tracking-widest">No nodes connected.</div>
                )}
              </div>
              <div className="flex gap-4 justify-center text-[10px] text-slate-500 mt-2 uppercase tracking-widest">
                <span className="flex items-center gap-2"><div className="w-2 h-2 bg-[#3d5afe]"></div> Nominal</span>
                <span className="flex items-center gap-2"><div className="w-2 h-2 bg-[#ffcc00] shadow-[0_0_5px_#ffcc00]"></div> High Risk</span>
                <span className="flex items-center gap-2"><div className="w-2 h-2 bg-[#ff3344] shadow-[0_0_5px_#ff3344]"></div> Anomaly</span>
              </div>
            </div>

            {/* Bar Chart: Market Cap Segmentation */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-[10px] font-bold uppercase tracking-widest mb-4 text-slate-400 flex items-center gap-2 border-b border-white/10 pb-3">
                <Activity className="w-4 h-4 text-[#00ff88]" />
                Volume Segmentation
              </h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={marketCapDistribution} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={10} />
                    <RechartsTooltip
                      cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                      contentStyle={{ backgroundColor: 'rgba(5, 6, 8, 0.95)', border: '1px solid rgba(255,255,255,0.1)', color: '#e2e8f0', borderRadius: '4px', fontFamily: 'JetBrains Mono' }}
                      itemStyle={{ color: '#e2e8f0' }}
                      labelStyle={{ color: '#00ff88', fontWeight: 'bold' }}
                    />
                    <Bar dataKey="count" fill="#3d5afe" radius={[2, 2, 0, 0]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {selectedCoin && (
            <div className="glass-panel p-6 rounded-xl animate-in fade-in duration-300">
              <div className="flex justify-between items-center mb-4 border-b border-white/10 pb-3">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-[#00ff88] flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  {selectedCoin.toUpperCase()} — 7D Market Cap Vector
                </h3>
                <button
                  onClick={() => setSelectedCoin(null)}
                  className="text-slate-500 hover:text-white text-[10px] uppercase font-bold tracking-widest cursor-pointer transition"
                >
                  Close [X]
                </button>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={coinHistory} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="formattedTime" stroke="#64748b" fontSize={10} minTickGap={30} />
                    <YAxis
                      stroke="#64748b"
                      fontSize={10}
                      tickFormatter={(v) => `$${(v / 1e9).toFixed(1)}B`}
                      domain={['auto', 'auto']}
                    />
                    <RechartsTooltip
                      cursor={{ stroke: 'rgba(255,255,255,0.1)' }}
                      contentStyle={{ backgroundColor: 'rgba(5, 6, 8, 0.95)', border: '1px solid rgba(0,255,136,0.5)', color: '#e2e8f0', borderRadius: '4px', fontFamily: 'JetBrains Mono' }}
                      itemStyle={{ color: '#00ff88' }}
                      labelStyle={{ color: '#3d5afe', fontWeight: 'bold', marginBottom: '4px' }}
                      formatter={(val) => [`$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Market Cap']}
                    />
                    <Line type="monotone" dataKey="market_cap" stroke="#00ff88" strokeWidth={2} dot={false} activeDot={{ r: 6, fill: '#00ff88', stroke: '#050608', strokeWidth: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Data Table */}
          <div className="glass-panel overflow-hidden rounded-xl border-t-2 border-t-[#3d5afe]/50">
            <div className="p-4 border-b border-white/5 bg-black/40 flex justify-between items-center">
              <h3 className="text-sm font-bold tracking-widest uppercase text-[#3d5afe] flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#3d5afe] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-[#3d5afe]"></span>
                </span>
                Live Asset Feed
              </h3>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest">Click headers to arrange</span>
            </div>
            <div className="overflow-x-auto min-h-[300px]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-white/5 text-slate-400 text-[10px] uppercase tracking-widest">
                    <th className="p-4 font-bold hover:text-white cursor-pointer transition border-b border-white/5" onClick={() => requestSort('symbol')}>Identifier</th>
                    <th className="p-4 font-bold hover:text-white cursor-pointer transition text-right border-b border-white/5" onClick={() => requestSort('price')}>Price (USD)</th>
                    <th className="p-4 font-bold hover:text-white cursor-pointer transition text-right border-b border-white/5" onClick={() => requestSort('market_cap')}>Market Cap</th>
                    <th className="p-4 font-bold hover:text-white cursor-pointer transition border-b border-white/5" onClick={() => requestSort('cap_category')}>Classification</th>
                    <th className="p-4 font-bold hover:text-white cursor-pointer transition text-center border-b border-white/5" onClick={() => requestSort('ml_risk_category')}>Threat Level</th>
                    <th className="p-4 font-bold border-b border-white/5">System Log</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {sortedData.map((row, i) => (
                    <tr key={i} onClick={() => fetchCoinHistory(row.symbol)} className={`cursor-pointer hover:bg-slate-800/40 transition-colors ${row.is_anomaly ? 'bg-[#ff3344]/5' : ''}`}>
                      <td className="p-4 flex items-center gap-3">
                        <div className="w-10 h-10 rounded border border-white/10 bg-black/50 flex flex-col items-center justify-center font-bold text-[#3d5afe]">
                          <span className="text-sm">{row.symbol?.substring(0, 3).toUpperCase()}</span>
                        </div>
                        <div>
                          <div className="font-bold text-white tracking-widest">{row.symbol?.toUpperCase()}</div>
                          <div className="text-[10px] text-slate-500 uppercase">{row.name}</div>
                        </div>
                      </td>
                      <td className="p-4 text-right text-slate-300 font-bold">${row.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</td>
                      <td className="p-4 text-right text-slate-300">${row.market_cap?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${row.cap_category === 'Large-Cap' ? 'bg-[#3d5afe]/10 text-[#3d5afe] border-[#3d5afe]/20' :
                          row.cap_category === 'Mid-Cap' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                            'bg-slate-500/10 text-slate-400 border-slate-500/20'
                          }`}>
                          {row.cap_category || 'N/A'}
                        </span>
                      </td>
                      <td className="p-4 text-center">
                        <span className={`px-3 py-1 rounded text-[10px] font-bold uppercase tracking-widest inline-block ${row.ml_risk_category === 'High' ? 'bg-[#ff3344]/10 text-[#ff3344] border border-[#ff3344]/30 shadow-[0_0_10px_rgba(255,51,68,0.2)]' :
                          row.ml_risk_category === 'Medium' ? 'bg-[#ffcc00]/10 text-[#ffcc00] border border-[#ffcc00]/30' :
                            row.ml_risk_category === 'Low' ? 'bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30 shadow-[0_0_10px_rgba(0,255,136,0.1)]' :
                              'bg-slate-800 text-slate-500 border border-slate-700'
                          }`}>
                          {row.ml_risk_category || 'N/A'}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          <span className={`text-[11px] font-bold ${row.is_anomaly ? 'text-[#ff3344]' : 'text-slate-400'}`}>
                            {row.risk_explanation ? `> ${row.risk_explanation}` : '> NOMINAL'}
                          </span>
                          {row.is_anomaly && (
                            <span className="inline-flex items-center gap-2 text-[10px] text-[#ffcc00] font-bold uppercase tracking-widest mt-1">
                              <AlertTriangle className="w-3 h-3 animate-pulse" />
                              Iso-Forest Match
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {sortedData.length === 0 && !loading && (
                <div className="p-8 text-center text-slate-600 border-t border-white/5 uppercase tracking-widest text-[10px]">
                  System waiting for data streams.
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
