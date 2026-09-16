FROM node:20-slim
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# NEXT_PUBLIC_* vars are inlined into the JS bundle at build time, not
# read at container runtime - so this must be a build ARG, not just an
# env_file entry in docker-compose (that only affects the running
# container, which is too late for Next.js's build step).
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
