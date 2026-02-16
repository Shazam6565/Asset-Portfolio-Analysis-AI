'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { X, Lock } from 'lucide-react';

interface LoginModalProps {
    onCheckLogin: () => void;
    onClose: () => void;
}

const LoginModal = ({ onCheckLogin, onClose }: LoginModalProps) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [mfaCode, setMfaCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showMfa, setShowMfa] = useState(false); // Typically we'd detect this from backend, but simpler to ask upfront or check error

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await api.login({ username, password, mfa_code: mfaCode || null });
            onCheckLogin();
            onClose();
        } catch (err: any) {
            setError(err.message);
            // Heuristic: if error contains 'MFA' or similar, show MFA input
            if (err.message.includes('MFA') || err.message.includes('challenge')) {
                setShowMfa(true);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-navy-shadow backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-light-navy border border-lightest-navy rounded-lg p-8 w-full max-w-md relative shadow-2xl">
                <button onClick={onClose} className="absolute top-4 right-4 text-slate hover:text-green">
                    <X className="w-5 h-5" />
                </button>

                <div className="flex flex-col items-center mb-6">
                    <div className="w-12 h-12 bg-green/10 rounded-full flex items-center justify-center mb-3 text-green">
                        <Lock className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold text-lightest-slate">Connect Robinhood</h2>
                    <p className="text-slate text-sm mt-1">Secure connection via local backend</p>
                </div>

                {error && (
                    <div className="bg-pink/10 border border-pink text-pink p-3 rounded mb-4 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate mb-1">Username / Email</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-navy border border-lightest-navy rounded px-3 py-2 text-white focus:border-green focus:outline-none"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate mb-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-navy border border-lightest-navy rounded px-3 py-2 text-white focus:border-green focus:outline-none"
                            required
                        />
                    </div>

                    {showMfa && (
                        <div>
                            <label className="block text-sm font-medium text-green mb-1">MFA Code (SMS/App)</label>
                            <input
                                type="text"
                                value={mfaCode}
                                onChange={(e) => setMfaCode(e.target.value)}
                                className="w-full bg-navy border border-green rounded px-3 py-2 text-white focus:outline-none"
                                placeholder="123456"
                            />
                        </div>
                    )}

                    <div className="flex items-center justify-between text-xs text-slate mt-2">
                        <label className="flex items-center">
                            <input type="checkbox" className="mr-2" /> Remember session
                        </label>
                        <button type="button" className="hover:text-green" onClick={() => setShowMfa(!showMfa)}>
                            {showMfa ? 'Hide MFA' : 'Enter MFA Code?'}
                        </button>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-green text-navy font-bold py-3 rounded hover:bg-green/90 transition-colors disabled:opacity-50 mt-6"
                    >
                        {loading ? 'Connecting...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default LoginModal;
