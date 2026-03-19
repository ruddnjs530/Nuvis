/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#e1f0fc', // Light blue bg for active items
          DEFAULT: '#005AAB', // Samsung blue primary
          dark: '#004282',
        },
        background: '#f2f2f2', // Soft gray background (One UI style)
        surface: '#ffffff', // Card backgrounds
        text: {
          primary: '#111111',
          secondary: '#666666',
        }
      },
      borderRadius: {
        '4xl': '2rem', // Exaggerated rounded corners characteristic of One UI
      },
      fontFamily: {
        sans: ['"Pretendard"', '"Inter"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
