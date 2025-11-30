❯ python3 manage.py runserver                                   
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
November 30, 2025 - 11:18:28
Django version 4.2.8, using settings 'docshub.settings'
Starting ASGI/Daphne version 4.0.0 development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
HTTP GET /assets/index-DZH-tyRp.js 200 [0.27, 127.0.0.1:34630]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.27, 127.0.0.1:34624]
HTTP GET /Docs-Hub.png 200 [0.01, 127.0.0.1:34630]
HTTP GET / 200 [0.01, 127.0.0.1:34630]
HTTP GET /assets/index-CjW2QjLo.css 304 [0.02, 127.0.0.1:34630]
HTTP GET /assets/index-DZH-tyRp.js 304 [0.02, 127.0.0.1:34624]
HTTP GET /Docs-Hub.png 304 [0.00, 127.0.0.1:34624]
HTTP GET / 304 [0.00, 127.0.0.1:34624]
HTTP GET / 304 [0.01, 127.0.0.1:34624]
HTTP GET / 304 [0.01, 127.0.0.1:34624]
HTTP GET / 200 [0.02, 127.0.0.1:34624]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.01, 127.0.0.1:34624]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.01, 127.0.0.1:34630]
HTTP GET /Docs-Hub.png 200 [0.01, 127.0.0.1:34630]
HTTP GET / 200 [0.02, 127.0.0.1:34630]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.02, 127.0.0.1:34624]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.03, 127.0.0.1:34630]
HTTP GET /Docs-Hub.png 200 [0.01, 127.0.0.1:34630]
HTTP GET / 200 [0.00, 127.0.0.1:34630]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.02, 127.0.0.1:34630]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.01, 127.0.0.1:34624]
HTTP GET /Docs-Hub.png 200 [0.00, 127.0.0.1:34624]
HTTP GET / 200 [0.01, 127.0.0.1:34624]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.02, 127.0.0.1:34630]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.04, 127.0.0.1:34624]
HTTP GET /Docs-Hub.png 200 [0.00, 127.0.0.1:34624]
HTTP GET / 200 [0.00, 127.0.0.1:34624]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.01, 127.0.0.1:34624]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.01, 127.0.0.1:34630]
HTTP GET /Docs-Hub.png 200 [0.01, 127.0.0.1:34630]
HTTP GET / 200 [0.01, 127.0.0.1:34630]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.03, 127.0.0.1:34630]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.03, 127.0.0.1:34624]
HTTP GET /Docs-Hub.png 200 [0.00, 127.0.0.1:34624]
HTTP GET / 200 [0.00, 127.0.0.1:34624]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.01, 127.0.0.1:34624]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.01, 127.0.0.1:34630]
HTTP GET /Docs-Hub.png 200 [0.01, 127.0.0.1:34630]
HTTP GET /assets/index-DZH-tyRp.js 304 [0.00, 127.0.0.1:34630]
HTTP GET /assets/index-CjW2QjLo.css 304 [0.00, 127.0.0.1:34624]
HTTP GET /Docs-Hub.png 304 [0.00, 127.0.0.1:34624]
HTTP GET / 200 [0.00, 127.0.0.1:32794]
HTTP GET /assets/index-DZH-tyRp.js 200 [0.01, 127.0.0.1:32794]
HTTP GET /assets/index-CjW2QjLo.css 200 [0.01, 127.0.0.1:32802]
HTTP GET /Docs-Hub.png 200 [0.00, 127.0.0.1:32802]
HTTP GET / 304 [0.01, 127.0.0.1:32802]
HTTP GET / 304 [0.01, 127.0.0.1:32802]
HTTP GET / 304 [0.01, 127.0.0.1:32802]
#!/bin/bash

# DocsHub Quick Start
# Run this after dependencies are installed

set -e

echo "🚀 DocsHub Quick Start"
echo ""
echo "Make sure you have 4 terminal windows ready!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Terminal 1 - START REDIS:"
echo "  $ redis-server"
echo ""
echo "Terminal 2 - START DJANGO:"
echo "  $ python manage.py runserver"
echo ""
echo "Terminal 3 - START CELERY (optional):"
echo "  $ celery -A docshub worker -l info"
echo ""
echo "Terminal 4 - READY FOR COMMANDS:"
echo "  You can create a superuser:"
echo "  $ python manage.py createsuperuser"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access the app at: http://localhost:8000"
echo "🔐 Admin panel at:    http://localhost:8000/admin"
echo ""
echo "📝 Features:"
echo "  ✓ Real-time collaborative editing"
echo "  ✓ Documents & Spreadsheets"
echo "  ✓ User authentication"
echo "  ✓ Version history"
echo ""
