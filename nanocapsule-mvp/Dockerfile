# Imagen de VLP Studio. Reescrita en VLP-01 (2026-09-17).
# Cambios vs la versión fósil: base py3.12 (no 3.9; rdkit 2025.9 y el entorno real
# corren en 3.12), instala los motores que usa el Studio (obabel, vina), healthcheck
# por urllib (antes usaba `requests`/`curl`, ninguno instalado) contra /api/health
# (endpoint que antes no existía → contenedor siempre unhealthy).
#
# LÍMITES CONOCIDOS (honestos, no resueltos aquí):
#  - `hole` e `idock` NO están en apt (Oxford / manual). Esta imagen NO los trae:
#    la puerta PAC-PORE (perfil de poro, cribado) no funcionará hasta proveerlos
#    (montarlos o añadirlos en una capa propia). /api/health los reporta ausentes.
#  - El build context es solo nanocapsule-mvp/; los modelos de Poromania (carpeta
#    hermana) quedan fuera. Montar por volumen si se quiere Pac-Pore en contenedor.

FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Imagen final ---
FROM python:3.12-slim

# Motores del sistema (apt) + libs de runtime para PyMOL/RDKit headless.
RUN apt-get update && apt-get install -y --no-install-recommends \
    packmol \
    pymol \
    openbabel \
    autodock-vina \
    libgl1-mesa-glx \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . .
RUN mkdir -p Input/Capsides Input/Enzimas Output

ENV FLASK_APP=src/web/app.py
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=0

EXPOSE 5000

# Healthcheck con la stdlib (urllib): 0 si /api/health responde 200.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/api/health').status==200 else 1)" || exit 1

CMD ["python", "src/web/app.py"]
