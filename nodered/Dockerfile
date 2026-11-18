FROM docker.io/nodered/node-red:4.0
COPY package.json /data/package.json
RUN npm install --prefix /data
COPY flows.json /data/flows.json
