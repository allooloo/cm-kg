# CM-KG regional node door (ORDER-018). One image, region and node as environment variables. Built in the cloud with `az acr build`.
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund
COPY index.js ./
COPY static ./static
ENV PORT=8080 NODE_ENV=production
EXPOSE 8080
USER node
CMD ["node", "index.js"]
