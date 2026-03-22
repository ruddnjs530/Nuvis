# Build stage
FROM node:18-alpine AS builder

WORKDIR /usr/src/app

COPY package*.json ./
COPY prisma ./prisma/

# Install application dependencies, ensuring Prisma CLI and client are included
RUN npm ci

# Generate Prisma Client
RUN npx prisma generate

COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /usr/src/app

COPY package*.json ./
COPY prisma ./prisma/
COPY proto ./proto/

# Install only production dependencies
RUN npm ci --only=production

# Install Prisma for production use and generate the Client
RUN npm install @prisma/client
RUN npx prisma generate

COPY --from=builder /usr/src/app/dist ./dist

# Start the application
CMD [ "npm", "run", "start:prod" ]
