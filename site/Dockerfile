# Página de apresentação do NaView: arquivos estáticos servidos pelo nginx.
# Construir a partir da raiz do repositório: docker build -f site/Dockerfile .
# No Coolify: Build Pack = Dockerfile, Base Directory = /, Dockerfile Location = /site/Dockerfile.

# 1) Monta a página e o pacote de download (site/publico).
FROM python:3.13-alpine AS montar
WORKDIR /naview
COPY . .
RUN python3 ferramentas/gerar_site.py

# 2) Serve só o resultado.
FROM nginx:1.27-alpine
COPY site/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=montar /naview/site/publico/ /usr/share/nginx/html/
EXPOSE 80
