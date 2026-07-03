# Stage 1: Build compilation
FROM node:20-alpine AS build

# Set container working directory
WORKDIR /workspace

# Copy manifest package dependencies
COPY package*.json ./

# Install npm packages
RUN npm install

# Copy frontend source files
COPY . .

# Compile production bundle
RUN npm run build

# Stage 2: Serve static static pages
FROM nginx:alpine

# Copy compiled bundles to web root directory
COPY --from=build /workspace/dist /usr/share/nginx/html

# Copy custom Nginx configuration mapping
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for traffic monitor cockpit
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
