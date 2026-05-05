/**
 * Theme Store — Light/Dark Mode Toggle
 * Menyimpan preferensi theme di localStorage
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark';

interface ThemeStore {
    theme: Theme;
    toggleTheme: () => void;
    setTheme: (theme: Theme) => void;
}

export const useThemeStore = create<ThemeStore>()(
    persist(
        (set) => ({
            theme: 'dark', // Default dark mode sesuai design system

            toggleTheme: () =>
                set((state) => {
                    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
                    applyTheme(newTheme);
                    return { theme: newTheme };
                }),

            setTheme: (theme: Theme) => {
                applyTheme(theme);
                set({ theme });
            },
        }),
        {
            name: 'pramana-theme',
            onRehydrateStorage: () => (state) => {
                // Apply theme saat app load
                if (state) {
                    applyTheme(state.theme);
                }
            },
        }
    )
);

function applyTheme(theme: Theme) {
    const root = document.documentElement;
    if (theme === 'light') {
        root.setAttribute('data-theme', 'light');
    } else {
        root.removeAttribute('data-theme');
    }
}

// Initialize theme on module load
const initialTheme = useThemeStore.getState().theme;
applyTheme(initialTheme);
