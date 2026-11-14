FROM node:22.22.0-bookworm-slim
WORKDIR /app
COPY --chown=node:node package.json server.mjs ./
RUN mkdir /app/data && chown node:node /app/data
USER node
ENV HOST=0.0.0.0 PORT=8787 SESSION_DB_PATH=/app/data/sessions.sqlite
EXPOSE 8787
VOLUME /app/data
HEALTHCHECK --interval=30s --timeout=3s CMD node -e "fetch('http://127.0.0.1:8787/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "server.mjs"]
