# DocsHub Architecture Documentation

> A comprehensive guide to the architecture, design patterns, and system structure of DocsHub

---

## 📐 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Component Structure](#component-structure)
5. [Data Flow](#data-flow)
6. [Module Dependencies](#module-dependencies)
7. [Database Schema](#database-schema)
8. [API Architecture](#api-architecture)
9. [Real-time Collaboration](#real-time-collaboration)
10. [Testing Architecture](#testing-architecture)
11. [Deployment Architecture](#deployment-architecture)

---

## 🏗️ System Overview

DocsHub is a modern, real-time collaborative document and spreadsheet editor built with a **Django REST API backend** and a **React TypeScript frontend**, connected via **WebSockets** for real-time synchronization.

### Core Principles

- **Separation of Concerns**: Clear separation between frontend and backend
- **RESTful API**: Standard REST endpoints for all operations
- **Real-time Sync**: WebSocket-based collaboration for instant updates
- **Role-Based Access**: Fine-grained permission system
- **Scalable Design**: Modular architecture for easy extension

---

## 🎨 Architecture Diagram

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        React[React Frontend<br/>TypeScript + Vite]
    end
    
    subgraph "API Gateway"
        Django[Django Server<br/>ASGI/WSGI]
        REST[REST API<br/>DRF]
        WS[WebSocket<br/>Channels]
    end
    
    subgraph "Application Layer"
        Accounts[Accounts App<br/>Auth & Users]
        Documents[Documents App<br/>Document Management]
        Spreadsheets[Spreadsheets App<br/>Spreadsheet Management]
        Notifications[Notifications App<br/>User Notifications]
        Collaboration[Collaboration App<br/>WebSocket Consumers]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL/SQLite<br/>Database)]
        RedisCache[(Redis<br/>Channel Layer)]
    end
    
    subgraph "Background Services"
        Celery[Celery Worker<br/>Background Tasks]
    end
    
    Browser --> React
    React -->|HTTP/REST| REST
    React -->|WebSocket| WS
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
    Collaboration --> RedisCache
    Collaboration --> DB
    Celery --> DB
    Celery --> RedisCache
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (React)
    participant API as Django REST API
    participant WS as WebSocket
    participant DB as Database
    participant R as Redis
    
    U->>F: Opens Document
    F->>API: GET /api/documents/{id}/
    API->>DB: Query Document
    DB-->>API: Document Data
    API-->>F: Document JSON
    F->>WS: Connect to WebSocket
    WS->>R: Join Channel Group
    WS-->>F: Connection Established
    
    U->>F: Types Content
    F->>WS: Send content_update
    WS->>R: Broadcast to Group
    R->>WS: Distribute to All Clients
    WS-->>F: Receive Update
    F->>API: POST /api/documents/{id}/update/ (debounced)
    API->>DB: Save Document
    DB-->>API: Success
    API-->>F: Confirmation
```

---

## 🛠️ Technology Stack

### Backend Stack

```mermaid
graph LR
    subgraph "Core Framework"
        Django[Django 4.2]
        DRF[Django REST Framework]
        Channels[Django Channels 4.0]
    end
    
    subgraph "Server"
        Daphne[Daphne ASGI Server]
        Gunicorn[Gunicorn WSGI]
    end
    
    subgraph "Database"
        PostgreSQL[PostgreSQL]
        SQLite[SQLite Dev]
    end
    
    subgraph "Cache & Messaging"
        RedisServer[Redis Server]
    end
    
    subgraph "Task Queue"
        Celery[Celery 5.3]
    end
    
    Django --> DRF
    Django --> Channels
    Channels --> Daphne
    Django --> Gunicorn
    Django --> PostgreSQL
    Django --> SQLite
    Channels --> RedisServer
    Celery --> RedisServer
```

### Frontend Stack

```mermaid
graph LR
    subgraph "Core"
        React[React 18]
        TypeScript[TypeScript]
        Vite[Vite Build Tool]
    end
    
    subgraph "UI & Styling"
        Tailwind[TailwindCSS]
        Lucide[Lucide Icons]
    end
    
    subgraph "State & Routing"
        Zustand[Zustand State]
        Router[React Router]
    end
    
    subgraph "Editors"
        Quill[Quill Editor]
        Handsontable[Handsontable]
    end
    
    subgraph "Communication"
        Axios[Axios HTTP]
        WebSocket[WebSocket API]
    end
    
    React --> TypeScript
    TypeScript --> Vite
    React --> Tailwind
    React --> Zustand
    React --> Router
    React --> Quill
    React --> Handsontable
    React --> Axios
    React --> WebSocket
```

---

## 🧩 Component Structure

### Django App Structure

```mermaid
graph TD
    subgraph "docshub (Project Root)"
        Settings[settings.py<br/>Configuration]
        URLs[urls.py<br/>URL Routing]
        ASGI[asgi.py<br/>WebSocket Setup]
        WSGI[wsgi.py<br/>HTTP Setup]
    end
    
    subgraph "accounts App"
        A_Models[models.py<br/>User Models]
        A_Views[views.py<br/>Auth Views]
        A_API[api.py<br/>Auth API]
        A_Admin[admin.py<br/>User Admin]
    end
    
    subgraph "documents App"
        D_Models[models.py<br/>Document Models]
        D_API[api.py<br/>Document API]
        D_Views[views.py<br/>Document Views]
        D_Utils[utils.py<br/>Document Utils]
        D_Admin[admin.py<br/>Document Admin]
    end
    
    subgraph "spreadsheets App"
        S_Models[models.py<br/>Spreadsheet Models]
        S_API[api.py<br/>Spreadsheet API]
        S_Utils[utils.py<br/>Spreadsheet Utils]
        S_Admin[admin.py<br/>Spreadsheet Admin]
    end
    
    subgraph "notifications App"
        N_Models[models.py<br/>Notification Models]
        N_API[api.py<br/>Notification API]
        N_Context[context_processors.py<br/>Template Context]
    end
    
    subgraph "collaboration App"
        C_Consumers[consumers.py<br/>WebSocket Consumers]
        C_Routing[routing.py<br/>WebSocket Routes]
    end
    
    Settings --> A_Models
    Settings --> D_Models
    Settings --> S_Models
    Settings --> N_Models
    URLs --> A_API
    URLs --> D_API
    URLs --> S_API
    URLs --> N_API
    ASGI --> C_Routing
    C_Routing --> C_Consumers
```

### Frontend Component Structure

```mermaid
graph TD
    subgraph "src/"
        App[App.tsx<br/>Main Application]
        Main[main.tsx<br/>Entry Point]
        
        subgraph "pages/"
            Dashboard[Dashboard.tsx]
            Login[Login.tsx]
            Register[Register.tsx]
            DocEditor[DocumentEditor.tsx]
            SheetEditor[SpreadsheetEditor.tsx]
        end
        
        subgraph "components/"
            Layout[Layout.tsx<br/>App Layout]
        end
        
        subgraph "services/"
            API[api.ts<br/>API Client]
            WebSocket[websocket.ts<br/>WebSocket Manager]
        end
        
        Store[store.ts<br/>Zustand Store]
    end
    
    App --> Dashboard
    App --> Login
    App --> Register
    App --> DocEditor
    App --> SheetEditor
    App --> Layout
    DocEditor --> API
    DocEditor --> WebSocket
    SheetEditor --> API
    SheetEditor --> WebSocket
    Dashboard --> API
    API --> Store
    WebSocket --> Store
```

---

## 🔄 Data Flow

### Document Editing Flow

```mermaid
flowchart TD
    Start([User Opens Document]) --> Load[Frontend: Load Document]
    Load --> API1[API: GET /api/documents/id/]
    API1 --> DB1[(Database: Query Document)]
    DB1 --> Return1[Return Document Data]
    Return1 --> Render[Frontend: Render in Quill Editor]
    Render --> Connect[Frontend: Connect WebSocket]
    Connect --> WS1[WebSocket: Join Room]
    WS1 --> Ready[Ready for Editing]
    
    Ready --> UserEdit[User Types Content]
    UserEdit --> LocalUpdate[Frontend: Update Local State]
    LocalUpdate --> WS2[WebSocket: Send content_update]
    WS2 --> Broadcast[Redis: Broadcast to All Clients]
    Broadcast --> OtherUsers[Other Users: Receive Update]
    Broadcast --> Debounce[Frontend: Debounce Save]
    Debounce --> API2[API: POST /api/documents/id/update/]
    API2 --> DB2[(Database: Save Document)]
    DB2 --> Success[Save Success]
    
    style Start fill:#e1f5ff
    style Ready fill:#c8e6c9
    style Success fill:#c8e6c9
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as Django API
    participant DB as Database
    participant S as Session
    
    U->>F: Enter Credentials
    F->>API: POST /api/accounts/login/
    API->>DB: Verify User
    DB-->>API: User Data
    API->>S: Create Session
    S-->>API: Session ID
    API-->>F: User Data + Cookie
    F->>F: Store in Zustand
    F-->>U: Redirect to Dashboard
```

### Document Sharing Flow

```mermaid
flowchart LR
    Owner[Document Owner] --> Share[Share Document]
    Share --> API[API: POST /api/documents/id/share/]
    API --> Check{User Exists?}
    Check -->|No| Error[Return Error]
    Check -->|Yes| CreatePerm[Create Permission]
    CreatePerm --> Notify[Create Notification]
    Notify --> DB[(Save to Database)]
    DB --> Email[Send Email Notification]
    Email --> Recipient[Recipient User]
    
    style Owner fill:#fff9c4
    style Recipient fill:#c8e6c9
    style Error fill:#ffcdd2
```

---

## 🔗 Module Dependencies

### Backend Dependencies Graph

```mermaid
graph TD
    subgraph "Core Django"
        Django[Django Framework]
        DRF[Django REST Framework]
        Channels[Django Channels]
    end
    
    subgraph "Apps"
        Accounts[accounts]
        Documents[documents]
        Spreadsheets[spreadsheets]
        Notifications[notifications]
        Collaboration[collaboration]
    end
    
    subgraph "External Services"
        RedisService[Redis]
        Celery[Celery]
    end
    
    Django --> Accounts
    Django --> Documents
    Django --> Spreadsheets
    Django --> Notifications
    Django --> Collaboration
    DRF --> Accounts
    DRF --> Documents
    DRF --> Spreadsheets
    DRF --> Notifications
    Channels --> Collaboration
    Collaboration --> RedisCache
    Documents --> Notifications
    Spreadsheets --> Notifications
    Accounts --> Documents
    Accounts --> Spreadsheets
    Celery --> RedisCache
    Celery --> Documents
```

### Frontend Dependencies Graph

```mermaid
graph TD
    subgraph "Core"
        React[React]
        TypeScript[TypeScript]
        Vite[Vite]
    end
    
    subgraph "Pages"
        Dashboard[Dashboard]
        Login[Login]
        Register[Register]
        DocEditor[DocumentEditor]
        SheetEditor[SpreadsheetEditor]
    end
    
    subgraph "Services"
        API[api.ts]
        WebSocket[websocket.ts]
        Store[store.ts]
    end
    
    React --> Dashboard
    React --> Login
    React --> Register
    React --> DocEditor
    React --> SheetEditor
    DocEditor --> API
    DocEditor --> WebSocket
    DocEditor --> Store
    SheetEditor --> API
    SheetEditor --> WebSocket
    SheetEditor --> Store
    Dashboard --> API
    API --> Store
    WebSocket --> Store
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Document : owns
    User ||--o{ Spreadsheet : owns
    User ||--o{ DocumentPermission : has
    User ||--o{ SpreadsheetPermission : has
    User ||--o{ Notification : receives
    User ||--o{ DocumentComment : creates
    User ||--o{ SpreadsheetComment : creates
    User ||--o{ DocumentVersion : creates
    User ||--o{ SpreadsheetVersion : creates
    
    Document ||--o{ DocumentPermission : has
    Document ||--o{ DocumentComment : has
    Document ||--o{ DocumentVersion : has
    
    Spreadsheet ||--o{ SpreadsheetPermission : has
    Spreadsheet ||--o{ SpreadsheetComment : has
    Spreadsheet ||--o{ SpreadsheetVersion : has
    
    User {
        int id PK
        string username
        string email
        string password
        datetime date_joined
    }
    
    Document {
        int id PK
        int owner_id FK
        string title
        text content
        string document_type
        datetime created_at
        datetime updated_at
    }
    
    DocumentPermission {
        int id PK
        int document_id FK
        int user_id FK
        string role
        datetime created_at
    }
    
    Spreadsheet {
        int id PK
        int owner_id FK
        string title
        json data
        datetime created_at
        datetime updated_at
    }
    
    Notification {
        int id PK
        int recipient_id FK
        string notification_type
        string title
        text message
        bool read
        datetime created_at
    }
```

### Model Relationships

```mermaid
graph LR
    User -->|1:N| Document
    User -->|1:N| Spreadsheet
    User -->|1:N| DocumentPermission
    User -->|1:N| SpreadsheetPermission
    User -->|1:N| Notification
    User -->|1:N| DocumentComment
    User -->|1:N| SpreadsheetComment
    
    Document -->|1:N| DocumentPermission
    Document -->|1:N| DocumentComment
    Document -->|1:N| DocumentVersion
    
    Spreadsheet -->|1:N| SpreadsheetPermission
    Spreadsheet -->|1:N| SpreadsheetComment
    Spreadsheet -->|1:N| SpreadsheetVersion
```

---

## 🌐 API Architecture

### API Endpoint Structure

```mermaid
graph TD
    subgraph "Authentication API"
        A1[POST /api/accounts/register/]
        A2[POST /api/accounts/login/]
        A3[POST /api/accounts/logout/]
        A4[GET /api/accounts/profile/]
    end
    
    subgraph "Documents API"
        D1[GET /api/documents/]
        D2[POST /api/documents/create/]
        D3[GET /api/documents/id/]
        D4[POST /api/documents/id/update/]
        D5[POST /api/documents/id/delete/]
        D6[POST /api/documents/id/share/]
        D7[POST /api/documents/id/remove/]
    end
    
    subgraph "Spreadsheets API"
        S1[GET /api/spreadsheets/]
        S2[POST /api/spreadsheets/create/]
        S3[GET /api/spreadsheets/id/]
        S4[POST /api/spreadsheets/id/update/]
        S5[POST /api/spreadsheets/id/delete/]
    end
    
    subgraph "Notifications API"
        N1[GET /api/notifications/]
        N2[GET /api/notifications/unread-count/]
    end
```

### API Request/Response Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant M as Middleware
    participant V as View
    participant S as Serializer
    participant M2 as Model
    participant DB as Database
    
    C->>M: HTTP Request
    M->>M: Authentication Check
    M->>M: CORS Check
    M->>V: Route to View
    V->>V: Permission Check
    V->>S: Validate Data
    S->>M2: Create/Update Model
    M2->>DB: Database Operation
    DB-->>M2: Result
    M2-->>S: Model Instance
    S-->>V: Serialized Data
    V-->>M: HTTP Response
    M-->>C: JSON Response
```

---

## ⚡ Real-time Collaboration

### WebSocket Architecture

```mermaid
graph TB
    subgraph "Client 1"
        C1[React Component]
        WS1[WebSocket Client]
    end
    
    subgraph "Client 2"
        C2[React Component]
        WS2[WebSocket Client]
    end
    
    subgraph "Django Channels"
        ASGI[ASGI Application]
        Router[URL Router]
        Consumer[DocumentConsumer]
        Channel[Channel Layer]
    end
    
    subgraph "Redis Layer"
        RedisServer[(Redis Server)]
        Groups[Channel Groups]
    end
    
    C1 --> WS1
    C2 --> WS2
    WS1 --> ASGI
    WS2 --> ASGI
    ASGI --> Router
    Router --> Consumer
    Consumer --> Channel
    Channel --> RedisServer
    RedisServer --> Groups
    Groups --> Channel
    Channel --> Consumer
    Consumer --> WS1
    Consumer --> WS2
    WS1 --> C1
    WS2 --> C2
```

### Real-time Update Flow

```mermaid
sequenceDiagram
    participant U1 as User 1
    participant F1 as Frontend 1
    participant WS as WebSocket
    participant R as Redis
    participant F2 as Frontend 2
    participant U2 as User 2
    
    U1->>F1: Types Content
    F1->>WS: Send content_update
    WS->>R: Broadcast to Group
    R->>F2: Distribute Message
    F2->>U2: Update UI
    F1->>F1: Debounce Timer
    F1->>WS: Save to Database (API)
    WS-->>F1: Save Confirmation
```

---

## 🧪 Testing Architecture

### Test Coverage Map

```mermaid
graph TD
    subgraph "Test Suites"
        T1[accounts/tests.py<br/>10 tests]
        T2[documents/tests.py<br/>25 tests]
        T3[spreadsheets/tests.py<br/>15 tests]
        T4[notifications/tests.py<br/>8 tests]
        T5[collaboration/tests.py<br/>8 tests]
    end
    
    subgraph "Test Types"
        Model[Model Tests]
        API[API Tests]
        Perm[Permission Tests]
        WS[WebSocket Tests]
    end
    
    T1 --> Model
    T1 --> API
    T2 --> Model
    T2 --> API
    T2 --> Perm
    T3 --> Model
    T3 --> API
    T3 --> Perm
    T4 --> Model
    T4 --> API
    T5 --> WS
    
    style T1 fill:#e3f2fd
    style T2 fill:#e8f5e9
    style T3 fill:#fff3e0
    style T4 fill:#f3e5f5
    style T5 fill:#fce4ec
```

### Test Execution Flow

```mermaid
flowchart TD
    Start([Run Tests]) --> Setup[Set Up Test Database]
    Setup --> Load[Load Test Fixtures]
    Load --> Run[Execute Test Cases]
    Run --> Model[Model Tests]
    Run --> API[API Tests]
    Run --> WS[WebSocket Tests]
    Model --> Assert[Assert Results]
    API --> Assert
    WS --> Assert
    Assert --> Report[Generate Report]
    Report --> Cleanup[Clean Up Test Database]
    Cleanup --> End([Tests Complete])
    
    style Start fill:#e1f5ff
    style End fill:#c8e6c9
```

---

## 🚀 Deployment Architecture

### Production Deployment

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx]
    end
    
    subgraph "Application Servers"
        App1[Django App 1]
        App2[Django App 2]
        App3[Django App 3]
    end
    
    subgraph "Database Cluster"
        DB1[(PostgreSQL Primary)]
        DB2[(PostgreSQL Replica)]
    end
    
    subgraph "Cache & Queue"
        RedisMaster[(Redis Master)]
        RedisReplica[(Redis Replica)]
    end
    
    subgraph "Background Workers"
        Celery1[Celery Worker 1]
        Celery2[Celery Worker 2]
    end
    
    subgraph "Static Files"
        CDN[CDN/Cloud Storage]
    end
    
    LB --> App1
    LB --> App2
    LB --> App3
    App1 --> DB1
    App2 --> DB1
    App3 --> DB1
    DB1 --> DB2
    App1 --> RedisMaster
    App2 --> RedisMaster
    App3 --> RedisMaster
    RedisMaster --> RedisReplica
    Celery1 --> RedisMaster
    Celery2 --> RedisMaster
    Celery1 --> DB1
    Celery2 --> DB1
    App1 --> CDN
    App2 --> CDN
    App3 --> CDN
```

---

## 📊 System Metrics & Monitoring

### Key Performance Indicators

```mermaid
graph LR
    subgraph "Performance"
        Latency[API Latency]
        Throughput[Request Throughput]
        WS_Conn[WebSocket Connections]
    end
    
    subgraph "Reliability"
        Uptime[System Uptime]
        Error_Rate[Error Rate]
        Success_Rate[Success Rate]
    end
    
    subgraph "Scalability"
        Concurrent_Users[Concurrent Users]
        DB_Conn[Database Connections]
        Redis_Mem[Redis Memory]
    end
```

---

## 🔐 Security Architecture

### Security Layers

```mermaid
graph TD
    subgraph "Network Layer"
        HTTPS[HTTPS/TLS]
        WSS[WSS/TLS]
    end
    
    subgraph "Application Layer"
        Auth[Authentication]
        Authz[Authorization]
        CSRF[CSRF Protection]
        CORS[CORS Policy]
    end
    
    subgraph "Data Layer"
        Encryption[Data Encryption]
        Validation[Input Validation]
        Sanitization[Output Sanitization]
    end
    
    HTTPS --> Auth
    WSS --> Auth
    Auth --> Authz
    Authz --> CSRF
    CSRF --> CORS
    CORS --> Encryption
    Encryption --> Validation
    Validation --> Sanitization
```

---

## 📝 Summary

### Architecture Highlights

- ✅ **Modular Design**: Clear separation of concerns with Django apps
- ✅ **RESTful API**: Standard REST endpoints for all operations
- ✅ **Real-time Sync**: WebSocket-based collaboration via Django Channels
- ✅ **Scalable**: Horizontal scaling support with Redis and Celery
- ✅ **Tested**: Comprehensive test suite covering all major features
- ✅ **Secure**: Multiple layers of security (HTTPS, authentication, authorization)
- ✅ **Type-Safe**: TypeScript on frontend, type hints in Python
- ✅ **Modern Stack**: Latest versions of Django, React, and supporting libraries

### Technology Choices

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Backend** | Django 4.2 | Mature, feature-rich, excellent ORM |
| **API** | Django REST Framework | Industry standard, well-documented |
| **WebSocket** | Django Channels | Native Django integration |
| **Frontend** | React 18 + TypeScript | Modern, type-safe, component-based |
| **Database** | PostgreSQL | Robust, ACID-compliant, scalable |
| **Cache** | Redis | Fast, supports pub/sub for WebSockets |
| **Task Queue** | Celery | Reliable background task processing |

---

**Last Updated**: 2025-01-27  
**Version**: 1.0.0  
**Maintainer**: DocsHub Development Team

