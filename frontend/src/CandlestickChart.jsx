import React, { useEffect, useState } from 'react';
import ReactApexChart from 'react-apexcharts';

export default function CandlestickChart({ symbol }) {
    const [error, setError] = useState(false);
    const [series, setSeries] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!symbol) return;
        setError(false);
        setLoading(true);

        const fetchKlines = async () => {
            try {
                const binanceSymbol = `${symbol.toUpperCase()}USDT`;
                const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${binanceSymbol}&interval=1h&limit=168`);

                if (!res.ok) {
                    throw new Error("Cannot fetch klines for symbol");
                }

                const data = await res.json();
                const formattedData = data.map(d => ({
                    x: new Date(parseInt(d[0])),
                    y: [
                        parseFloat(d[1]), // open
                        parseFloat(d[2]), // high
                        parseFloat(d[3]), // low
                        parseFloat(d[4])  // close
                    ]
                }));

                setSeries([{ name: 'candle', data: formattedData }]);
            } catch (err) {
                console.error(err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };

        fetchKlines();
    }, [symbol]);

    const options = {
        chart: {
            type: 'candlestick',
            background: 'transparent',
            foreColor: '#d1d4dc',
            toolbar: { show: false }
        },
        xaxis: {
            type: 'datetime',
            labels: { style: { colors: '#94a3b8' } }
        },
        yaxis: {
            tooltip: { enabled: true },
            labels: { style: { colors: '#94a3b8' } }
        },
        grid: {
            borderColor: 'rgba(42, 46, 57, 0.5)'
        },
        plotOptions: {
            candlestick: {
                colors: { upward: '#10b981', downward: '#ef4444' }
            }
        },
        theme: { mode: 'dark' }
    };

    if (error) {
        return <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>Candlestick data unavailable directly for {symbol.toUpperCase()}/USDT</div>;
    }

    if (loading) {
        return <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>Loading chart data...</div>;
    }

    return (
        <div style={{ width: '100%', height: '300px' }}>
            <ReactApexChart options={options} series={series} type="candlestick" height={300} />
        </div>
    );
}
