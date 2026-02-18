"""
Servidor HTTP simple para servir el dashboard
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

# Cambiar al directorio del proyecto
project_dir = Path(__file__).parent
os.chdir(project_dir)

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def translate_path(self, path):
        """Traduce rutas de URL a rutas del sistema de archivos"""
        if path == '/':
            path = '/dashboard.html'
        return super().translate_path(path)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"[{self.client_address[0]}] {format % args}")

# Mostrar diagnóstico
cwd = os.getcwd()
print(f"📁 Directorio de trabajo: {cwd}")
print(f"\n📂 Archivos en el directorio raíz:")
for item in sorted(os.listdir('.')):
    if os.path.isfile(item):
        print(f"   📄 {item}")
        
print(f"\n📂 Subdirectorios:")
for item in sorted(os.listdir('.')):
    if os.path.isdir(item) and not item.startswith('.'):
        files = [f for f in os.listdir(item) if os.path.isfile(os.path.join(item, f))]
        print(f"   📁 {item}/ ({len(files)} archivos)")

print(f"\n{'='*60}")
print(f"✅ Servidor iniciado en http://localhost:{PORT}")
print(f"📊 Abre en tu navegador: http://localhost:{PORT}/dashboard.html")
print(f"{'='*60}\n")

try:
    # Permitir reutilizar el puerto
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n❌ Servidor detenido")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
