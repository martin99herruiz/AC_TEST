#!/usr/bin/env bash
set -Eeuo pipefail

# Sincroniza AC_TEST desde GitHub y publica solamente:
#   <PUBLIC_DIR>/test-ac.html
#   <PUBLIC_DIR>/../recap.html
#
# Uso:
#   bash scripts/sync-github-to-server.sh /var/www/html/ac
#
# Configuración opcional mediante variables de entorno:
#   REPO_URL, BRANCH, CHECKOUT_DIR

REPO_URL="${REPO_URL:-https://github.com/martin99herruiz/AC_TEST.git}"
BRANCH="${BRANCH:-main}"
PUBLIC_DIR="${1:-${PUBLIC_DIR:-}}"
CHECKOUT_DIR="${CHECKOUT_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/ac-test-sync/repo}"

TEST_SOURCE='test-ac-arquitectura-computadores.html'
RECAP_SOURCE='recap_ac_memoria_coherencia_comunicacion_amdahl.md'

usage() {
  cat <<'EOF'
Uso:
  bash scripts/sync-github-to-server.sh DIRECTORIO_PUBLICO

Ejemplo:
  bash scripts/sync-github-to-server.sh /var/www/html/ac

Resultado:
  /var/www/html/ac/test-ac.html
  /var/www/html/recap.html

Dependencias del servidor: git, pandoc, flock e install (coreutils).
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [[ -z "$PUBLIC_DIR" ]]; then
  usage >&2
  exit 2
fi

for command_name in git pandoc flock install mktemp realpath; do
  command -v "$command_name" >/dev/null 2>&1 ||
    die "falta '$command_name' en el servidor"
done

# Normaliza las rutas antes de crear temporales o publicar.
PUBLIC_DIR="$(realpath -m -- "$PUBLIC_DIR")"
RECAP_DIR="$(dirname -- "$PUBLIC_DIR")"
CHECKOUT_DIR="$(realpath -m -- "$CHECKOUT_DIR")"
[[ "$PUBLIC_DIR" != '/' ]] || die 'DIRECTORIO_PUBLICO no puede ser /'
[[ "$RECAP_DIR" != '/' ]] || die 'recap.html no puede publicarse directamente en /'

install -d -m 0755 -- "$(dirname -- "$CHECKOUT_DIR")"

LOCK_FILE="$(dirname -- "$CHECKOUT_DIR")/sync.lock"
exec 9>"$LOCK_FILE"
flock -n 9 || die 'ya hay otra sincronización en curso'

if [[ ! -d "$CHECKOUT_DIR/.git" ]]; then
  [[ ! -e "$CHECKOUT_DIR" ]] || die "$CHECKOUT_DIR existe pero no es un repositorio Git"
  git clone --branch "$BRANCH" --single-branch -- "$REPO_URL" "$CHECKOUT_DIR"
else
  current_remote="$(git -C "$CHECKOUT_DIR" remote get-url origin)"
  [[ "$current_remote" == "$REPO_URL" ]] ||
    die "el origin de $CHECKOUT_DIR es '$current_remote', no '$REPO_URL'"

  [[ -z "$(git -C "$CHECKOUT_DIR" status --porcelain)" ]] ||
    die "la copia de despliegue contiene cambios locales: $CHECKOUT_DIR"

  git -C "$CHECKOUT_DIR" checkout --quiet "$BRANCH"
  git -C "$CHECKOUT_DIR" pull --ff-only origin "$BRANCH"
fi

TEST_INPUT="$CHECKOUT_DIR/$TEST_SOURCE"
RECAP_INPUT="$CHECKOUT_DIR/$RECAP_SOURCE"
[[ -f "$TEST_INPUT" ]] || die "no existe $TEST_SOURCE en la rama $BRANCH"
[[ -f "$RECAP_INPUT" ]] || die "no existe $RECAP_SOURCE en la rama $BRANCH"

install -d -m 0755 -- "$PUBLIC_DIR" "$RECAP_DIR"

test_tmp="$(mktemp "$PUBLIC_DIR/.test-ac.html.XXXXXX")"
recap_tmp="$(mktemp "$RECAP_DIR/.recap.html.XXXXXX")"
header_tmp="$(mktemp "${TMPDIR:-/tmp}/ac-recap-header.XXXXXX.html")"

cleanup() {
  rm -f -- "${test_tmp:-}" "${recap_tmp:-}" "${header_tmp:-}"
}
trap cleanup EXIT

cat >"$header_tmp" <<'EOF'
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { color-scheme: light dark; }
  body {
    max-width: 1180px; margin: 0 auto; padding: 2rem;
    font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  h1, h2, h3 { line-height: 1.2; }
  table { display: block; width: 100%; overflow-x: auto; border-collapse: collapse; }
  th, td { padding: .55rem .7rem; border: 1px solid #8888; vertical-align: top; }
  th { background: #8882; }
  blockquote { margin-left: 0; padding-left: 1rem; border-left: 4px solid #8888; }
  code { padding: .1rem .25rem; background: #8882; border-radius: .2rem; }
  pre code { display: block; padding: 1rem; overflow-x: auto; }
  a { color: #1683d8; }
</style>
EOF

# Se generan primero archivos temporales en el mismo sistema de archivos y
# después se renombran: el servidor nunca sirve una copia a medio escribir.
install -m 0644 -- "$TEST_INPUT" "$test_tmp"
pandoc \
  --from=gfm \
  --to=html5 \
  --standalone \
  --toc \
  --toc-depth=3 \
  --mathjax='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js' \
  --metadata lang=es \
  --metadata 'title=Recap de Arquitectura de Computadores' \
  --include-in-header="$header_tmp" \
  --output="$recap_tmp" \
  "$RECAP_INPUT"
chmod 0644 -- "$recap_tmp"

mv -f -- "$test_tmp" "$PUBLIC_DIR/test-ac.html"
test_tmp=''
mv -f -- "$recap_tmp" "$RECAP_DIR/recap.html"
recap_tmp=''

commit="$(git -C "$CHECKOUT_DIR" rev-parse --short HEAD)"
printf 'Sincronización completada (%s, commit %s).\n' "$BRANCH" "$commit"
printf 'Test:  %s\n' "$PUBLIC_DIR/test-ac.html"
printf 'Recap: %s\n' "$RECAP_DIR/recap.html"
