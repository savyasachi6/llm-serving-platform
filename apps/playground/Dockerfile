# --- Stage 1: Builder ---
# This is a multi-stage Docker build. We use a Node.js image to build our frontend assets,
# but we won't include Node.js in the final image, making it much smaller and more secure.
# 'node:20-alpine' uses the lightweight Alpine Linux distribution and Node version 20.
FROM node:20-alpine AS builder

# Set the working directory for the build stage to /app.
WORKDIR /app

# Copy package.json and package-lock.json first.
# By copying these before the source code, we take advantage of Docker layer caching.
# If dependencies haven't changed, 'npm install' will use the cached layer.
COPY package*.json ./

# Run npm install to download all project dependencies specified in package.json.
RUN npm install

# Copy all the application source code into the container.
COPY . .

# Run the build script (usually defined in package.json as something like 'tsc && vite build').
# This transpiles TypeScript, bundles React code, and outputs static HTML/CSS/JS files into a 'dist' directory.
RUN npm run build

# --- Stage 2: Production Server ---
# Now we start a new, completely fresh stage using Nginx, a high-performance web server.
# This final image will ONLY contain Nginx and the static files we just built.
FROM nginx:alpine

# Copy the compiled static assets from the 'builder' stage into Nginx's default public directory.
# The '--from=builder' flag tells Docker to grab files from the previous stage.
COPY --from=builder /app/dist /usr/share/nginx/html

# EXPOSE informs Docker that the container will listen on port 80 at runtime.
# Port 80 is the standard HTTP port, which Nginx serves on by default.
EXPOSE 80

# Define the command to start the Nginx server.
# '-g daemon off;' forces Nginx to run in the foreground. If it runs in the background (daemon mode),
# the Docker container will immediately exit because it thinks the primary process has finished.
CMD ["nginx", "-g", "daemon off;"]
