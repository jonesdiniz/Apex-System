# Passo 1: Use a imagem oficial do FastAPI com Python 3.11
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia apenas o arquivo de dependências primeiro para otimizar o cache
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da sua aplicação para o diretório de trabalho
# (Isso assume que seu script Python está na mesma pasta do Dockerfile)
COPY ./ /app

# Instrução explícita para a imagem base sobre qual ficheiro e variável executar.
ENV APP_MODULE="api_gateway_v4_production_ready:app"

# A imagem base já lida com o comando de inicialização (CMD).
# O Uvicorn será iniciado automaticamente na porta 80,
# gerenciado pelo Gunicorn para performance e estabilidade.
# O Cloud Run irá mapear a porta 8080 para a porta 80 do contêiner.
