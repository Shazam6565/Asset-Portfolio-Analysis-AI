import React from 'react';
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react';

interface Asset {
    symbol: string;
    name: string;
    price: number;
    quantity: number;
    value: number;
    change: number;
}

interface PortfolioTableProps {
    data: Asset[];
    loading?: boolean;
}

const PortfolioTable = ({ data, loading }: PortfolioTableProps) => {
    if (loading) {
        return (
            <div className="p-12 flex flex-col items-center justify-center text-[var(--text-muted)]">
                <Loader2 className="w-8 h-8 text-[var(--accent-primary)] animate-spin mb-4" />
                <span className="text-sm font-medium">Loading assets...</span>
            </div>
        )
    }

    return (
        <div className="w-full">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/30">
                <h2 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wide">Holdings</h2>
                <span className="text-[var(--accent-primary)] text-xs font-mono px-2 py-1 bg-[var(--accent-primary)]/10 rounded">Live</span>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="text-[var(--text-muted)] text-xs uppercase tracking-wider border-b border-[var(--border-subtle)]">
                            <th className="py-4 pl-6 font-medium">Asset</th>
                            <th className="py-4 font-medium text-right">Price</th>
                            <th className="py-4 font-medium text-right">Qty</th>
                            <th className="py-4 font-medium text-right">Value</th>
                            <th className="py-4 font-medium text-right pr-6">24h</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-subtle)]">
                        {data.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="py-12 text-center text-[var(--text-muted)]">No assets found or not connected.</td>
                            </tr>
                        ) : data.map((asset) => (
                            <tr key={asset.symbol} className="group hover:bg-[var(--bg-tertiary)] transition-colors">
                                <td className="py-4 pl-6">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-center text-xs font-bold text-[var(--text-primary)]">
                                            {asset.symbol[0]}
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="font-bold text-[var(--text-primary)] tracking-wide">{asset.symbol}</span>
                                            <span className="text-xs text-[var(--text-muted)]">{asset.name}</span>
                                        </div>
                                    </div>
                                </td>
                                <td className="py-4 text-right font-mono text-[var(--text-secondary)]">${asset.price.toFixed(2)}</td>
                                <td className="py-4 text-right font-mono text-[var(--text-secondary)]">{asset.quantity}</td>
                                <td className="py-4 text-right font-mono text-[var(--text-primary)] font-medium">${asset.value.toFixed(2)}</td>
                                <td className="py-4 text-right pr-6">
                                    <div className={`flex items-center justify-end font-mono text-sm ${asset.change >= 0 ? 'text-[var(--accent-primary)]' : 'text-red-400'}`}>
                                        {asset.change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                                        {asset.change > 0 && '+'}{asset.change.toFixed(2)}%
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PortfolioTable;
