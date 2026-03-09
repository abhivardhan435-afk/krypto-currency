import React, { useEffect, useState } from 'react';
import ReactApexChart from 'react-apexcharts';
import axios from 'axios';

export default function CoinGrowthChart({ symbol }) {
    const [series, setSeries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        if (!symbol) return;

        let isMounted = true;
        setLoading(true);
        setError(false);

        const fetchHistory = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/api/history/${symbol}`);
                if (response.data.status === 'success' && isMounted) {
                    const dataPts = response.data.data.map(item => ({
                        x: new Date(item.timestamp).getTime(),
                        y: item.growth_pct.toFixed(4)
                    }));
                    setSeries([{ name: 'Growth %', data: dataPts }]);
                } else if (isMounted) {
                    setError(true);
                }
            } catch (err) {
                console.error(err);
                if (isMounted) setError(true);
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchHistory();
        // Re-fetch every 60s to stay real-time
        const interval = setInterval(fetchHistory, 60000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [symbol]);

    const options = {
        chart: {
            type: 'area',
            background: 'transparent',
            foreColor: '#d1d4dc',
            toolbar: { show: false },
            zoom: { enabled: false }
        },
        colors: ['#3b82f6'],
        dataLabels: { enabled: false },
        stroke: { curve: 'smooth', width: 2 },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.7,
                opacityTo: 0.1,
                stops: [0, 90, 100]
            }
        },
        xaxis: {
            type: 'datetime',
            labels: { style: { colors: '#94a3b8' } },
            tooltip: { enabled: false }
        },
        yaxis: {
            labels: {
                style: { colors: '#94a3b8' },
                formatter: (value) => { return value.toFixed(2) + "%" }
            }
        },
        grid: { borderColor: 'rgba(42, 46, 57, 0.5)' },
        theme: { mode: 'dark' },
        tooltip: {
            y: { formatter: (value) => { return value + "%" } }
        }
    };

    if (error) {
        return <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>Growth data unavailable for {symbol.toUpperCase()}</div>;
    }

    if (loading && series.length === 0) {
        return <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>Loading growth trajectory...</div>;
    }

    return (
        <div style={{ width: '100%', height: '300px' }}>
            <ReactApexChart options={options} series={series} type="area" height={300} />
        </div>
    );
}
