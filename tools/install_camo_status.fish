#!/data/data/com.termux/files/usr/bin/fish
set -l target "$HOME/AMO_AI/bin/camo-status.py"
mkdir -p (dirname $target)
curl -fsSL "https://raw.githubusercontent.com/amoedo7/DesarrollAmo/main/tools/camo_status.py" -o $target
chmod +x $target
if not contains "$HOME/AMO_AI/bin" $PATH
    fish_add_path "$HOME/AMO_AI/bin"
end
ln -sf $target "$HOME/AMO_AI/bin/camo-status"
echo "CAMO Status instalado. Ejecutá: camo-status"
