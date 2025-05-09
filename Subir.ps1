# Ruta del proyecto
$proyecto = "C:\Users\El3imm\OneDrive\Escritorio\DesarrollAMO"

# Eliminar y reiniciar Git
if (Test-Path ".git") {
    Remove-Item -Recurse -Force .git
}
git init
git checkout -b main
git remote add origin https://github.com/amoedo7/DesarrollAmo.git

# Agregar y subir solo README.md
git add . 
$mensaje = Read-Host "📝 Escribí el mensaje del commit"
git commit -m "$mensaje"
git push -u origin main --force

Write-Host "n✅ ¡Listo! El repositorio en GitHub solo tiene el nuevo README.md." -ForegroundColor Green
