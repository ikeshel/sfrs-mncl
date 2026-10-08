#!/usr/bin/env bash
# Install desktop prerequisites and Python packages in the project's .venv.
# Author: i.keshelashvili@gsi.de
set -euo pipefail

usage() {
    echo "Usage: $0 [--dry-run | --help]"
    echo "Run as your normal user; only APT commands use sudo."
}

dry_run=false
if (( $# > 1 )); then
    usage >&2
    exit 2
fi
case "${1:-}" in
    --dry-run) dry_run=true ;;
    --help|-h) usage; exit 0 ;;
    '') ;;
    *) usage >&2; exit 2 ;;
esac

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$project_dir/.venv"

if ! command -v apt-get >/dev/null; then
    echo "This installer requires a Debian/Ubuntu system with apt-get." >&2
    exit 1
fi
if ! "$dry_run" && (( EUID == 0 )); then
    echo "Run without sudo so the Python environment belongs to your user." >&2
    exit 1
fi
if ! "$dry_run" && ! command -v sudo >/dev/null; then
    echo "sudo is required to install system packages." >&2
    exit 1
fi

# Strip comments and surrounding whitespace; accept plain APT package names.
packages=()
while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue
    if [[ ! "$line" =~ ^[a-z0-9][a-z0-9.+-]+$ ]]; then
        echo "Invalid APT package name: $line" >&2
        exit 1
    fi
    packages+=("$line")
done < "$project_dir/apt_dependencies.txt"
if (( ${#packages[@]} == 0 )); then
    echo "apt_dependencies.txt contains no packages." >&2
    exit 1
fi
[[ -r "$project_dir/python_dependencies.txt" ]] || {
    echo "Cannot read python_dependencies.txt." >&2
    exit 1
}

run() {
    printf '+ '
    printf '%q ' "$@"
    printf '\n'
    if ! "$dry_run"; then
        "$@"
    fi
}

run sudo apt-get update
run sudo apt-get install "${packages[@]}"
run python3 -m venv "$venv_dir"
run "$venv_dir/bin/python" -m pip install -r "$project_dir/python_dependencies.txt"
run "$venv_dir/bin/python" -m pip check

if "$dry_run"; then
    echo "Dry run complete; no packages installed or files changed."
else
    printf '\nSetup complete. Activate the environment with:\nsource %q\n' "$venv_dir/bin/activate"
fi
