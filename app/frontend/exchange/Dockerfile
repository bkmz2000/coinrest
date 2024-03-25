FROM node:lts-alpine

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

RUN npm install -g @vue/cli

COPY package.json .
COPY package-lock.json .
COPY vite.config.js .
RUN npm install
COPY . .

EXPOSE 8070

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8070"]
