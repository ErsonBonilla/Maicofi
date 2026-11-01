import { type Config } from "tailwindcss";

export default {
  content: [
    "{routes,islands,components}/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cereza: "#54121B",
        cafetal: "#2C4234",
        pergamino: "#FAF6F0",
        carbon: "#232323",
      },
    },
  },
} satisfies Config;
