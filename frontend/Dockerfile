FROM node:22-slim

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm install

# Copy source and build assets
COPY . .
RUN npm run build

# Cloud Run runtime configuration
ENV NODE_ENV=production
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

CMD ["npx", "tsx", "server/index.ts"]
