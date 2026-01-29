# Google Cloud File Vault - Technical Assessment

A secure, serverless file vault deployed on Google Cloud that enforces strict per-user isolation, irreversible PII redaction, and intelligent data extraction using Vertex AI (Gemini).

## 📋 Project Overview

**Core Philosophy: Zero Trust Redaction & Least Privilege.**
This system ensures sensitive PII is visually and structurally removed from documents *before* they are permanently stored or processed by AI. The extraction model never sees the original file.

---

## 🏗️ Architecture & Data Flow

The solution is a **Serverless Monolith** (FastAPI) on Cloud Run, leveraging fully managed Google Cloud services for state and security.

```mermaid
graph TD
    User([User]) -->|1. Upload PDF| API[Cloud Run API (FastAPI)]
    
    subgraph "Zone 1: Quarantine (Ephemeral)"
        API -->|Stream Raw| QB[Quarantine Bucket]
        API -->|Stream Redacted| QB
    end
    
    subgraph "Zone 2: Processing (Stateless)"
        API -->|2. Rasterize & Redact| DLP[Cloud DLP + pdf2image]
    end
    
    subgraph "Zone 3: Human Gate"
        User -->|3. View Preview| SignedURL[Signed URL (Redacted Only)]
        User -->|4. Approve| API
    end
    
    subgraph "Zone 4: The Vault (Secure)"
        API -->|5. Move Redacted| VB[Vault Bucket]
        API -->|6. Extract Data| Vertex[Vertex AI (Gemini)]
        Vertex -->|Read Redacted| VB
    end
    
    subgraph "Zone 5: Persistence"
        API -->|7. Write JSON| SQL[Cloud SQL (PostgreSQL)]
    end
    
    style QB fill:#ffcccc,stroke:#333,stroke-width:2px
    style VB fill:#ccffcc,stroke:#333,stroke-width:2px
    style Vertex fill:#ccccff,stroke:#333,stroke-width:2px
