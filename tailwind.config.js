/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ['./app/templates/*.html', './app/static/**/*.js'],
    theme: {
        extend: {
            colors: {
                'stone-950': '#18191E',
                'neutral-950': '#232429',

                'blue-600': '#3D1EBB',
                'blue-700': '#281494',
                'blue-950': '#252634',

                'slate-900': '#161617',
                'slate-700 ': '#222225',
                'slate-800': '#19191b',

                'zinc-950': '#1A1926',
                'zinc-700': '#34324F',
                'gray-900': '#282a2f',

                'gray-50': '#F4F4F4',
                'gray-600': '#5C6773',

                'indigo-100': '#AFB4FF',
                'indigo-50': '#C1D4FF',
            },
            fontFamily: {
                'noto-sans': ['Noto Sans', 'sans-serif'],
            },
        },
    },
    plugins: [],
    safelist: ['-z-10'],
};
