# Architecture Diagrams - Source Files

This file contains diagram source code that can be rendered using various tools.

## Mermaid Diagrams

All diagrams in `ARCHITECTURE.md` are written in Mermaid syntax. You can:

1. **View in GitHub**: Mermaid diagrams render automatically in GitHub markdown
2. **View in VS Code**: Install the "Markdown Preview Mermaid Support" extension
3. **Export as Images**: Use [Mermaid Live Editor](https://mermaid.live/) or [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)

## Graphviz DOT Format

### System Architecture (DOT)

```dot
digraph SystemArchitecture {
    rankdir=TB;
    node [shape=box, style=rounded];
    
    subgraph cluster_client {
        label="Client Layer";
        Browser [label="Web Browser"];
        React [label="React Frontend\nTypeScript + Vite"];
        Browser -> React;
    }
    
    subgraph cluster_api {
        label="API Gateway";
        Django [label="Django Server\nASGI/WSGI"];
        REST [label="REST API\nDRF"];
        WS [label="WebSocket\nChannels"];
        Django -> REST;
        Django -> WS;
    }
    
    subgraph cluster_apps {
        label="Application Layer";
        Accounts [label="Accounts App"];
        Documents [label="Documents App"];
        Spreadsheets [label="Spreadsheets App"];
        Notifications [label="Notifications App"];
        Collaboration [label="Collaboration App"];
    }
    
    subgraph cluster_data {
        label="Data Layer";
        DB [label="PostgreSQL/SQLite\nDatabase", shape=cylinder];
        Redis [label="Redis\nChannel Layer", shape=cylinder];
    }
    
    React -> REST [label="HTTP/REST"];
    React -> WS [label="WebSocket"];
    REST -> Django;
    WS -> Django;
    Django -> Accounts;
    Django -> Documents;
    Django -> Spreadsheets;
    Django -> Notifications;
    Django -> Collaboration;
    Accounts -> DB;
    Documents -> DB;
    Spreadsheets -> DB;
    Notifications -> DB;
    Collaboration -> Redis;
    Collaboration -> DB;
}
```

### Module Dependencies (DOT)

```dot
digraph ModuleDependencies {
    rankdir=LR;
    node [shape=box];
    
    subgraph cluster_core {
        label="Core Django";
        Django [label="Django Framework"];
        DRF [label="Django REST Framework"];
        Channels [label="Django Channels"];
    }
    
    subgraph cluster_apps {
        label="Apps";
        Accounts [label="accounts"];
        Documents [label="documents"];
        Spreadsheets [label="spreadsheets"];
        Notifications [label="notifications"];
        Collaboration [label="collaboration"];
    }
    
    subgraph cluster_external {
        label="External Services";
        Redis [label="Redis", shape=cylinder];
        Celery [label="Celery", shape=cylinder];
    }
    
    Django -> Accounts;
    Django -> Documents;
    Django -> Spreadsheets;
    Django -> Notifications;
    Django -> Collaboration;
    DRF -> Accounts;
    DRF -> Documents;
    DRF -> Spreadsheets;
    DRF -> Notifications;
    Channels -> Collaboration;
    Collaboration -> Redis;
    Documents -> Notifications;
    Spreadsheets -> Notifications;
    Accounts -> Documents;
    Accounts -> Spreadsheets;
    Celery -> Redis;
    Celery -> Documents;
}
```

### Database Schema (DOT)

```dot
digraph DatabaseSchema {
    rankdir=TB;
    node [shape=record];
    
    User [label="{User|id: int (PK)\lusername: string\lemail: string\lpassword: string\ldate_joined: datetime}"];
    
    Document [label="{Document|id: int (PK)\lowner_id: int (FK)\ltitle: string\lcontent: text\ldocument_type: string\lcreated_at: datetime\lupdated_at: datetime}"];
    
    DocumentPermission [label="{DocumentPermission|id: int (PK)\ldocument_id: int (FK)\luser_id: int (FK)\lrole: string\lcreated_at: datetime}"];
    
    Spreadsheet [label="{Spreadsheet|id: int (PK)\lowner_id: int (FK)\ltitle: string\ldata: json\lcreated_at: datetime\lupdated_at: datetime}"];
    
    Notification [label="{Notification|id: int (PK)\lrecipient_id: int (FK)\lnotification_type: string\ltitle: string\lmessage: text\lread: bool\lcreated_at: datetime}"];
    
    User -> Document [label="1:N owns"];
    User -> Spreadsheet [label="1:N owns"];
    User -> DocumentPermission [label="1:N has"];
    User -> Notification [label="1:N receives"];
    Document -> DocumentPermission [label="1:N has"];
}
```

## PlantUML Format

### Component Diagram (PlantUML)

```plantuml
@startuml
!define RECTANGLE class

package "Client Layer" {
    [Web Browser] as Browser
    [React Frontend] as React
    Browser --> React
}

package "API Gateway" {
    [Django Server] as Django
    [REST API] as REST
    [WebSocket] as WS
    Django --> REST
    Django --> WS
}

package "Application Layer" {
    [Accounts App] as Accounts
    [Documents App] as Documents
    [Spreadsheets App] as Spreadsheets
    [Notifications App] as Notifications
    [Collaboration App] as Collaboration
}

package "Data Layer" {
    database "PostgreSQL/SQLite" as DB
    database "Redis" as Redis
}

React --> REST : HTTP/REST
React --> WS : WebSocket
REST --> Django
WS --> Django
Django --> Accounts
Django --> Documents
Django --> Spreadsheets
Django --> Notifications
Django --> Collaboration
Accounts --> DB
Documents --> DB
Spreadsheets --> DB
Notifications --> DB
Collaboration --> Redis
Collaboration --> DB

@enduml
```

### Sequence Diagram (PlantUML)

```plantuml
@startuml
actor User
participant "Frontend (React)" as Frontend
participant "Django REST API" as API
participant "WebSocket" as WS
participant "Database" as DB
participant "Redis" as Redis

User -> Frontend: Opens Document
Frontend -> API: GET /api/documents/{id}/
API -> DB: Query Document
DB --> API: Document Data
API --> Frontend: Document JSON
Frontend -> WS: Connect to WebSocket
WS -> Redis: Join Channel Group
WS --> Frontend: Connection Established

User -> Frontend: Types Content
Frontend -> WS: Send content_update
WS -> Redis: Broadcast to Group
Redis -> WS: Distribute to All Clients
WS --> Frontend: Receive Update
Frontend -> API: POST /api/documents/{id}/update/
API -> DB: Save Document
DB --> API: Success
API --> Frontend: Confirmation
@enduml
```

## Rendering Instructions

### Using Mermaid CLI

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Render diagram to PNG
mmdc -i architecture.mmd -o architecture.png

# Render diagram to SVG
mmdc -i architecture.mmd -o architecture.svg
```

### Using Graphviz

```bash
# Install Graphviz
# Ubuntu/Debian: sudo apt-get install graphviz
# macOS: brew install graphviz
# Windows: Download from https://graphviz.org/

# Render DOT file
dot -Tpng architecture.dot -o architecture.png
dot -Tsvg architecture.dot -o architecture.svg
```

### Using PlantUML

```bash
# Install PlantUML
# Download from http://plantuml.com/starting

# Render PlantUML file
java -jar plantuml.jar architecture.puml
```

## Online Tools

- **Mermaid Live Editor**: https://mermaid.live/
- **Graphviz Online**: https://dreampuf.github.io/GraphvizOnline/
- **PlantUML Online**: http://www.plantuml.com/plantuml/uml/

## Export Formats

All diagrams can be exported to:
- **PNG**: For presentations and documents
- **SVG**: For scalable vector graphics
- **PDF**: For documentation
- **HTML**: For interactive web pages

