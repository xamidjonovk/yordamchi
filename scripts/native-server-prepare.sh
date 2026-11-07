#!/usr/bin/env bash
# Run as the dedicated, unprivileged project account, after an approved admin bootstrap.
# It prepares software only; it never logs into Telegram or starts the agent.
set -euo pipefail
[[ "$(id -u)" -ne 0 ]] || { echo 'Use the dedicated non-root project account.' >&2; exit 1; }
project_root="${HPA_PROJECT_HOME:-$HOME/hermes-personal}"
[[ "$project_root" = /* && "$project_root" =~ ^/[a-zA-Z0-9_./-]+$ && "$project_root" != *..* ]] || {
  echo 'HPA_PROJECT_HOME must be an absolute path without spaces or shell metacharacters.' >&2; exit 1;
}
if systemctl --user is-active --quiet hermes-personal-agent.service; then
  echo 'Stop the existing hermes-personal-agent user service before preparing or changing it.' >&2; exit 1
fi
repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$project_root" == "$HOME/"* ]] || { echo 'HPA_PROJECT_HOME must be inside the dedicated account home.' >&2; exit 1; }
[[ "$repository_root" =~ ^/[a-zA-Z0-9_./-]+$ && "$repository_root" != *..* ]] || {
  echo 'The repository path must not contain spaces or shell metacharacters.' >&2; exit 1;
}
export HPA_HOME="$project_root/instance"
export HERMES_HOME="$project_root/hermes"
export UV_INSTALL_DIR="$project_root/tools"
export UV_NO_MODIFY_PATH=1
export UV_LINK_MODE=copy
export PATH="$UV_INSTALL_DIR:$HOME/.local/bin:$PATH"
mkdir -p "$project_root/tools" "$HPA_HOME" "$HERMES_HOME"
chmod 700 "$project_root" "$HPA_HOME" "$HERMES_HOME"
if [[ ! -x "$UV_INSTALL_DIR/uv" ]]; then
  curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh
fi
if [[ ! -x "$HOME/.local/bin/hermes" ]]; then
  installer="$project_root/tools/install-hermes.sh"
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/bf0203a794a07aac3ff764972ab9087baa4e4f4e/scripts/install.sh -o "$installer"
  bash "$installer" --commit bf0203a794a07aac3ff764972ab9087baa4e4f4e --non-interactive --skip-computer-use
fi
cd "$repository_root"
uv sync --frozen --python 3.11 --no-dev
if [[ -f "$project_root/system-libs/environment" ]]; then
  "$HOME/.local/bin/hermes" config set terminal.client_env_passthrough '["LD_LIBRARY_PATH","FONTCONFIG_PATH","XDG_DATA_DIRS"]'
fi
cat > "$project_root/hpa" <<WRAPPER
#!/usr/bin/env bash
export HPA_HOME="$HPA_HOME"
export HERMES_HOME="$HERMES_HOME"
export HERMES_BIN="$HOME/.local/bin/hermes"
export PATH="$repository_root/.venv/bin:$UV_INSTALL_DIR:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
if [[ -f "$project_root/system-libs/environment" ]]; then
  set -a
  source "$project_root/system-libs/environment"
  set +a
fi
exec "$repository_root/.venv/bin/hpa" "\$@"
WRAPPER
chmod 700 "$project_root/hpa"
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/hermes-personal-agent.service" <<UNIT
[Unit]
Description=Hermes personal Telegram agent
After=network-online.target

[Service]
Type=simple
Environment=HPA_HOME=$HPA_HOME
Environment=HERMES_HOME=$HERMES_HOME
Environment=HERMES_BIN=$HOME/.local/bin/hermes
Environment=PATH=$repository_root/.venv/bin:$UV_INSTALL_DIR:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=-$project_root/system-libs/environment
WorkingDirectory=$HPA_HOME/workspace
ExecStart=$repository_root/.venv/bin/python -m hermes_personal_agent.cli supervisor
Restart=on-failure
RestartSec=10
TimeoutStopSec=45
MemoryMax=2G
MemorySwapMax=0
CPUQuota=150%
TasksMax=512
NoNewPrivileges=true
UMask=0077
Nice=10

[Install]
WantedBy=default.target
UNIT
cat > "$HOME/.config/systemd/user/hermes-personal-backup.service" <<UNIT
[Unit]
Description=Local Hermes knowledge snapshot

[Service]
Type=oneshot
Environment=HPA_HOME=$HPA_HOME
Environment=HPA_BACKUP_DIR=$project_root/backups
ExecStart=$repository_root/.venv/bin/python $repository_root/scripts/native-backup.py
MemoryMax=256M
CPUQuota=25%
TasksMax=32
NoNewPrivileges=true
UMask=0077
Nice=10
UNIT
cat > "$HOME/.config/systemd/user/hermes-personal-backup.timer" <<'UNIT'
[Unit]
Description=Daily private Hermes knowledge backup

[Timer]
OnCalendar=*-*-* 03:15:00 Asia/Tashkent
RandomizedDelaySec=120
Persistent=true

[Install]
WantedBy=timers.target
UNIT
mkdir -p "$HPA_HOME/workspace"
systemctl --user daemon-reload
echo 'SOFTWARE_PREPARED_SERVICE_NOT_STARTED'
printf 'HPA_HOME=%s\nHERMES_HOME=%s\n' "$HPA_HOME" "$HERMES_HOME"
