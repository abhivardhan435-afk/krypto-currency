import React from 'react';

export default function CorrelationMatrix({ matrix }) {
    if (!matrix) return null;
    const symbols = Object.keys(matrix).sort();

    if (symbols.length === 0) return <div style={{ color: 'var(--text-secondary)' }}>Waiting for correlation data...</div>;

    const getColor = (value) => {
        if (value === 1) return 'rgba(59, 130, 246, 0.8)'; // accent
        if (value > 0) return `rgba(16, 185, 129, ${value})`; // green for positive
        if (value === 0) return 'rgba(45, 55, 72, 0.5)';
        return `rgba(239, 68, 68, ${Math.abs(value)})`; // red for negative
    }

    return (
        <div style={{ overflowX: 'auto', fontSize: '0.75rem', width: '100%' }}>
            <table style={{ minWidth: 'max-content', width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        <th style={{ borderBottom: 'none' }}></th>
                        {symbols.map(s => <th key={s} style={{ textAlign: 'center', padding: '0.25rem', borderBottom: 'none' }}>{s}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {symbols.map(s1 => (
                        <tr key={s1} style={{ background: 'transparent' }}>
                            <td style={{ fontWeight: 'bold', borderBottom: 'none', padding: '0.25rem', textAlign: 'right', paddingRight: '0.5rem' }}>{s1}</td>
                            {symbols.map(s2 => {
                                const val = matrix[s1][s2] || 0;
                                return (
                                    <td key={s2} style={{
                                        backgroundColor: getColor(val),
                                        color: val === 0 ? 'var(--text-secondary)' : '#fff',
                                        textAlign: 'center',
                                        width: '28px',
                                        height: '28px',
                                        padding: '0.1rem',
                                        border: '1px solid var(--bg-tertiary)',
                                        fontSize: '0.65rem'
                                    }}>
                                        {val.toFixed(2)}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
