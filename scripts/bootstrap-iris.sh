#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
readonly script_dir
repo_root="$(cd "${script_dir}/.." && pwd)"
readonly repo_root

cd "${repo_root}"

docker compose up -d iris
docker compose exec iris /docker-entrypoint-initdb.d/init.sh

grant_output="$(docker compose exec -T iris iris session "${IRIS_INSTANCE:-IRIS}" -U %SYS <<'EOF'
set serviceRole=$system.Util.GetEnviron("MEDSENT_SERVICE_ROLE")
if serviceRole="" set serviceRole="VeSafe_Service"
kill props
set props("Resources")="VeSafe_Data:RWU,VeSafe_Wallet_Use:U,VeSafe_Wallet_Edit:W,VeSafe_FHIR_Use:U,VeSafe_FHIR_Edit:W,"_$CHAR(37)_"Native_GlobalAccess:U"
set sc=##class(Security.Roles).Modify(serviceRole,.props)
if $SYSTEM.Status.IsError(sc) write !,"[VeSafe] Unable to grant native global access to "_serviceRole,!
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc)
if $SYSTEM.Status.IsError(sc) halt
write !,"[VeSafe] Granted "_$CHAR(37)_"Native_GlobalAccess to "_serviceRole,!
halt
EOF
)"

printf '%s\n' "${grant_output}"

if [[ "${grant_output}" != *"[VeSafe] Granted %Native_GlobalAccess"* ]]; then
  echo "MedSim IRIS native-global bootstrap failed" >&2
  exit 1
fi
