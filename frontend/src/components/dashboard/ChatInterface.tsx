'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, Loader2, Database, BarChart3, Building2, Newspaper, Brain, CheckCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api, AnalysisResponse, HoldingsResponse } from '@/lib/api';
import AnalysisCard from './AnalysisCard';

interface Message {
    id: number;
    role: 'user' | 'assistant';
    content?: string;
    analysis?: AnalysisResponse | HoldingsResponse;
}

// Loading steps for multi-agent orchestration
const LOADING_STEPS = [
    { id: 1, label: 'Gathering market data...', icon: Database, duration: 1500 },
    { id: 2, label: 'Running technical analysis...', icon: BarChart3, duration: 2000 },
    { id: 3, label: 'Analyzing fundamentals...', icon: Building2, duration: 2000 },
    { id: 4, label: 'Processing news & sentiment...', icon: Newspaper, duration: 1500 },
    { id: 5, label: 'Synthesizing recommendation...', icon: Brain, duration: 2000 },
];

const ChatInterface = () => {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 1,
            role: 'assistant',
            content: "Hello! I'm your V2 AI Investment Analyst. I can analyze stocks with technical, fundamental, and sentiment data. Try asking 'Analyze AAPL' or 'What's going on with my portfolio?'"
        }
    ]);
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);
    const [isAnalysisMode, setIsAnalysisMode] = useState(true);
    const [portfolio, setPortfolio] = useState<any[]>([]);

    // Auto-scroll ref
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading, loadingStep]); // Scroll on step updates too

    // Fetch portfolio on mount
    useEffect(() => {
        const fetchPortfolio = async () => {
            try {
                const response = await api.getPortfolio();
                if (response.data && Array.isArray(response.data)) {
                    setPortfolio(response.data);
                    console.log('Portfolio loaded for AI context:', response.data.length, 'holdings');
                }
            } catch (err) {
                console.log('Portfolio not available (user may not be logged in)');
            }
        };
        fetchPortfolio();
    }, []);

    const classifyQuery = (query: string, portfolio: any[]): 'holdings' | 'analysis' | 'general' => {
        const upperQuery = query.toUpperCase();

        // HOLDINGS patterns
        if (/(position|holding|shares|avg cost|average cost|own|price of|my pl|my p&l)/i.test(query)) {
            // Check if any portfolio ticker is mentioned
            if (portfolio.some(h => upperQuery.includes(h.symbol))) {
                return 'holdings';
            }
        }

        // ANALYSIS patterns  
        if (/(analyze|should i|buy|sell|bullish|bearish|outlook|recommendation|target|forecast)/i.test(query)) {
            return 'analysis';
        }

        // Default to general
        return 'general';
    };

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userText = input;
        const queryType = classifyQuery(userText, portfolio);

        const newUserMsg: Message = { id: Date.now(), role: 'user', content: userText };

        setMessages(prev => [...prev, newUserMsg]);
        setInput('');
        setLoading(true);
        setLoadingStep(0);
        setIsAnalysisMode(queryType === 'analysis');

        // Placeholder for AI response
        const aiMsgId = Date.now() + 1;
        const initialAiMsg: Message = {
            id: aiMsgId,
            role: 'assistant',
            content: '',
        };
        setMessages(prev => [...prev, initialAiMsg]);

        // Simulated progress timer - ONLY for analysis mode
        let progressInterval: NodeJS.Timeout | null = null;
        if (queryType === 'analysis') {
            progressInterval = setInterval(() => {
                setLoadingStep(prev => {
                    if (prev < 4) return prev + 1;
                    return prev;
                });
            }, 1500);
        }

        try {
            const history = messages.map(m => ({
                role: m.role as string,
                content: m.content || (m.analysis ? `Analysis for ${m.analysis.ticker}` : '')
            }));

            // Standard Await API
            const result = await api.analyze({
                query: userText,
                portfolio_context: portfolio,
                conversation_history: history
            });

            if (progressInterval) clearInterval(progressInterval);
            setLoadingStep(5); // Complete

            setMessages(prev => prev.map(msg => {
                if (msg.id === aiMsgId) {
                    // Check response type
                    if (result.response_type === 'holdings_lookup') {
                        // Format specific holdings response
                        const h = result as any;
                        const content = `**${h.company_name} (${h.ticker}) Position:**
- Shares: ${h.shares_held}
- Market Value: $${h.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
- Unrealized P&L: $${h.unrealized_pl_dollars.toLocaleString(undefined, { minimumFractionDigits: 2 })} (${h.unrealized_pl_percent.toFixed(2)}%)`;

                        return {
                            ...msg,
                            content: content,
                            analysis: undefined // No analysis card for simple holdings
                        };
                    } else {
                        // Regular analysis/general response
                        return {
                            ...msg,
                            content: (result as any).synthesis,
                            analysis: (result as any).ticker ? (result as any) : undefined
                        };
                    }
                }
                return msg;
            }));

        } catch (err: any) {
            console.error(err);
            if (progressInterval) clearInterval(progressInterval);
            setMessages(prev => prev.map(msg => {
                if (msg.id === aiMsgId) {
                    return {
                        ...msg,
                        content: `Error: ${err.message || "An unexpected error occurred."}`
                    };
                }
                return msg;
            }));
        } finally {
            setLoading(false);
            if (progressInterval) clearInterval(progressInterval);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[var(--bg-secondary)] relative">
            {/* Header */}
            <div className="flex-none p-6 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-secondary)]">
                <div className="flex items-center space-x-4">
                    <div className="bg-[var(--accent-primary)]/10 p-2.5 rounded-xl border border-[var(--accent-primary)]/20 shadow-sm">
                        <Bot className="w-6 h-6 text-[var(--accent-primary)]" />
                    </div>
                    <div>
                        <h3 className="font-bold text-[var(--text-primary)] tracking-wide">Sentinel AI <span className="text-[var(--text-muted)] font-normal text-xs ml-2">V2.0</span></h3>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent-primary)] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--accent-primary)]"></span>
                            </span>
                            <span className="text-xs text-[var(--text-secondary)] font-medium">Systems Online</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-thin scrollbar-thumb-[var(--border-strong)] scrollbar-track-transparent">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] ${msg.role === 'user' ? '' : 'w-full'}`}>
                            {/* User Message */}
                            {msg.role === 'user' && (
                                <div className="bg-[var(--accent-primary)] text-[var(--bg-primary)] rounded-2xl rounded-tr-sm px-6 py-4 shadow-sm">
                                    <p className="text-sm font-medium leading-relaxed">{msg.content}</p>
                                </div>
                            )}

                            {/* AI Message */}
                            {msg.role === 'assistant' && (
                                <div className="space-y-6">
                                    {/* Text Content with Markdown */}
                                    {(!msg.analysis) && (
                                        <div className="text-[var(--text-secondary)] pl-2 border-l-2 border-[var(--border-subtle)]">
                                            <div className="prose prose-sm max-w-none
                                                text-[var(--text-secondary)]
                                                prose-p:leading-relaxed prose-p:my-2
                                                prose-strong:text-[var(--text-primary)] prose-strong:font-semibold
                                                prose-ul:my-2 prose-li:my-0.5
                                                prose-headings:text-[var(--text-primary)] prose-headings:font-bold prose-headings:mt-4 prose-headings:mb-2
                                                prose-a:text-[var(--accent-primary)] prose-a:no-underline hover:prose-a:underline">
                                                <ReactMarkdown>{msg.content || ''}</ReactMarkdown>
                                            </div>
                                        </div>
                                    )}

                                    {/* Structured Analysis Card */}
                                    {msg.analysis && msg.analysis.response_type !== 'holdings_lookup' && (
                                        <AnalysisCard data={msg.analysis as AnalysisResponse} />
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {/* Loading Indicator - Step by Step Progress */}
                {loading && isAnalysisMode && (
                    <div className="flex justify-start">
                        <div className="bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] rounded-xl p-5 w-full max-w-md shadow-sm">
                            <div className="flex items-center gap-3 mb-4 border-b border-[var(--border-subtle)] pb-3">
                                <Brain className="w-5 h-5 text-[var(--accent-primary)] animate-pulse" />
                                <span className="text-sm font-bold text-[var(--text-primary)]">Analyzing...</span>
                            </div>
                            <div className="space-y-3">
                                {LOADING_STEPS.map((step, index) => {
                                    const Icon = step.icon;
                                    const isActive = index === loadingStep;
                                    const isComplete = index < loadingStep;
                                    return (
                                        <div
                                            key={step.id}
                                            className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-500 ${isActive
                                                ? 'bg-[var(--bg-primary)] border border-[var(--border-subtle)] translate-x-1'
                                                : isComplete
                                                    ? 'opacity-40'
                                                    : 'opacity-20 blur-[0.5px]'
                                                }`}
                                        >
                                            {isComplete ? (
                                                <CheckCircle className="w-4 h-4 text-[var(--accent-primary)]" />
                                            ) : isActive ? (
                                                <Loader2 className="w-4 h-4 text-[var(--accent-primary)] animate-spin" />
                                            ) : (
                                                <Icon className="w-4 h-4 text-[var(--text-muted)]" />
                                            )}
                                            <span className={`text-xs font-medium ${isActive ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}`}>
                                                {step.label}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="flex-none p-6 pt-2 bg-[var(--bg-secondary)]">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Ask Sentinel AI..."
                        className="w-full bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-subtle)] rounded-full pl-6 pr-14 py-4 focus:outline-none focus:ring-1 focus:ring-[var(--accent-primary)] focus:border-[var(--accent-primary)] placeholder-[var(--text-muted)]/60 text-sm shadow-sm transition-all duration-200"
                        disabled={loading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="absolute right-2 p-2.5 bg-[var(--accent-primary)] text-[var(--bg-primary)] rounded-full hover:opacity-90 transition-all disabled:opacity-0 disabled:scale-75 shadow-md transform scale-100"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
                <div className="mt-3 text-center">
                    <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider opacity-60">
                        AI Model: V2.0 • Market Data: Real-time
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
