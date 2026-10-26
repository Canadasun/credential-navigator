/** The browser calls /api/*, which Next.js forwards to the FastAPI service. */
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8010";

export default {
  experimental: {
    // The proxy cuts request bodies at 10 MB by default, so a PDF just under the API's
    // 10 MB limit (plus form encoding) arrived truncated and failed with a 500.
    // Leave headroom so the API's own size check answers instead.
    middlewareClientMaxBodySize: "12mb",
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};
