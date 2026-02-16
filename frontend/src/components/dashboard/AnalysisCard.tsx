import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AnalysisResponse } from '@/lib/api';
import { ChevronDown, ChevronRight, AlertTriangle, TrendingUp, Target, Shield } from 'lucide-react';
import { formatAnalysisText } from '@/lib/utils';

interface AnalysisCardProps {
    data: AnalysisResponse;
}

export default function AnalysisCard({ data }: AnalysisCardProps) {
    const isBuy = data.recommendation === 'BUY';
    const isSell = data.recommendation === 'SELL';

    // Helper to determine color based on sentiment/action
    const getRecommendationColor = () => {
        if (isBuy) return 'text-[var(--text-green)] bg-[rgba(100,255,218,0.1)]';
        if (isSell) return 'text-red-400 bg-red-900/20';
        return 'text-yellow-400 bg-yellow-900/20';
    };

    return (
        <div className="bg-[var(--light-navy)] border border-[var(--lightest-navy)] rounded-lg p-6 my-4 shadow-xl">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-[var(--lightest-navy)] pb-4 mb-4">
                <div>
                    <h2 className="text-2xl font-bold text-[var(--text-lightest)] flex items-center gap-3">
                        {data.ticker}
                        {data.stock_info?.name && <span className="text-sm font-normal text-[var(--text-slate)]">({data.stock_info.name})</span>}
                    </h2>
                    <div className="flex items-center gap-4 mt-2">
                        {data.recommendation && (
                            <span className={`px-3 py-1 rounded text-sm font-bold ${getRecommendationColor()}`}>
                                {data.recommendation}
                            </span>
                        )}
                        {data.confidence && (
                            <span className="text-xs text-[var(--text-slate)] uppercase tracking-wider">
                                Confidence: <span className="text-[var(--text-lightest)]">{data.confidence}</span>
                            </span>
                        )}
                    </div>
                </div>
                {data.price_target && (
                    <div className="mt-4 md:mt-0 text-right">
                        <div className="text-xs text-[var(--text-green)] uppercase">12-Mo Price Target</div>
                        <div className="text-3xl font-bold text-[var(--text-lightest)]">{data.price_target}</div>
                    </div>
                )}
            </div>

            {/* Synthesis / Thesis */}
            <div className="mb-6">
                <h3 className="text-[var(--text-green)] font-mono text-sm mb-2">INVESTMENT THESIS</h3>
                <div className="text-[var(--text-slate)] leading-relaxed prose prose-sm prose-invert max-w-none
                    prose-p:text-[var(--text-slate)] prose-p:leading-relaxed prose-p:my-2
                    prose-strong:text-[var(--text-lightest)] prose-strong:font-semibold
                    prose-ul:my-2 prose-ul:pl-4 prose-li:my-1 prose-li:text-[var(--text-slate)]
                    prose-ol:my-2 prose-ol:pl-4
                    prose-headings:text-[var(--text-lightest)] prose-headings:font-bold prose-headings:mt-4 prose-headings:mb-2
                    prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
                    prose-code:text-[var(--green)] prose-code:bg-[var(--navy)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
                    prose-a:text-[var(--green)] prose-a:no-underline hover:prose-a:underline
                    prose-blockquote:border-l-[var(--green)] prose-blockquote:text-[var(--text-slate)] prose-blockquote:italic">
                    <ReactMarkdown>{data.synthesis}</ReactMarkdown>
                </div>
            </div>

            {/* Agent Details (Collapsible) */}
            <div className="space-y-2 mb-6">
                <CollapsibleSection title="Technical Analysis" content={data.technical_report} />
                <CollapsibleSection title="Fundamental Analysis" content={data.fundamental_report} />
                <CollapsibleSection title="Market Sentiment" content={data.sentiment_report} />
            </div>

            {/* Risks & Catalysts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {data.risks.length > 0 && (
                    <div className="bg-red-900/10 p-4 rounded border border-red-900/30">
                        <h4 className="text-red-400 font-bold mb-3 flex items-center gap-2">
                            <AlertTriangle size={16} /> Key Risks
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-[var(--text-slate)]">
                            {data.risks.map((risk, i) => (
                                <li key={i}>{risk}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {data.catalysts.length > 0 && (
                    <div className="bg-[rgba(100,255,218,0.05)] p-4 rounded border border-[var(--green)]/20">
                        <h4 className="text-[var(--text-green)] font-bold mb-3 flex items-center gap-2">
                            <TrendingUp size={16} /> Catalysts
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-[var(--text-slate)]">
                            {data.catalysts.map((cat, i) => (
                                <li key={i}>{cat}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            {/* Errors if any */}
            {data.errors && data.errors.length > 0 && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/50 rounded text-red-500 text-xs">
                    Analysis incomplete: {data.errors.join(", ")}
                </div>
            )}
        </div>
    );
}

function CollapsibleSection({ title, content }: { title: string, content?: string }) {
    const [isOpen, setIsOpen] = useState(false);

    if (!content) return null;

    return (
        <div className="border border-[var(--lightest-navy)] rounded overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between p-3 bg-[var(--light-navy)] hover:bg-[var(--lightest-navy)] transition-colors"
            >
                <span className="font-mono text-sm text-[var(--text-lightest)]">{title}</span>
                {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {isOpen && (
                <div className="p-4 bg-[var(--navy)] text-sm text-[var(--text-slate)] border-t border-[var(--lightest-navy)]">
                    <div className="analysis-markdown">
                        <ReactMarkdown components={{
                            // Custom renderer for paragraphs to handle badges if we used a custom parser, 
                            // but we are using standard specific class styling in CSS.
                            // We can also override specific elements if needed, but CSS is cleaner.
                        }}>
                            {formatAnalysisText(content)}
                        </ReactMarkdown>
                    </div>
                </div>
            )}
        </div>
    );
}
