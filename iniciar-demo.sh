#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"

if [ "${FITBATTLE_REDE:-0}" = "1" ]; then
  ENDERECO=0.0.0.0
else
  ENDERECO=127.0.0.1
fi

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
. .venv/bin/activate
python -m pip install -q -r backend/requirements.txt

HOST="$ENDERECO" PORT=5000 ADMIN_EMAILS=helena@fitbattle.dev python backend/tests/servidor_dev.py &
API_PID=$!
python -m http.server 5500 --bind "$ENDERECO" --directory frontend &
FRONT_PID=$!
trap 'kill $API_PID $FRONT_PID 2>/dev/null' EXIT INT TERM

echo
echo "FitBattle demo no ar."
echo "  Tela de login (este computador): http://localhost:5500/login.html"
echo "  API: http://localhost:5000/healthz"
echo "  Login de demonstracao: helena@fitbattle.dev / senhaforte123"
if [ "$ENDERECO" = "0.0.0.0" ]; then
  echo "  Modo rede ativo (FITBATTLE_REDE=1): outro aparelho da mesma rede pode abrir"
  echo "    http://IP_DESTE_COMPUTADOR:5500/login.html"
  echo "  Use so em rede de confianca: a conta de demonstracao tem senha publica."
else
  echo "  Para abrir de outro aparelho da rede, rode com FITBATTLE_REDE=1 (use so em rede de confianca)."
fi
echo "  Para encerrar: Ctrl+C"
echo

wait
