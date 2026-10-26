/** The browser calls /api/*, which Next.js forwards to the FastAPI service. */
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8010";

export default {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};
