import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement, BarElement,
  Title, Tooltip, Legend, ScatterController
} from 'chart.js';
import { Bar, Scatter } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, BarElement,
  Title, Tooltip, Legend, ScatterController
);

import CandlestickChart from './CandlestickChart';
import CorrelationMatrix from './CorrelationMatrix';
import CoinGrowthChart from './CoinGrowthChart';

const API_URL = "http://127.0.0.1:8000/api/dashboard";

function App() {
  const [data, setData] = useState([]);
  const [summary, setSummary] = useState({});
  const [metrics, setMetrics] = useState({});
  const [corrMatrix, setCorrMatrix] = useState(null);
  const [selectedCoin, setSelectedCoin] = useState('BTC');
  const [lastUpdated, setLastUpdated] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await axios.get(API_URL);
      if (response.data.status === "success") {
        setData(response.data.data);
        setSummary(response.data.summary);
        setMetrics(response.data.metrics);
        setCorrMatrix(response.data.corr_matrix);
        setLastUpdated(new Date(response.data.timestamp).toLocaleTimeString());
      }
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const triggerFetch = async () => {
    try {
      setLoading(true);
      await axios.post("http://127.0.0.1:8000/api/fetch");
      setTimeout(fetchData, 2000); // Wait for backend to update DB
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  // Prepare chart data
  const marketCapData = useMemo(() => {
    const sorted = [...data].sort((a, b) => b.market_cap - a.market_cap).slice(0, 20); // Top 20 for visibility
    return {
      labels: sorted.map(d => d.symbol),
      datasets: [
        {
          label: 'Market Cap ($)',
          data: sorted.map(d => d.market_cap),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderRadius: 4,
        }
      ]
    };
  }, [data]);

  const scatterData = useMemo(() => {
    return {
      datasets: [
        {
          label: 'Liquidity vs Volatility',
          data: data.map(d => ({
            x: d.norm_liquidity,
            y: d.norm_volatility,
            symbol: d.symbol,
            risk: d.risk_score
          })),
          backgroundColor: data.map(d =>
            d.is_anomaly ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.4)'
          ),
          pointRadius: data.map(d => d.is_anomaly ? 6 : 3),
          pointBorderColor: 'rgba(42, 46, 57, 0.8)',
          pointBorderWidth: 1,
        }
      ]
    };
  }, [data]);

  const scatterOptions = {
    plugins: {
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.raw.symbol} - Risk: ${(ctx.raw.risk).toFixed(2)}`
        }
      }
    },
    scales: { x: { title: { display: true, text: 'Normalized Liquidity' } }, y: { title: { display: true, text: 'Normalized Volatility' } } }
  };

  const downloadCSV = () => {
    if (data.length === 0) return;
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(","),
      ...data.map(row => headers.map(h => row[h]).join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "crypto_surveillance_data.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading && data.length === 0) {
    return <div className="dashboard-container"><div style={{ margin: 'auto' }}>Loading Intelligence Engine...</div></div>;
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <div>
          <h1>KRYPTOS Intelligence</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Real-Time ML Market Segmentation & Risk Profiling</p>
        </div>
        <div>
          <span className="status-badge" style={{ marginRight: '1rem' }}>
            <span style={{ width: '8px', height: '8px', background: 'var(--success-color)', borderRadius: '50%', display: 'inline-block', marginRight: '0.5rem' }}></span>
            Live (Updates 60s)
          </span>
          <button className="action-btn" style={{ marginRight: '1rem' }} onClick={downloadCSV}>Export CSV</button>
          <button className="action-btn" onClick={triggerFetch}>Force Fetch</button>
        </div>
      </header>

      <div className="grid">
        <div className="card">
          <div className="card-title">RF Model Validation</div>
          <div className="metric-value">{metrics.accuracy ? (metrics.accuracy * 100).toFixed(0) : 0}% Acc</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Train-Test Validated (Random Forest)</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.5rem' }}>
            F1: {metrics.f1 || 0} | P: {metrics.precision || 0} | R: {metrics.recall || 0}
          </div>
        </div>
        <div className="card">
          <div className="card-title">Assets Tracked</div>
          <div className="metric-value">{summary.total_coins || 0}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Segmented by dynamic thresholds</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.5rem' }}>
            Small: &lt;${(summary.small_cap_threshold / 1e6).toFixed(1)}M | Large: &gt;${(summary.large_cap_threshold / 1e6).toFixed(1)}M
          </div>
        </div>
        <div className="card">
          <div className="card-title">Anomalies Detected</div>
          <div className="metric-value" style={{ color: 'var(--danger-color)' }}>
            {data.filter(d => d.is_anomaly).length}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Isolated via Isolation Forest (-1 outliers)</div>
        </div>
      </div>

      <div className="grid-large">
        <div className="card">
          <div className="card-title" style={{ marginBottom: '0.25rem' }}>Market Cap Distribution (Top 20)</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem', marginTop: 0 }}>Displays the total market capitalization for the top 20 cryptocurrencies to identify market dominance.</p>
          <div className="chart-container">
            <Bar data={marketCapData} options={{ maintainAspectRatio: false, plugins: { legend: { display: false } } }} />
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: '0.25rem' }}>Risk Matrix: Liquidity vs Volatility</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem', marginTop: 0 }}>Evaluates asset risk based on liquidity and volatility. Red points highlight ML-detected anomalies.</p>
          <div className="chart-container">
            <Scatter data={scatterData} options={{ maintainAspectRatio: false, ...scatterOptions }} />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card" style={{ flex: '1 1 50%', minWidth: 0 }}>
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <span>Advanced Candlestick Chart (1H)</span>
            <select
              value={selectedCoin}
              onChange={(e) => setSelectedCoin(e.target.value)}
              style={{ background: 'var(--bg-tertiary)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '0.25rem 0.5rem', outline: 'none' }}
            >
              {data.slice(0, 50).map(d => <option key={d.symbol} value={d.symbol}>{d.symbol}</option>)}
            </select>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem', marginTop: 0 }}>Visualizes Open, High, Low, and Close prices over time for detailed technical analysis.</p>
          <div className="chart-container">
            <CandlestickChart symbol={selectedCoin} />
          </div>
        </div>

        <div className="card" style={{ flex: '1 1 50%', minWidth: 0 }}>
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <span>Cumulative Market Cap Growth (%) vs Time</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem', marginTop: 0 }}>Tracks the percentage growth of the selected asset's market cap to highlight performance trends.</p>
          <div className="chart-container">
            <CoinGrowthChart symbol={selectedCoin} />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div className="card-title" style={{ width: '100%', textAlign: 'center', marginBottom: '0.25rem' }}>Cross-Asset Correlation Matrix (Top 15 Returns)</div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1rem', marginTop: 0, textAlign: 'center' }}>Shows correlation between assets' returns. Positive (green) moves together; negative (red) diverges.</p>
        <div style={{ padding: '0.5rem 0', display: 'flex', justifyContent: 'center', width: '100%' }}>
          <CorrelationMatrix matrix={corrMatrix} />
        </div>
      </div>

      <div className="card">
        <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Live Assets Feed (Last Updated: {lastUpdated})</span>
          <span>Red background indicates ML Anomaly</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Asset</th>
                <th>Price ($)</th>
                <th>24h Change</th>
                <th>Market Segment</th>
                <th>Liq Ratio</th>
                <th>Vol (Std)</th>
                <th>Risk Score</th>
                <th>Risk Category</th>
              </tr>
            </thead>
            <tbody>
              {data.map(row => (
                <tr key={row.symbol} className={row.is_anomaly ? 'anomaly-row' : ''}>
                  <td style={{ fontWeight: 600 }}>{row.symbol} <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginLeft: '0.5rem' }}>{row.name}</span></td>
                  <td>${row.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</td>
                  <td style={{ color: row.percent_change_24h >= 0 ? 'var(--success-color)' : 'var(--danger-color)' }}>
                    {row.percent_change_24h >= 0 ? '+' : ''}{row.percent_change_24h.toFixed(2)}%
                  </td>
                  <td>{row.market_segment}</td>
                  <td>{row.norm_liquidity.toFixed(4)}</td>
                  <td>{row.norm_volatility.toFixed(4)}</td>
                  <td>{row.risk_score.toFixed(3)}</td>
                  <td>
                    <span className={`badge-risk risk-${row.risk_category}`}>
                      {row.risk_category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
