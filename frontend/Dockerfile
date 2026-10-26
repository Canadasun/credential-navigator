# Applicant portal. API_URL is where Next.js forwards /api/* (fixed at build time).
FROM node:22-slim AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG API_URL=http://api:8000
ENV API_URL=$API_URL
RUN npm run build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY --from=build /app/.next ./.next
COPY --from=build /app/next.config.mjs ./
USER node
EXPOSE 3010
CMD ["npx", "next", "start", "-p", "3010"]
