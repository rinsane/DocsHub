# DocsHub

Real-time collaborative document and spreadsheet editor.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
npm install
npm run build
```

### 2. Start Services

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Django
python manage.py runserver

# Terminal 3: Celery (optional, for background tasks)
celery -A docshub worker -l info
```

### 3. Access the App

- **Frontend:** http://localhost:8000
- **Admin:** http://localhost:8000/admin

## Features

- Real-time collaborative editing (documents & spreadsheets)
- User authentication & role-based permissions
- Rich text editor (Quill)
- Spreadsheet grid (Handsontable)
- WebSocket-based sync
- Version history
- Comments
- Import/Export

## Tech Stack

- **Backend:** Django 4.2 + Channels 4.0 + Redis
- **Frontend:** React 18 + TypeScript + Vite + TailwindCSS

## Create Superuser

```bash
python manage.py createsuperuser
```

## Project Structure

```
├── docshub/          # Django settings & ASGI
├── accounts/         # User authentication
├── documents/        # Document management
├── spreadsheets/     # Spreadsheet management
├── collaboration/    # Real-time sync
├── notifications/    # User notifications
├── src/              # React frontend source
│   ├── pages/        # Page components
│   ├── components/   # Shared components
│   ├── services/     # WebSocket, API
│   └── App.tsx       # Main app
└── static/dist/      # Built React app (served by Django)
```

## Development

- Frontend changes: edit files in `src/`, then run `npm run build`
- Backend changes: edit Django files, Django will auto-reload
- Database: use `/admin` to manage data
- WebSocket: automatically connects when opening documents

## Browser Support

Chrome, Firefox, Safari, Edge (latest versions)

