#!/data/data/com.termux/files/usr/bin/fish
set -l target "$HOME/AMO_AI/bin/camo-status.py"
mkdir -p (dirname $target)
curl -fsSL "https://raw.githubusercontent.com/amoedo7/DesarrollAmo/main/tools/camo_status.py" -o $target
python $target --self-test; or begin
    echo "CAMO Status: falló el self-test; no se instaló" >&2
    rm -f $target
    return 1
end
chmod +x $target
if not contains "$HOME/AMO_AI/bin" $PATH
    fish_add_path "$HOME/AMO_AI/bin"
end
ln -sf $target "$HOME/AMO_AI/bin/camo-status"
echo "CAMO Status v2.1 instalado · caché 120 s · metadata 6 h"
echo "Ejecutá: camo-status   |   Forzar red: camo-status --fresh"
