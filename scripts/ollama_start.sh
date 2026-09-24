#!/usr/bin/env bash
# ============================================================
# Corvus Corax - Ollama kalici baslatma (Linux/macOS/WSL)
# 11434 kapaliysa serve'i arka planda baslatir.
#  chmod +x scripts/ollama_start.sh && ./scripts/ollama_start.sh
# ============================================================
set -e
if ! command -v ollama >/dev/null 2>&1; then
    echo "[HATA] ollama PATH'te yok. Kur: https://ollama.com/download" >&2
    exit 1
fi

if (exec 3<>/dev/tcp/127.0.0.1/11434) 2>/dev/null; then
    exec 3<&- 3>&-
    echo "[OK] Ollama zaten calisiyor (port 11434)."
    exit 0
fi

echo "[..] ollama serve arka planda baslatiliyor -> $TMPDIR/ollama_serve.log"
nohup ollama serve >"${TMPDIR:-/tmp}/ollama_serve.log" 2>&1 &

for _ in $(seq 1 10); do
    sleep 2
    if (exec 3<>/dev/tcp/127.0.0.1/11434) 2>/dev/null; then
        exec 3<&- 3>&-
        echo "[OK] Ollama ayakta: http://127.0.0.1:11434"
        exit 0
    fi
done
echo "[UYARI] 20sn icinde port acilmadi. Log'a bakin." >&2
exit 2