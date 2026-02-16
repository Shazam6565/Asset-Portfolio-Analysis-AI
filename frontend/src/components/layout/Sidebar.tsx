import Link from 'next/link';
import { Home, TrendingUp, Settings, MessageSquare, Moon, Sun, Monitor } from 'lucide-react';

interface SidebarProps {
    toggleTheme?: () => void;
    currentTheme?: string;
}

const Sidebar = ({ toggleTheme, currentTheme = 'default' }: SidebarProps) => {
    const links = [
        { name: 'Dashboard', href: '/', icon: Home },
        { name: 'Analysis', href: '/analysis', icon: MessageSquare }, // Placeholder route
        { name: 'Trade', href: '/trade', icon: TrendingUp }, // Placeholder route
        { name: 'Settings', href: '/settings', icon: Settings }, // Placeholder route
    ];

    const getThemeIcon = () => {
        switch (currentTheme) {
            case 'dark': return <Moon className="w-4 h-4" />;
            case 'light': return <Sun className="w-4 h-4" />;
            default: return <Monitor className="w-4 h-4" />;
        }
    };

    return (
        <div className="h-full flex flex-col items-center py-6">
            <div className="mb-8">
                <div className="w-10 h-10 bg-[var(--accent-primary)] rounded-xl flex items-center justify-center text-[var(--bg-primary)] font-bold text-xl">
                    R
                </div>
            </div>

            <nav className="flex-1 space-y-4 w-full px-2">
                {links.map((link) => {
                    const Icon = link.icon;
                    return (
                        <Link
                            key={link.name}
                            href={link.href}
                            title={link.name}
                            className="flex items-center justify-center p-3 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] rounded-xl transition-all duration-200 group relative"
                        >
                            <Icon className="w-5 h-5" />
                        </Link>
                    );
                })}
            </nav>

            <div className="space-y-4 w-full px-2">
                {toggleTheme && (
                    <button
                        onClick={toggleTheme}
                        className="w-full flex items-center justify-center p-3 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] rounded-xl transition-all duration-200"
                        title={`Theme: ${currentTheme}`}
                    >
                        {getThemeIcon()}
                    </button>
                )}

                <div className="flex items-center justify-center p-3">
                    <div className="w-8 h-8 rounded-full bg-[var(--accent-primary)]/10 flex items-center justify-center text-[var(--accent-primary)] font-bold text-xs ring-2 ring-[var(--bg-primary)]">
                        US
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
