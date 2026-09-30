# Use an official Node.js runtime as a parent image
FROM node:22.14-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install app dependencies
RUN npm install \
    # Some build environments (e.g. ACR Tasks) don't preserve the executable
    # bit on node_modules/.bin scripts such as run-p; restore it explicitly so
    # `npm run build` can invoke them.
    && chmod -R a+x node_modules/.bin

# Copy the rest of the app source code to the container
COPY . .

# Build the app
RUN npm run build 

# Run the app on nginx
FROM nginx:stable-alpine-slim AS runner

# Copy the build output to replace the default nginx contents
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose the port the app listens on
EXPOSE 8080

# Set the build argument for the app version number
ARG APP_VERSION=0.1.0

# Set the environment variable for the app version number
ENV APP_VERSION=$APP_VERSION

# Copy the nginx configuration template to the container
COPY nginx.conf /etc/nginx/conf.d/nginx.conf.template

# Update the nginx configuration to use the app version number
# and Copy the nginx configuration template to the container
RUN envsubst '${APP_VERSION}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Static body returned by the credential check endpoint used by the login page
RUN printf '{"status":"ok"}' > /usr/share/nginx/html/auth-check.json

# Generate the HTTP Basic authentication config from environment variables at
# container start (scripts in /docker-entrypoint.d are run by the nginx image)
COPY docker-entrypoint.d/20-basic-auth.sh /docker-entrypoint.d/20-basic-auth.sh
RUN chmod +x /docker-entrypoint.d/20-basic-auth.sh

# Start the app
CMD ["nginx", "-g", "daemon off;"]