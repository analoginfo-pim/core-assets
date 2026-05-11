# PIM-ORM Architecture Patterns and Conventions

> **Vendored, read-only reference.** Canonical edits live in
> [`analoginfo-pim/mix-orm` — `crates/orm-core/ARCHITECTURE_PATTERNS.md`](https://github.com/analoginfo-pim/mix-orm/blob/main/crates/orm-core/ARCHITECTURE_PATTERNS.md).
> This copy lives under `core-assets/docs/external/mix-orm/` so AI
> agents and developers in this workspace can grep / open it without
> pulling the upstream `mix-orm` checkout. It is **not** vendored into
> `pim-orm` itself (per `pim-offline-server/AGENTS.md`: *"we do not
> vendor those files in this repo"*). Refresh from upstream when the
> patterns change; otherwise treat this file as a snapshot — do not
> edit in place.

**Purpose**: This document describes the architectural patterns, conventions, and best practices for building modules using the PIM-ORM framework. This guide is intended for developers and AI agents implementing new ORM modules.

**Last Updated**: 2026-02-17

---

## Table of Contents

0. [Quick Start: Creating a New Module](#quick-start-creating-a-new-module) ⭐ **START HERE**
1. [System Architecture Hierarchy](#system-architecture-hierarchy)
2. [Module Naming Convention](#module-naming-convention)
3. [ID Type Standard](#id-type-standard)
4. [Global Singleton Connection Pattern](#global-singleton-connection-pattern)
5. [CQRS Pattern](#cqrs-pattern)
6. [Handler Instantiation Pattern](#handler-instantiation-pattern)
7. [Schema/Domain Model Pattern](#schemadomain-model-pattern)
8. [Standardized Lookups Pattern](#standardized-lookups-pattern)
9. [Command/Request DTOs Pattern](#commandrequest-dtos-pattern)
10. [Module-Specific Migrations Pattern](#module-specific-migrations-pattern)
11. [Modular Seeds Pattern](#modular-seeds-pattern)
12. [Database Abstraction Traits Pattern](#database-abstraction-traits-pattern)
13. [Error Handling Pattern](#error-handling-pattern)
14. [Re-export Facade Pattern](#re-export-facade-pattern)
15. [Manager/Service Layer Pattern](#managerservice-layer-pattern)
16. [Thin API Layer Pattern](#thin-api-layer-pattern)
17. [Query Extraction at the API Boundary](#query-extraction-at-the-api-boundary)
18. [SQL Best Practices](#sql-best-practices)
19. [Documentation Pattern](#documentation-pattern)
20. [Test Infrastructure Pattern](#test-infrastructure-pattern)
21. [Deprecated Patterns](#deprecated-patterns)

---

## Quick Start: Creating a New Module

**Pattern**: Start with the ORM module first, then optionally add a domain library wrapper and API layer.

### Decision Tree: What Are You Building?

**Option A: Pure ORM Module** (like `pim-orm-hsm`)

- Just database access, no business logic
- Will be consumed by other libraries
- **Start here** if you're unsure

**Option B: ORM + Domain Library** (like `pim-hsm` wrapping `pim-orm-hsm`)

- ORM module + business logic/managers
- Provides a higher-level API
- **Start with Option A first**, then add the wrapper

**Option C: ORM + Library + API** (like `pim-crypto`)

- Complete stack: database + business logic + HTTP endpoints
- **Start with Option A**, then add library and API incrementally

### Bootstrap Process for Option A (Pure ORM Module)

#### Step 1: Create Module Directory

```bash
# Choose your module name (single word preferred)
MODULE_NAME="mymodule"  # e.g., "crypto", "hsm", "vault"
MODULE_ID="008"         # Next available ID from Module Registry

# Create at workspace root (NOT in a crates/ subdirectory!)
cd /path/to/pim-orm-${MODULE_NAME}
mkdir -p src/{commands,queries,schema} migrations
```

**❌ WRONG:**

```bash
mkdir -p crates/pim-orm-mymodule  # Don't nest in crates/!
```

**✅ CORRECT:**

```bash
# ORM module is the project root
cd /path/to/pim-orm-mymodule
```

#### Step 2: Create Cargo.toml

```toml
[package]
name = "pim-orm-mymodule"
version = "0.1.0"
edition = "2021"
description = "PIM-ORM MyModule - [Brief description]"

[lib]
path = "src/lib.rs"

[dependencies]
# Core ORM traits (encapsulates database driver)
# Use registry versions if developing as internal workspace member
pim-orm-core = { registry = "pim-crates", version = "^0.3.5", features = ["sqlx", "uuid"] }
pim-orm-derive = { registry = "pim-crates", version = "^0.3.5" }
# OR use local paths if developing as standalone module
# pim-orm-core = { path = "../pim-orm-core/pim-orm-core", features = ["sqlx", "uuid"] }
# pim-orm-derive = { path = "../pim-orm-core/pim-orm-derive" }

# Standard dependencies
tokio = { version = "1", features = ["full"] }
async-trait = "0.1"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
chrono = { version = "0.4", features = ["serde"] }
thiserror = "2.0"
utoipa = { version = "5.4.0", features = ["chrono"] }  # OpenAPI by design
tracing = "0.1"
uuid = { version = "1", features = ["v4", "serde"] }

# Database (compile-time only for derive macro)
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio-rustls", "macros", "migrate"] }
```

#### Step 3: Create Minimal lib.rs

```rust
//! # PIM-ORM MyModule
//!
//! [Brief description of what this module manages]

pub mod commands;
pub mod error;
pub mod migrations;
pub mod queries;
pub mod schema;

// Re-export commonly used types
pub use error::MyModuleError;
// Add handler and schema exports as you create them
```

#### Step 4: Create First Migration

```sql
-- migrations/008000001_create_mymodule_lookups.sql
-- pim-orm-mymodule module migration

-- Migration: Create MyModule Enum Lookups
-- Version: 001
-- Date: 2025-12-30

CREATE TABLE IF NOT EXISTS mymodule_status_types (
    id INTEGER PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed data
INSERT INTO mymodule_status_types (id, code, label, display_order) VALUES
    (1, 'ACTIVE', 'Active', 1),
    (2, 'INACTIVE', 'Inactive', 2)
ON CONFLICT (id) DO NOTHING;
```

#### Step 5: Verify Structure

Your directory should look like:

```
pim-orm-mymodule/           # ✅ At project root
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── error.rs
│   ├── migrations.rs
│   ├── commands/
│   │   └── mod.rs
│   ├── queries/
│   │   └── mod.rs
│   └── schema/
│       └── mod.rs
└── migrations/
    └── 008000001_create_mymodule_lookups.sql
```

**NOT:**

```
crates/                     # ❌ Don't create this!
└── pim-orm-mymodule/       # ❌ Don't nest!
```

### Bootstrap Process for Option C (ORM + Library + API)

If you want the full stack (like `pim-crypto`), create as a workspace:

```bash
# Create project directory
mkdir pim-mymodule && cd pim-mymodule

# Create workspace structure
mkdir -p src/managers
mkdir -p api/src
mkdir -p pim-orm-mymodule/src/{commands,queries,schema}
mkdir -p pim-orm-mymodule/migrations
```

**Root Cargo.toml:**

```toml
[workspace]
members = [".", "api", "pim-orm-mymodule"]  # ✅ ORM as workspace member
resolver = "2"

[package]
name = "pim-mymodule"
version = "0.1.0"
edition = "2021"

[dependencies]
pim-orm-mymodule = { path = "./pim-orm-mymodule" }  # ✅ Local path
```

**Final structure:**

```
pim-mymodule/               # Workspace root
├── Cargo.toml              # Workspace definition
├── src/                    # Domain library (managers)
│   └── lib.rs
├── pim-orm-mymodule/       # ✅ ORM module as workspace member
│   ├── Cargo.toml
│   └── src/
└── api/                    # Thin API wrapper
    ├── Cargo.toml
    └── src/
```

### Common Mistakes to Avoid

| ❌ Wrong                   | ✅ Correct                    | Why                                  |
| -------------------------- | ----------------------------- | ------------------------------------ |
| `crates/pim-orm-mymodule/` | `pim-orm-mymodule/` (at root) | ORM modules aren't nested            |
| Custom `db/` module        | Use `pim-orm-core`            | Don't reinvent database abstractions |
| Hardcoded enums            | Lookup tables                 | Follow Standardized Lookups Pattern  |
| `TIMESTAMP`                | `TIMESTAMPTZ`                 | Always use timezone-aware timestamps |
| Manual `FromDatabaseRow`   | Derive macro                  | Let the macro generate boilerplate   |

### Connection and Initialization Pattern for Internal Workspace Modules

**Temporary Pattern**: If you're developing an ORM module as an internal workspace member (like `pim-crypto/pim-orm-crypto/`), you need to:

1. **Use `pim-orm` for initialization** (not `pim-orm-core` directly)
2. **Use registry versions** of `pim-orm-core` (not local paths)
3. **Create a `db::global` wrapper** to match the `pim-orm` facade's API

#### Step 1: Use Registry Versions in Cargo.toml

```toml
# In pim-orm-mymodule/Cargo.toml
[dependencies]
# ✅ Use registry versions to match pim-orm's dependencies
pim-orm-core = { registry = "pim-crates", version = "^0.3.5", features = ["sqlx", "uuid", "migrations"] }
pim-orm-derive = { registry = "pim-crates", version = "^0.3.5" }

# ❌ DON'T use local paths - this creates separate global pools!
# pim-orm-core = { path = "../../pim-orm-core/pim-orm-core" }
```

**WHY**: Using registry versions ensures your ORM module shares the same `pim-orm-core` instance as `pim-orm`, which means they share the same global connection pool. Local path dependencies create separate instances and separate pools, causing connection failures.

#### Step 2: Create db::global Wrapper

```rust
// In pim-orm-mymodule/src/lib.rs
pub mod db {
    pub mod global {
        use std::sync::Arc;
        use pim_orm_core::{DatabaseConnection, error::PimOrmError};

        /// Get the global database connection (async).
        pub async fn connection() -> Result<Arc<dyn DatabaseConnection>, PimOrmError> {
            pim_orm_core::global_connection().await
        }
    }
}
```

> **Note**: Older modules may include a `connection_blocking()` wrapper here. That function is **deprecated** — it uses `tokio::task::block_in_place` to synchronously acquire a connection and panics on failure. Do not add it to new modules. Always use the async `connection().await?` form.

#### Step 3: Use pim-orm for Initialization in API

```toml
# In api/Cargo.toml
[dependencies]
pim-mymodule = { path = ".." }
pim-orm = { path = "../../pim-orm" }  # For initialization
pim-orm-mymodule = { path = "../pim-orm-mymodule", features = ["migrations"] }
```

```rust
// In api/src/main.rs
use pim_orm::db::sqlx_impl::SqlxPostgresConnection;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize using pim-orm (not pim-orm-core directly)
    let config = pim_orm::DatabaseConfig::with_defaults();
    let builder = pim_orm::DefaultConnectionBuilder;
    let pool = pim_orm::DatabasePool::new(&config, &builder).await?;

    // Initialize global connection for handlers
    pim_orm::db::init_global_connection(config).await?;

    // Run module migrations
    let sqlx_pool = pool.connection().as_any()
        .downcast_ref::<SqlxPostgresConnection>()
        .ok_or("Failed to downcast")?
        .get_pool();
    pim_orm_mymodule::migrations::run_migrations(sqlx_pool).await?;

    // Start server...
    Ok(())
}
```

#### Step 4: Use in Handlers and Managers

```rust
use pim_orm_mymodule::db::global;

pub async fn my_handler() -> Result<(), MyError> {
    let connection = global::connection().await?;
    let handler = MyQueryHandler::with_connection(connection);
    // ...
}
```

**WHY**:

- `pim-orm` provides the initialization infrastructure and ensures proper connection pooling
- Registry versions of `pim-orm-core` ensure all components share the same global pool
- The `db::global` wrapper matches the `pim-orm` facade's API (`connection()` vs `global_connection()`)
- Once extracted to a separate repo and consumed through `pim-orm`, these wrappers can be removed

### Next Steps

Once your basic structure is in place:

1. **Read [CQRS Pattern](#cqrs-pattern)** - Understand command/query separation
2. **Read [Schema/Domain Model Pattern](#schemadomain-model-pattern)** - Create your entities
3. **Read [Standardized Lookups Pattern](#standardized-lookups-pattern)** - Define your enums
4. **Read [Handler Instantiation Pattern](#handler-instantiation-pattern)** - Implement handlers
5. **See [Example: Creating pim-orm-hsm](#example-creating-pim-orm-hsm)** - Complete reference

**WHY**: Starting with the correct structure prevents costly refactoring later. The ORM module is the foundation - build it right first, then add layers on top.

---

## System Architecture Hierarchy

**Pattern**: The PIM system is organized in layers, with ORM modules at the foundation and API/UI layers on top.

### Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                         UI Layer                             │
│  pim-ui (React) - Consumes APIs, caches lookups             │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  pim-server, pim-api, pim-events-api, pim-jobs-api, etc.   │
│  (Axum REST APIs with OpenAPI)                              │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Library/Service Layer                      │
│  pim-events, pim-jobs, pim-hsm, etc.                        │
│  (Business logic, managers, domain services)                │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                      ORM Layer                               │
│  pim-orm (facade)                                           │
│  ├── pim-orm-core (traits, utilities)                      │
│  ├── pim-orm-jobs (001)                                    │
│  ├── pim-orm-events (002)                                  │
│  ├── pim-orm-offline (003)                                 │
│  ├── pim-orm-messaging (004)                               │
│  ├── pim-orm-vault (005)                                   │
│  ├── pim-orm-hsm (006)                                     │
│  └── pim-orm-crypto (007)                                  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                           │
│  PostgreSQL (primary), MySQL, MS SQL Server                 │
└─────────────────────────────────────────────────────────────┘
```

### Module Registry

| Module ID | Module Name | Crate Name        | Purpose                            |
| --------- | ----------- | ----------------- | ---------------------------------- |
| `001`     | jobs        | pim-orm-jobs      | Job scheduling and execution       |
| `002`     | events      | pim-orm-events    | Event distribution and alerting    |
| `003`     | offline     | pim-orm-offline   | Offline endpoint management        |
| `004`     | messaging   | pim-orm-messaging | Message queue and notifications    |
| `005`     | vault       | pim-orm-vault     | Secret storage and management      |
| `006`     | hsm         | pim-orm-hsm       | HSM configuration management       |
| `007`     | crypto      | pim-orm-crypto    | Encryption operations and key mgmt |

**WHY**: This hierarchy ensures clear separation of concerns. ORM modules are pure data access, libraries add business logic, APIs expose HTTP endpoints, and UI consumes APIs. Each layer can be developed, tested, and deployed independently.

---

## Module Naming Convention

**Pattern**: Use a short, single-word tag/name for your module. This name is used consistently across all artifacts.

### Naming Rules

1. **Choose a single word** (strongly preferred) or hyphenated compound if absolutely necessary
2. **Use the tag consistently** in:
   - Crate name: `pim-orm-{tag}`
   - Migration prefix: `{module_id}` (see [Module-Specific Migrations](#module-specific-migrations-pattern))
   - Table prefixes: `{tag}_*` (e.g., `events_destinations`, `hsm_connections`)
   - Feature flag: `{tag}` in `pim-orm` Cargo.toml

### Examples

| Module                      | Tag         | Crate Name          | Migration ID | Table Prefix Examples                    |
| --------------------------- | ----------- | ------------------- | ------------ | ---------------------------------------- |
| Job Scheduling              | `jobs`      | `pim-orm-jobs`      | `001`        | `tbl_BaseJobInfo`, `tbl_ScheduleJobInfo` |
| Event Distribution          | `events`    | `pim-orm-events`    | `002`        | `events_destinations`, `events_alerts`   |
| Offline Endpoint Management | `offline`   | `pim-orm-offline`   | `003`        | `offline_endpoints`, `offline_groups`    |
| Message Queue               | `messaging` | `pim-orm-messaging` | `004`        | `messaging_queues`, `messaging_topics`   |
| Secret Storage              | `vault`     | `pim-orm-vault`     | `005`        | `vault_secrets`, `vault_policies`        |
| HSM Configuration           | `hsm`       | `pim-orm-hsm`       | `006`        | `hsm_connections`, `hsm_vendors`         |

**WHY**: Single-word tags are easier to remember, type, and use consistently. The tag becomes a recognizable identifier that connects migrations, tables, handlers, and API endpoints across the entire system.

**IMPORTANT**: Table prefixes follow the pattern `{tag}_` plus a descriptive name. For example, the `events` module uses `events_destinations`, `events_alerts`, `events_templates`, etc. This makes it immediately clear which module owns each table.

**Example**: For HSM configuration management, use `hsm` (not `hsm-config` or `hsm_configuration`):

- Crate: `pim-orm-hsm`
- Tables: `hsm_connections`, `hsm_vendors`, `hsm_keys`, `hsm_key_operations`
- Feature: `features = ["hsm"]`
- Migration prefix: `006`

---

## ID Type Standard

**Pattern**: Use `i32` or `i64` (signed integers) for primary keys across all modules for maximum database compatibility.

### Standard

```rust
#[derive(Debug, Clone, FromDatabaseRow)]
#[from_database_row(database = "postgres")]
pub struct MyEntity {
    pub id: i32,  // ✅ STANDARD: Use i32 for most tables
    pub name: String,
    // ... other fields
}

#[derive(Debug, Clone, FromDatabaseRow)]
#[from_database_row(database = "postgres")]
pub struct LargeVolumeEntity {
    pub id: i64,  // ✅ ACCEPTABLE: Use i64 for expected large tables
    pub data: String,
    // ... other fields
}
```

### Choosing Between i32 and i64

**Use `i32` (default choice):**

- Most tables (< 2 billion rows expected)
- Lookup/enum tables
- Configuration tables
- Reference data

**Use `i64` for:**

- **High-volume transactional tables** (audit logs, events, messages)
- **Time-series data** (metrics, telemetry)
- **Historical records** (job executions, password rotations)
- Any table expected to exceed 2 billion rows

### Why Signed Integers?

- **Cross-database compatibility**: Works consistently across PostgreSQL, MySQL, MS SQL Server, and Oracle
- **Performance**: Smaller index size than UUID (i32: 4 bytes, i64: 8 bytes, UUID: 16 bytes)
- **Simplicity**: Auto-increment integers are universally supported
- **Proven**: All existing modules (`pim-orm-jobs`, `pim-orm-events`) use `i32`/`i64`

### Legacy UUID Migration

**Note**: `pim-orm-offline` currently uses UUIDs for historical reasons (offline registration without coordination). These are **slated for migration to `i32`** in the next phase. Do not use UUIDs for new modules unless you have a specific distributed coordination requirement.

### Foreign Keys

Foreign keys should match the type of the referenced primary key:

```rust
pub struct MyEntity {
    pub id: i32,
    pub parent_id: Option<i32>,  // ✅ Foreign key matches parent's i32 type
    pub vendor_id: i32,           // ✅ Required foreign key
}

pub struct AuditLog {
    pub id: i64,                  // ✅ Large table uses i64
    pub entity_id: i32,           // ✅ FK to smaller table uses i32
    pub user_id: i32,
}
```

---

## Global Singleton Connection Pattern

**Pattern**: PIM-ORM uses a global singleton database connection pool that must be initialized once at application startup.

### Initialization (Application Startup)

```rust
use pim_orm::DatabaseConfig;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize the global connection pool once
    let config = DatabaseConfig::with_defaults();
    pim_orm::db::global::init(config).await?;

    // ... start your application
    Ok(())
}
```

### Accessing the Connection

```rust
let connection = pim_orm::db::global::connection().await?;
```

> **Deprecated**: `connection_blocking()` exists in older code but is deprecated. It blocks the async runtime and panics on failure. Always use the async form above.

### Checking Initialization Status

```rust
if pim_orm::db::global::is_initialized() {
    // Pool is ready
}
```

### Test Initialization Pattern

For tests, use `Once::call_once` to initialize the pool exactly once:

```rust
use std::sync::Once;

static INIT: Once = Once::new();

async fn setup_test_db() -> Result<(), Box<dyn std::error::Error>> {
    if pim_orm::db::global::is_initialized() {
        return Ok(());
    }

    INIT.call_once(|| {
        // Initialize in a dedicated thread with its own runtime
        // This keeps the pool alive for all tests
        std::thread::spawn(move || {
            let runtime = tokio::runtime::Runtime::new().unwrap();
            runtime.block_on(async {
                let config = DatabaseConfig::with_defaults();
                pim_orm::db::global::init(config).await.unwrap();
            });
            loop {
                std::thread::sleep(std::time::Duration::from_secs(3600));
            }
        });
    });

    Ok(())
}
```

**WHY**: A global singleton pool avoids connection overhead and ensures consistent connection management across the entire application. Handlers are lightweight and ephemeral, but the connection pool is long-lived.

---

## CQRS Pattern

**Pattern**: Strict separation between write operations (commands) and read operations (queries).

### Structure

```
src/
├── commands/
│   ├── mod.rs
│   └── entity_commands.rs    # Write operations
├── queries/
│   ├── mod.rs
│   └── entity_queries.rs     # Read operations
└── schema/
    ├── mod.rs
    └── entities.rs            # Domain models
```

### Command Handler (Writes)

```rust
use pim_orm_core::{DatabaseConnection, PimOrmError};
use std::sync::Arc;

pub struct EntityCommandHandler {
    connection: Arc<dyn DatabaseConnection>,
}

impl EntityCommandHandler {
    pub fn with_connection(connection: Arc<dyn DatabaseConnection>) -> Self {
        Self { connection }
    }

    pub async fn create_entity(&self, cmd: CreateEntityCommand) -> Result<i32, PimOrmError> {
        let query = "INSERT INTO entities (name, value) VALUES ($1, $2) RETURNING id";
        let row = self.connection
            .query_one(query, &[&cmd.name, &cmd.value])
            .await?;
        let id: i32 = row.get("id")?;
        Ok(id)
    }

    pub async fn update_entity(&self, cmd: UpdateEntityCommand) -> Result<(), PimOrmError> {
        let query = "UPDATE entities SET name = $1 WHERE id = $2";
        self.connection
            .execute(query, &[&cmd.name, &cmd.id])
            .await?;
        Ok(())
    }

    pub async fn delete_entity(&self, id: i32) -> Result<(), PimOrmError> {
        let query = "DELETE FROM entities WHERE id = $1";
        self.connection.execute(query, &[&id]).await?;
        Ok(())
    }
}
```

### Query Handler (Reads)

```rust
pub struct EntityQueryHandler {
    connection: Arc<dyn DatabaseConnection>,
}

impl EntityQueryHandler {
    pub fn with_connection(connection: Arc<dyn DatabaseConnection>) -> Self {
        Self { connection }
    }

    pub async fn get_entity(&self, id: i32) -> Result<Option<Entity>, PimOrmError> {
        let query = "SELECT * FROM entities WHERE id = $1";
        pim_orm_core::query_as_optional_dyn::<Entity>(
            self.connection.as_ref(),
            query,
            &[&id],
        ).await
    }

    pub async fn list_entities(&self) -> Result<Vec<Entity>, PimOrmError> {
        let query = "SELECT * FROM entities ORDER BY name";
        pim_orm_core::query_as_dyn::<Entity>(
            self.connection.as_ref(),
            query,
            &[],
        ).await
    }
}
```

**WHY**: CQRS separates concerns cleanly. Queries never modify data, and commands focus solely on writes. This makes code easier to reason about, test, and optimize independently.

---

## Handler Instantiation Pattern

**Pattern**: Handlers are lightweight, instantiated per-request/operation, and do NOT live in application state.

### ✅ Correct: Create Handlers Per-Request

```rust
// In an Axum handler
pub async fn list_entities(
    State(_state): State<AppState>,  // State does NOT hold handlers
) -> Result<Json<Vec<Entity>>> {
    // Acquire connection, then create handler on-demand
    let connection = pim_orm::db::global::connection().await?;
    let query = EntityQueryHandler::with_connection(connection);
    let entities = query.list_entities().await?;
    Ok(Json(entities))
}

pub async fn create_entity(
    State(_state): State<AppState>,
    Json(req): Json<CreateEntityRequest>,
) -> Result<Json<i32>> {
    let connection = pim_orm::db::global::connection().await?;
    let cmd = EntityCommandHandler::with_connection(connection);
    let id = cmd.create_entity(req.into()).await?;
    Ok(Json(id))
}
```

### ❌ Incorrect: Storing Handlers in State

```rust
// DON'T DO THIS
pub struct AppState {
    query_handler: EntityQueryHandler,  // ❌ Handlers don't belong in state
    cmd_handler: EntityCommandHandler,  // ❌ Handlers don't belong in state
}
```

### Why Not Store Handlers?

- Handlers are cheap to create (they just hold an `Arc<dyn DatabaseConnection>`)
- The connection pool is the expensive resource, and it's already a global singleton
- Creating handlers per-request keeps code simple and avoids lifetime issues

**WHY**: Handlers are thin wrappers around database operations. The connection pool (global singleton) is the shared resource. Instantiating handlers per-request keeps the architecture simple and avoids unnecessary state management.

---

## Schema/Domain Model Pattern

**Pattern**: Domain structs decorated with derive macros for automatic database row conversion.

### Basic Schema

```rust
use pim_orm_derive::FromDatabaseRow;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, FromDatabaseRow, Serialize, Deserialize)]
#[from_database_row(database = "postgres")]
pub struct Entity {
    pub id: i32,
    pub name: String,
    pub description: Option<String>,
    pub status: i32,  // Enum stored as i32
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
```

### Enum Handling

**IMPORTANT**: Enums should be stored as `i32` values that reference standardized lookup tables. See the [Standardized Lookups Pattern](#standardized-lookups-pattern) section for the complete, modern approach.

**Legacy Pattern (Avoid for New Code):**

In older code, you may see enums hardcoded in Rust with conversion methods:

```rust
// ⚠️ LEGACY: Hardcoded enum (avoid for new modules)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(i32)]
pub enum EntityStatus {
    Active = 1,
    Inactive = 2,
    Archived = 3,
}

impl EntityStatus {
    pub fn from_i32(value: i32) -> Option<Self> {
        match value {
            1 => Some(Self::Active),
            2 => Some(Self::Inactive),
            3 => Some(Self::Archived),
            _ => None,
        }
    }
}
```

**Modern Pattern (Use This):**

Store enum values as `i32` in your entity, but define the enum values in a lookup table:

```rust
// ✅ MODERN: Entity references lookup table
#[derive(Debug, Clone, FromDatabaseRow, Serialize, Deserialize, utoipa::ToSchema)]
#[from_database_row(database = "postgres")]
pub struct Entity {
    pub id: i32,
    pub name: String,
    pub status: i32,  // References entity_status_types lookup table
    pub created_at: DateTime<Utc>,
}
```

```sql
-- Lookup table defines the enum values
CREATE TABLE IF NOT EXISTS entity_status_types (
    id INTEGER PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0
);

INSERT INTO entity_status_types (id, code, label, display_order) VALUES
    (1, 'ACTIVE', 'Active', 1),
    (2, 'INACTIVE', 'Inactive', 2),
    (3, 'ARCHIVED', 'Archived', 3)
ON CONFLICT (id) DO NOTHING;
```

**WHY**: Lookup tables provide flexibility (add new values without code changes), consistency (same pattern everywhere), and UI integration (dynamic dropdowns). See [Standardized Lookups Pattern](#standardized-lookups-pattern) for complete details.

### OpenAPI Support (Required)

```rust
#[derive(Debug, Clone, FromDatabaseRow, Serialize, Deserialize, utoipa::ToSchema)]
#[from_database_row(database = "postgres")]
pub struct Entity {
    pub id: i32,
    pub name: String,
    pub created_at: DateTime<Utc>,  // Always use DateTime<Utc> for timestamps
}
```

**IMPORTANT**: OpenAPI support should be included by design, not as an optional feature. All schema types should derive `utoipa::ToSchema` to ensure API documentation is always available.

### Timestamp Handling

**Always use `TIMESTAMPTZ` in PostgreSQL and `DateTime<Utc>` in Rust:**

```rust
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, FromDatabaseRow)]
#[from_database_row(database = "postgres")]
pub struct Entity {
    pub created_at: DateTime<Utc>,   // ✅ TIMESTAMPTZ from database
    pub updated_at: DateTime<Utc>,   // ✅ TIMESTAMPTZ from database
    pub deleted_at: Option<DateTime<Utc>>,  // ✅ Optional for soft deletes
}
```

```sql
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- ✅ Use TIMESTAMPTZ
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- ✅ Use TIMESTAMPTZ
    deleted_at TIMESTAMPTZ                          -- ✅ Optional
);
```

**WHY**:

- `TIMESTAMPTZ` stores timestamps in UTC and converts to the client's timezone automatically
- `DateTime<Utc>` ensures all timestamps are timezone-aware in Rust
- This prevents timezone-related bugs and makes audit trails reliable
- The `FromDatabaseRow` derive macro eliminates boilerplate row-to-struct conversion code
- Storing enums as `i32` provides database compatibility while maintaining type safety in Rust

---

## Standardized Lookups Pattern

**Pattern**: Enum values are stored in standardized lookup tables with a consistent schema, seeded in migrations, and consumed by the UI for dynamic dropdowns. This is the modern, preferred approach for handling enums in PIM-ORM.

**Purpose**: Lookups standardize what were previously hardcoded enums. Instead of defining enum values in Rust code, we define them in database tables with rich metadata (labels, descriptions, display order). This makes the system more flexible and data-driven.

### Lookup Table Schema

All lookup tables follow this standard pattern:

```sql
CREATE TABLE IF NOT EXISTS {module}_{enum_name}_types (
    id INTEGER PRIMARY KEY,                    -- Enum value (1, 2, 3, ...)
    code VARCHAR(50) NOT NULL UNIQUE,          -- Machine-readable code (UPPERCASE_SNAKE)
    label VARCHAR(100) NOT NULL,               -- Human-readable label for UI
    description TEXT,                          -- Optional detailed description
    is_active BOOLEAN NOT NULL DEFAULT TRUE,   -- Soft delete flag
    display_order INTEGER NOT NULL DEFAULT 0,  -- Sort order for UI dropdowns
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_{module}_{enum_name}_types_active
    ON {module}_{enum_name}_types(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_{module}_{enum_name}_types_code
    ON {module}_{enum_name}_types(code);
```

### Seeding Lookup Data in Migrations

Lookup data is included in migrations using idempotent `INSERT ... ON CONFLICT DO NOTHING`:

```sql
-- Seed email provider types
INSERT INTO events_email_provider_types (id, code, label, description, display_order) VALUES
    (1, 'SMTP', 'SMTP', 'Traditional SMTP server', 1),
    (2, 'MICROSOFT_GRAPH', 'Microsoft Graph', 'Microsoft Graph API (Office 365/Exchange Online)', 2),
    (3, 'AWS_SES', 'AWS SES', 'Amazon Simple Email Service', 3),
    (4, 'SENDGRID', 'SendGrid', 'SendGrid API', 4),
    (5, 'MAILGUN', 'Mailgun', 'Mailgun API', 5)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE events_email_provider_types IS 'Email provider type enumeration';
COMMENT ON COLUMN events_email_provider_types.code IS 'Machine-readable code (e.g., SMTP, MICROSOFT_GRAPH)';
COMMENT ON COLUMN events_email_provider_types.label IS 'Human-readable label for UI display';
COMMENT ON COLUMN events_email_provider_types.is_active IS 'Soft delete flag - only active entries shown in UI';
COMMENT ON COLUMN events_email_provider_types.display_order IS 'Sort order for UI dropdowns (lower = first)';
```

### Rust Schema for Lookups

```rust
use pim_orm_derive::FromDatabaseRow;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, FromDatabaseRow, Serialize, Deserialize, utoipa::ToSchema)]
#[from_database_row(database = "postgres")]
pub struct EmailProviderType {
    pub id: i32,
    pub code: String,
    pub label: String,
    pub description: Option<String>,
    pub is_active: bool,
    pub display_order: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
```

### Query Handler for Lookups

```rust
pub struct LookupQueryHandler {
    connection: Arc<dyn DatabaseConnection>,
}

impl LookupQueryHandler {
    pub fn with_connection(connection: Arc<dyn DatabaseConnection>) -> Self {
        Self { connection }
    }

    /// Get all active email provider types for UI dropdowns
    pub async fn list_email_provider_types(&self) -> Result<Vec<EmailProviderType>, PimOrmError> {
        let query = r#"
            SELECT * FROM events_email_provider_types
            WHERE is_active = TRUE
            ORDER BY display_order, label
        "#;
        pim_orm_core::query_as_dyn(self.connection.as_ref(), query, &[]).await
    }

    /// Get a specific email provider type by ID
    pub async fn get_email_provider_type(&self, id: i32) -> Result<Option<EmailProviderType>, PimOrmError> {
        let query = "SELECT * FROM events_email_provider_types WHERE id = $1";
        pim_orm_core::query_as_optional_dyn(self.connection.as_ref(), query, &[&id]).await
    }

    /// Get email provider type by code
    pub async fn get_email_provider_type_by_code(&self, code: &str) -> Result<Option<EmailProviderType>, PimOrmError> {
        let query = "SELECT * FROM events_email_provider_types WHERE code = $1 AND is_active = TRUE";
        pim_orm_core::query_as_optional_dyn(self.connection.as_ref(), query, &[&code]).await
    }
}
```

### API Endpoint for Lookups

```rust
// In API layer
#[utoipa::path(
    get,
    path = "/api/lookups/email-provider-types",
    tag = "lookups",
    responses(
        (status = 200, description = "Email provider types", body = Vec<EmailProviderType>)
    )
)]
pub async fn list_email_provider_types() -> Result<Json<Vec<EmailProviderType>>> {
    let connection = pim_orm::db::global::connection().await?;
    let handler = LookupQueryHandler::with_connection(connection);
    let types = handler.list_email_provider_types().await?;
    Ok(Json(types))
}
```

### UI Integration (pim-ui)

The UI fetches lookups once and caches them, avoiding hardcoded values:

```typescript
// In pim-ui/src/services/lookups.ts
export interface LookupValue {
  id: number;
  code: string;
  label: string;
  description?: string;
  displayOrder: number;
}

class LookupCache {
  private cache: Map<string, LookupValue[]> = new Map();

  async getEmailProviderTypes(): Promise<LookupValue[]> {
    if (!this.cache.has("emailProviderTypes")) {
      const response = await axios.get("/api/lookups/email-provider-types");
      this.cache.set("emailProviderTypes", response.data);
    }
    return this.cache.get("emailProviderTypes")!;
  }

  // ... other lookup methods
}

export const lookupCache = new LookupCache();
```

```tsx
// In a React component
import { lookupCache } from "@/services/lookups";

export function EmailConfigForm() {
  const [providerTypes, setProviderTypes] = useState<LookupValue[]>([]);

  useEffect(() => {
    lookupCache.getEmailProviderTypes().then(setProviderTypes);
  }, []);

  return (
    <Select>
      {providerTypes.map((type) => (
        <SelectItem key={type.id} value={type.id.toString()}>
          {type.label}
        </SelectItem>
      ))}
    </Select>
  );
}
```

### Benefits of Standardized Lookups

1. **No Hardcoding**: UI never hardcodes enum values
2. **Dynamic**: New enum values can be added via migrations without code changes
3. **Consistent**: All lookups follow the same schema and API pattern
4. **Cacheable**: UI caches lookups for performance
5. **Documented**: OpenAPI automatically documents all lookup endpoints
6. **Soft Deletes**: `is_active` flag allows deprecating values without breaking existing data
7. **Ordered**: `display_order` controls UI presentation
8. **Searchable**: `code` and `label` support different use cases (API vs. UI)

**WHY**: Standardized lookups eliminate magic numbers and hardcoded strings throughout the system. The UI becomes data-driven, and new enum values can be added without deploying new code. This pattern is used extensively in `pim-orm-events` and `pim-orm-offline`.

### Lookups vs. Legacy Enums

| Aspect         | Legacy Hardcoded Enums            | Modern Lookup Tables                       |
| -------------- | --------------------------------- | ------------------------------------------ |
| Definition     | Rust code (`enum` type)           | Database table                             |
| Adding values  | Requires code change & deployment | Migration only                             |
| UI integration | Hardcoded in frontend             | Dynamic via API                            |
| Metadata       | None (just value)                 | Label, description, display order          |
| Soft delete    | Not possible                      | `is_active` flag                           |
| Ordering       | Fixed in code                     | `display_order` column                     |
| Documentation  | Code comments only                | Database `COMMENT ON` + description column |
| Recommended    | ❌ Avoid for new code             | ✅ Use for all new modules                 |

**Migration Path**: Existing modules with hardcoded enums should gradually migrate to lookup tables. New modules must use lookup tables from the start.

### Example: Complete Lookup Implementation

See `pim-orm-events/migrations/002000001_create_event_enum_lookups.sql` for a comprehensive example with multiple lookup tables (email providers, SIEM platforms, ITSM platforms, etc.).

---

## Command/Request DTOs Pattern

**Pattern**: Separate structs for commands/requests vs. domain models.

### Create Command

```rust
#[derive(Debug, Clone)]
pub struct CreateEntityCommand {
    pub name: String,
    pub description: Option<String>,
    pub status: i32,
}
```

### Update Command (Partial Updates)

```rust
#[derive(Debug, Clone)]
pub struct UpdateEntityCommand {
    pub id: i32,
    pub name: Option<String>,        // ✅ Optional for partial updates
    pub description: Option<String>,
    pub status: Option<i32>,
}
```

### API Request DTOs

The API layer defines its own request DTOs and maps them to ORM commands:

```rust
// In API layer
#[derive(Debug, Deserialize)]
pub struct CreateEntityRequest {
    pub name: String,
    pub description: Option<String>,
    pub status: String,  // API uses string, ORM uses i32
}

// In API handler
pub async fn create_entity(
    Json(req): Json<CreateEntityRequest>,
) -> Result<Json<i32>> {
    // Map API DTO to ORM command
    let status = match req.status.as_str() {
        "active" => 1,
        "inactive" => 2,
        _ => return Err(ApiError::BadRequest("Invalid status".into())),
    };

    let cmd = CreateEntityCommand {
        name: req.name,
        description: req.description,
        status,
    };

    let connection = pim_orm::db::global::connection().await?;
    let handler = EntityCommandHandler::with_connection(connection);
    let id = handler.create_entity(cmd).await?;
    Ok(Json(id))
}
```

**WHY**: Separating DTOs from domain models allows the API layer to have different validation, naming, and structure than the database layer. Update commands use `Option<T>` to distinguish between "don't update" (None) and "set to null" (Some(None)).

---

## Module-Specific Migrations Pattern

**Pattern**: Each ORM module has its own migration directory with a unique ID prefix.

### Migration Naming Convention

```
migrations/{module_id}{migration_number}_{description}.sql
```

- **module_id**: 3-digit prefix unique to your module (e.g., `003` for offline, `004` for hsm)
- **migration_number**: 6-digit sequential number (e.g., `000001`, `000002`)
- **description**: Snake_case description of the migration

### Examples

| Module            | Module ID | Migration File                                 |
| ----------------- | --------- | ---------------------------------------------- |
| pim-orm-jobs      | `001`     | `001000001_create_base_jobs.sql`               |
| pim-orm-events    | `002`     | `002000001_create_event_enum_lookups.sql`      |
| pim-orm-offline   | `003`     | `003000001_create_offline_global_settings.sql` |
| pim-orm-messaging | `004`     | `004000001_create_messaging_queues.sql`        |
| pim-orm-vault     | `005`     | `005000001_create_vault_secrets.sql`           |
| pim-orm-hsm       | `006`     | `006000001_create_hsm_vendors.sql`             |

### Migration Structure

```
pim-orm-{tag}/
├── migrations/
│   ├── {module_id}000001_{description}.sql
│   ├── {module_id}000002_{description}.sql
│   └── {module_id}000003_{description}.sql
└── src/
    └── migrations.rs
```

### Migration File Template

```sql
-- pim-orm-{tag} module migration
-- Part of {module description}

-- Migration: {Title}
-- Description: {Detailed description}
-- Version: {migration_number}
-- Date: {YYYY-MM-DD}

-- ============================================================================
-- IDEMPOTENT OPERATIONS
-- ============================================================================

-- Use CREATE TABLE IF NOT EXISTS for idempotency
CREATE TABLE IF NOT EXISTS {tag}_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Use CREATE INDEX IF NOT EXISTS
CREATE INDEX IF NOT EXISTS idx_{tag}_entities_name
    ON {tag}_entities(name);

-- Use INSERT ... ON CONFLICT DO NOTHING for seed data
INSERT INTO {tag}_lookup_values (id, code, label)
VALUES
    (1, 'ACTIVE', 'Active'),
    (2, 'INACTIVE', 'Inactive')
ON CONFLICT (id) DO NOTHING;

-- Use DROP ... IF EXISTS for cleanup
DROP TRIGGER IF EXISTS trigger_{tag}_entities_updated_at ON {tag}_entities;

-- Comments for documentation
COMMENT ON TABLE {tag}_entities IS 'Description of the table';
COMMENT ON COLUMN {tag}_entities.name IS 'Description of the column';
```

### Idempotency Requirements

**CRITICAL**: All migrations MUST be idempotent (safe to run multiple times).

#### ✅ Idempotent Patterns

```sql
-- Tables
CREATE TABLE IF NOT EXISTS my_table (...);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_my_index ON my_table(column);

-- Triggers (drop first, then create)
DROP TRIGGER IF EXISTS my_trigger ON my_table;
CREATE TRIGGER my_trigger ...;

-- Functions (use CREATE OR REPLACE)
CREATE OR REPLACE FUNCTION my_function() ...;

-- Seed data
INSERT INTO lookup_table (id, code, label)
VALUES (1, 'CODE', 'Label')
ON CONFLICT (id) DO NOTHING;

-- Alter table (check existence first)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'my_table' AND column_name = 'new_column'
    ) THEN
        ALTER TABLE my_table ADD COLUMN new_column TEXT;
    END IF;
END $$;
```

#### ❌ Non-Idempotent (Avoid)

```sql
-- ❌ Will fail on second run
CREATE TABLE my_table (...);

-- ❌ Will fail if index exists
CREATE INDEX idx_my_index ON my_table(column);

-- ❌ Will fail if data exists
INSERT INTO lookup_table VALUES (1, 'CODE', 'Label');

-- ❌ Will fail if column exists
ALTER TABLE my_table ADD COLUMN new_column TEXT;
```

**WHY**: Idempotent migrations allow:

- Re-running migrations after failures
- Testing migrations in development
- Deploying to environments with partial migration history
- Recovering from interrupted deployments

### Running Module Migrations

#### For Standalone Modules

```rust
use pim_orm_core::migrations::{run_module_migrations, MigrationConfig};

pub async fn run_migrations(pool: &sqlx::PgPool) -> Result<(), sqlx::migrate::MigrateError> {
    let migrator = sqlx::migrate!("./migrations");
    let config = MigrationConfig::module("mymodule", 008);
    run_module_migrations(pool, &migrator, &config).await?;
    Ok(())
}
```

#### For Internal Workspace Modules (with pim-orm)

When developing an ORM module as part of a larger workspace (like `pim-crypto/pim-orm-crypto`):

```rust
// In api/src/main.rs
use pim_orm::db::sqlx_impl::SqlxPostgresConnection;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create pool for migrations
    let config = pim_orm::DatabaseConfig::with_defaults();
    let builder = pim_orm::DefaultConnectionBuilder;
    let pool = pim_orm::DatabasePool::new(&config, &builder).await?;

    // Initialize global connection
    pim_orm::db::init_global_connection(config).await?;

    // Extract sqlx pool and run migrations
    let sqlx_pool = pool.connection().as_any()
        .downcast_ref::<SqlxPostgresConnection>()
        .ok_or("Failed to downcast")?
        .get_pool();

    pim_orm_mymodule::migrations::run_migrations(sqlx_pool).await?;

    Ok(())
}
```

**WHY**:

- Standalone modules can initialize directly with `pim-orm-core`
- Internal workspace modules must use `pim-orm` to ensure shared connection pools
- The sqlx pool is extracted from the `DatabasePool` for migration execution

---

## Database Abstraction Traits Pattern

**Pattern**: Traits abstract database operations for driver flexibility.

### Core Traits (from pim-orm-core)

```rust
use async_trait::async_trait;

#[async_trait]
pub trait DatabaseConnection: Send + Sync {
    async fn query(&self, query: &str, params: &[&(dyn ToSql + Sync)])
        -> Result<Vec<Box<dyn DatabaseRow>>, PimOrmError>;

    async fn query_one(&self, query: &str, params: &[&(dyn ToSql + Sync)])
        -> Result<Box<dyn DatabaseRow>, PimOrmError>;

    async fn query_opt(&self, query: &str, params: &[&(dyn ToSql + Sync)])
        -> Result<Option<Box<dyn DatabaseRow>>, PimOrmError>;

    async fn execute(&self, query: &str, params: &[&(dyn ToSql + Sync)])
        -> Result<u64, PimOrmError>;

    async fn transaction(&self) -> Result<Box<dyn DatabaseTransaction>, PimOrmError>;
}

pub trait DatabaseRow: Send + Sync {
    fn get<T: FromSql>(&self, name: &str) -> Result<T, PimOrmError>;
    fn try_get<T: FromSql>(&self, name: &str) -> Result<Option<T>, PimOrmError>;
}

#[async_trait]
pub trait DatabaseTransaction: Send + Sync {
    async fn commit(self: Box<Self>) -> Result<(), PimOrmError>;
    async fn rollback(self: Box<Self>) -> Result<(), PimOrmError>;
}

pub trait ToSql: Send + Sync {
    fn to_sql(&self) -> Result<SqlValue, PimOrmError>;
}

pub trait FromDatabaseRow: Sized {
    fn from_row(row: &dyn DatabaseRow) -> Result<Self, PimOrmError>;
}
```

### Generic Query Helpers

```rust
use pim_orm_core::{query_as_dyn, query_as_one_dyn, query_as_optional_dyn};

// Query multiple rows
let entities: Vec<Entity> = query_as_dyn(
    connection.as_ref(),
    "SELECT * FROM entities",
    &[],
).await?;

// Query exactly one row
let entity: Entity = query_as_one_dyn(
    connection.as_ref(),
    "SELECT * FROM entities WHERE id = $1",
    &[&id],
).await?;

// Query optional row
let entity: Option<Entity> = query_as_optional_dyn(
    connection.as_ref(),
    "SELECT * FROM entities WHERE id = $1",
    &[&id],
).await?;
```

**WHY**: Abstracting database operations through traits allows swapping database drivers (e.g., from `sqlx` to `tokio-postgres`) without changing handler code. The generic query helpers eliminate repetitive row conversion code.

---

## Error Handling Pattern

**Pattern**: Unified error type with conversion from database errors.

### Standard Error Type

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum MyModuleError {
    #[error("Entity not found: {0}")]
    NotFound(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Database error: {0}")]
    Database(#[from] PimOrmError),

    #[error("Internal error: {0}")]
    Internal(String),
}

// Automatic conversion from PimOrmError
impl From<PimOrmError> for MyModuleError {
    fn from(err: PimOrmError) -> Self {
        Self::Database(err)
    }
}
```

### Usage in Handlers

```rust
pub async fn get_entity(&self, id: i32) -> Result<Entity, MyModuleError> {
    let entity = query_as_optional_dyn::<Entity>(
        self.connection.as_ref(),
        "SELECT * FROM entities WHERE id = $1",
        &[&id],
    ).await?  // PimOrmError automatically converts to MyModuleError
    .ok_or_else(|| MyModuleError::NotFound(format!("Entity {}", id)))?;

    Ok(entity)
}
```

### API Layer Error Conversion

```rust
// In API layer
#[derive(Debug)]
pub enum ApiError {
    NotFound(String),
    BadRequest(String),
    Internal(String),
}

impl From<MyModuleError> for ApiError {
    fn from(err: MyModuleError) -> Self {
        match err {
            MyModuleError::NotFound(msg) => ApiError::NotFound(msg),
            MyModuleError::Validation(msg) => ApiError::BadRequest(msg),
            _ => ApiError::Internal(err.to_string()),
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            ApiError::NotFound(msg) => (StatusCode::NOT_FOUND, msg),
            ApiError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg),
            ApiError::Internal(msg) => (StatusCode::INTERNAL_SERVER_ERROR, msg),
        };
        (status, Json(json!({"error": message}))).into_response()
    }
}
```

**WHY**: A unified error type with automatic conversions reduces boilerplate and makes error handling consistent across the module. The `#[from]` attribute in `thiserror` provides automatic conversion with the `?` operator.

---

## Re-export Facade Pattern

**Pattern**: Main `pim-orm` crate re-exports types from sub-crates for convenience.

### In pim-orm/lib.rs

```rust
// Re-export core types
pub use pim_orm_core::{
    DatabaseConnection, DatabaseRow, PimOrmError,
    query_as_dyn, query_as_one_dyn, query_as_optional_dyn,
};

// Re-export module types (with feature flags)
#[cfg(feature = "hsm")]
pub use pim_orm_hsm::{
    // Schema types
    HsmConnection, HsmVendor, HsmKey,
    // Command types
    CreateHsmConnectionCommand, UpdateHsmConnectionCommand,
    // Handler types
    HsmConnectionCommandHandler, HsmConnectionQueryHandler,
};
```

### In Your Module's lib.rs

```rust
// Re-export for convenience
pub mod schema;
pub mod commands;
pub mod queries;
pub mod migrations;

// Re-export commonly used types
pub use schema::{HsmConnection, HsmVendor, HsmKey};
pub use commands::{
    CreateHsmConnectionCommand, UpdateHsmConnectionCommand,
    HsmConnectionCommandHandler,
};
pub use queries::HsmConnectionQueryHandler;
```

### Consuming Library Pattern (e.g., pim-hsm)

If you have a domain library that wraps the ORM module:

```rust
// In pim-hsm/src/lib.rs
pub mod hsm;
pub mod vendors;
pub mod keys;

// Re-export ORM types to avoid direct pim-orm dependency in API layer
pub use pim_orm::{
    // Schema types (for responses)
    HsmConnection, HsmVendor, HsmKey,
    // Command types (for requests)
    CreateHsmConnectionCommand, UpdateHsmConnectionCommand,
    // Handler types (for API layer)
    HsmConnectionCommandHandler, HsmConnectionQueryHandler,
    // Error types (for error conversion)
    PimOrmError,
};
```

**WHY**: Re-exporting creates a clean API surface. Consumers import from `pim_orm::*` rather than navigating sub-crates. The consuming library can further re-export to isolate the API layer from direct ORM dependencies.

---

## Manager/Service Layer Pattern

**Pattern**: Domain managers wrap ORM handlers with business logic.

### Manager Structure

```rust
use pim_orm::{
    HsmConnectionCommandHandler, HsmConnectionQueryHandler,
    CreateHsmConnectionCommand, UpdateHsmConnectionCommand,
    HsmConnection,
};

pub struct HsmConnectionManager {}

impl HsmConnectionManager {
    pub fn new() -> Self {
        Self {}
    }

    /// Create a new HSM connection with validation
    pub async fn create_connection(
        &self,
        name: String,
        vendor_id: i32,
        host: String,
        port: u16,
    ) -> Result<HsmConnection, HsmError> {
        // Business logic: Validate inputs
        if name.is_empty() {
            return Err(HsmError::Validation("Name cannot be empty".into()));
        }

        if port == 0 {
            return Err(HsmError::Validation("Port must be non-zero".into()));
        }

        // Get connection and create handlers
        let connection = pim_orm::db::global::connection().await
            .map_err(|e| HsmError::Internal(e.to_string()))?;
        let cmd_handler = HsmConnectionCommandHandler::with_connection(connection.clone());
        let query_handler = HsmConnectionQueryHandler::with_connection(connection);

        // Execute command
        let command = CreateHsmConnectionCommand {
            name,
            vendor_id,
            host,
            port: port as i32,
        };

        let id = cmd_handler.create_connection(command).await?;

        // Fetch and return created entity
        let created = query_handler
            .get_connection(id)
            .await?
            .ok_or_else(|| HsmError::Internal("Failed to retrieve created connection".into()))?;

        Ok(created)
    }

    /// Update a connection with partial updates
    pub async fn update_connection(
        &self,
        id: i32,
        name: Option<String>,
        host: Option<String>,
        port: Option<u16>,
    ) -> Result<HsmConnection, HsmError> {
        // Business logic: Validate updates
        if let Some(ref n) = name {
            if n.is_empty() {
                return Err(HsmError::Validation("Name cannot be empty".into()));
            }
        }

        let connection = pim_orm::db::global::connection().await
            .map_err(|e| HsmError::Internal(e.to_string()))?;
        let cmd_handler = HsmConnectionCommandHandler::with_connection(connection.clone());
        let query_handler = HsmConnectionQueryHandler::with_connection(connection);

        let command = UpdateHsmConnectionCommand {
            id,
            name,
            host,
            port: port.map(|p| p as i32),
        };

        cmd_handler.update_connection(command).await?;

        let updated = query_handler
            .get_connection(id)
            .await?
            .ok_or_else(|| HsmError::NotFound(format!("Connection {}", id)))?;

        Ok(updated)
    }

    /// Test HSM connection
    pub async fn test_connection(&self, id: i32) -> Result<bool, HsmError> {
        // Business logic: Fetch connection, validate, and test
        let connection = pim_orm::db::global::connection().await
            .map_err(|e| HsmError::Internal(e.to_string()))?;
        let query_handler = HsmConnectionQueryHandler::with_connection(connection);

        let conn = query_handler
            .get_connection(id)
            .await?
            .ok_or_else(|| HsmError::NotFound(format!("Connection {}", id)))?;

        // Domain-specific logic (not in ORM)
        let result = self.perform_connection_test(&conn).await?;

        Ok(result)
    }

    // Private helper for domain logic
    async fn perform_connection_test(&self, conn: &HsmConnection) -> Result<bool, HsmError> {
        // Actual connection testing logic here
        Ok(true)
    }
}
```

**WHY**: Managers encapsulate business logic and validation, keeping ORM handlers focused on pure database operations. This separation makes testing easier and keeps the ORM layer reusable across different applications.

---

## Thin API Layer Pattern

**⚠️ IMPORTANT**: If you're just starting a new module, see [Quick Start: Creating a New Module](#quick-start-creating-a-new-module) for the correct initial structure. This section describes the final architecture after your module is established.

**Pattern**: The API layer is thin, delegating to a fully functional library layer.

### Project Structure

```
pim-hsm/                    # Workspace root
├── Cargo.toml              # Workspace definition
├── src/                    # Library crate (fully functional)
│   ├── lib.rs
│   ├── connections/
│   │   ├── mod.rs
│   │   ├── manager.rs      # Business logic
│   │   ├── client.rs       # External integrations
│   │   └── error.rs
│   ├── vendors/
│   │   └── ...
│   └── keys/
│       └── ...
└── api/                    # API crate (thin wrapper)
    ├── Cargo.toml
    └── src/
        ├── lib.rs
        ├── main.rs         # Server entry point
        ├── connections/
        │   ├── mod.rs
        │   ├── handlers.rs # Thin Axum handlers
        │   ├── routes.rs   # Route definitions
        │   └── models.rs   # API-specific DTOs
        └── state.rs        # Application state
```

### Library Layer (src/)

The library layer contains all business logic and can be used independently:

```rust
// In pim-hsm/src/connections/manager.rs
pub struct HsmConnectionManager {
    // Business logic, no web framework dependencies
}

impl HsmConnectionManager {
    pub async fn create_connection(...) -> Result<HsmConnection, HsmError> {
        // Full implementation here
    }
}
```

### API Layer (api/)

The API layer is a thin wrapper that:

1. Defines HTTP routes
2. Parses/validates HTTP requests
3. Calls library functions
4. Formats HTTP responses

```rust
// In pim-hsm/api/src/connections/handlers.rs
use axum::{extract::State, Json};
use pim_hsm::connections::HsmConnectionManager;

pub async fn create_connection(
    State(state): State<AppState>,
    Json(req): Json<CreateConnectionRequest>,
) -> Result<Json<HsmConnection>, ApiError> {
    // Thin handler: just parse, call library, and return
    let manager = HsmConnectionManager::new();
    let connection = manager
        .create_connection(req.name, req.vendor_id, req.host, req.port)
        .await?;
    Ok(Json(connection))
}
```

### Cargo.toml Structure

```toml
# Workspace root
[workspace]
members = [".", "api"]

# Library crate
[package]
name = "pim-hsm"
version = "0.1.0"

[dependencies]
pim-orm = { workspace = true, features = ["hsm"] }
tokio = { workspace = true }
# No web framework dependencies here

# API crate
[package]
name = "pim-hsm-api"
version = "0.1.0"

[dependencies]
pim-hsm = { path = ".." }  # Depends on library
axum = { workspace = true }
tower-http = { workspace = true }
```

### Benefits

1. **Library is reusable**: Can be used in CLI tools, tests, other services
2. **API is replaceable**: Can swap Axum for another framework without touching business logic
3. **Testing is easier**: Test business logic without HTTP layer
4. **Clear separation**: Web concerns (routing, serialization) vs. domain logic

**WHY**: A thin API layer keeps web framework concerns separate from business logic. The library layer can be used independently in tests, CLI tools, or other services. This is the pattern used by `pim-events` (library in `src/`, API in `api/`).

---

## Query Extraction at the API Boundary

**Pattern**: Every Axum handler that consumes an ORM filter struct (or any struct that may carry repeated query keys) MUST extract it with `axum_extra::extract::Query`, never `axum::extract::Query`.

This is the wire-level enforcement of the ORM's filter contracts. The ORM declares filters as `Vec<T>` (and the universal `PagedRequest.sort: Vec<String>`); the API boundary is responsible for honoring that on the wire. Picking the wrong extractor silently breaks the contract for every paginated endpoint.

### The contract

`PagedRequest<F>` (defined in `pim-orm-core/src/queries/pagination.rs`) is the canonical paginated-request envelope, and it is `Vec`-bearing by design:

```rust
pub struct PagedRequest<F = ()> {
    pub page: Option<u32>,
    pub page_size: Option<u32>,
    pub q: Option<String>,
    pub sort: Vec<String>,        // repeated `?sort=...&sort=...`
    #[serde(flatten)]
    pub filter: F,                // typically also contains Vec<T> fields
}
```

Module filters routinely add their own `Vec<T>` fields, e.g.:

- `AccountStoreFilters.store_type: Vec<String>` (`pim-orm-jobs`)
- `DiscoveredAccountWindowsFilters.system_id: Option<Vec<i32>>`
- `AccountUsageFilters.system_id: Option<Vec<i32>>`, `account_id: Option<Vec<i32>>`
- `LogEntryFilters.level: Vec<i32>` (`pim-orm-events`)

These are accessed on the wire via repeated query keys: `?filter.system_id=12&filter.system_id=34`.

### Why `axum::extract::Query` breaks the contract

`axum::extract::Query` deserializes via `serde_urlencoded`, which rejects duplicate keys with `Failed to deserialize query string: duplicate field 'X'`. The moment a client sends `?sort=a&sort=b` or `?filter.system_id=1&filter.system_id=2`, the request returns `400` regardless of how the filter struct is declared. The ORM's `Vec<T>` contract is unreachable.

`axum_extra::extract::Query` deserializes via `serde_html_form`, which collects duplicate keys into a `Vec` and works correctly with `#[serde(flatten)]` filter structs.

### Required pattern

```rust
use axum::extract::{Json, Path, State};   // Query is NOT imported from here
use axum_extra::extract::Query;           // Always source Query from axum_extra

pub async fn list_things(
    State(state): State<AppState>,
    Query(request): Query<PagedRequest<ThingFilters>>,
) -> Result<Json<PagedResponse<Thing>>, ApiError> {
    // ...
}
```

### Anti-pattern

```rust
use axum::extract::{Json, Path, Query, State};   // ❌ Query from axum::extract

pub async fn list_things(
    Query(request): Query<PagedRequest<ThingFilters>>,   // ❌ 400s on duplicate keys
) -> Result<Json<PagedResponse<Thing>>, ApiError> { /* ... */ }
```

### Multi-value filters: declaring `Vec<T>` in the ORM

When the wire format for a filter is "repeat the key", the ORM filter field should be `Vec<T>` (or `Option<Vec<T>>` if optional), with a custom deserializer that accepts both a single scalar and a repeated list. The `string_or_vec` / `option_vec_i32_from_strings` helpers in `pim-orm-jobs/src/schema/filters.rs` are the reference implementations:

```rust
pub struct AccountStoreFilters {
    #[serde(rename = "filter.store_type", default, deserialize_with = "string_or_vec")]
    pub store_type: Vec<String>,
}
```

This makes both `?filter.store_type=MYSQL` and `?filter.store_type=MYSQL&filter.store_type=ORACLE` valid — but only when the handler uses `axum_extra::extract::Query`.

### OpenAPI documentation

When a filter is `Vec<T>`, document it as such in the `#[utoipa::path]` params block, including the "repeat the param" hint:

```rust
("filter.system_id" = Option<Vec<i32>>, Query, description = "Filter by system ID(s); repeat the param to match ANY"),
```

This signals to UI / SDK generators that the parameter is multi-value.

### Verification

Three probes verify a route honors the contract end-to-end:

```bash
# 1. Single value (must succeed)
curl 'http://localhost:8080/api/things?filter.system_id=1'

# 2. Multi-value filter (must succeed and return ANY-of)
curl 'http://localhost:8080/api/things?filter.system_id=1&filter.system_id=2'

# 3. Multi-sort (must succeed; PagedRequest.sort is Vec<String> for every paginated route)
curl 'http://localhost:8080/api/things?sort=name&sort=id'
```

Any 400 with `duplicate field 'X'` means the handler is using the wrong extractor.

### Scope

This rule applies to every API crate that consumes `pim-orm` filter structs — `pim-jobs-api`, `pim-events-api`, `pim-perms-api`, `pim-rpa-api`, `pim-messaging-api`, `pim-doc-api`, etc. The `events/api` crate carries an inline summary at `mix-server/crates/events/api/QUERY_EXTRACTION.md` that points back here; treat this section as the source of truth.

**WHY**: The ORM owns the filter contract. Any extractor that silently drops or rejects multi-value filters violates that contract at the wire boundary, and the failure is invisible to handler authors (the type-checker is happy because both extractors satisfy the same `Query<T>` signature). Mandating `axum_extra::extract::Query` everywhere makes the contract enforceable by `grep`, prevents per-handler regressions, and keeps the OpenAPI surface honest about which parameters are multi-value.

---

## SQL Best Practices

**Pattern**: Use PostgreSQL-specific features and patterns for robust, maintainable SQL.

### COALESCE for Partial Updates

Use `COALESCE` to handle partial updates elegantly, avoiding complex dynamic query building:

```rust
pub async fn update_entity(&self, cmd: UpdateEntityCommand) -> Result<(), PimOrmError> {
    // Use COALESCE to only update provided fields
    // NULL parameters are ignored, keeping existing values
    let query = r#"
        UPDATE entities
        SET
            name = COALESCE($1, name),
            description = COALESCE($2, description),
            status = COALESCE($3, status),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $4
    "#;

    self.connection
        .execute(query, &[
            &cmd.name,           // Option<String>
            &cmd.description,    // Option<String>
            &cmd.status,         // Option<i32>
            &cmd.id,             // i32
        ])
        .await?;

    Ok(())
}
```

**WHY**: `COALESCE` eliminates the need for complex dynamic SQL generation and lifetime management. When a parameter is `None` (NULL in SQL), `COALESCE` uses the existing column value. This is much simpler and safer than building SQL strings dynamically.

### TIMESTAMPTZ for All Timestamps

Always use `TIMESTAMPTZ` (timestamp with time zone) instead of `TIMESTAMP`:

```sql
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- ✅ TIMESTAMPTZ
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- ✅ TIMESTAMPTZ
    deleted_at TIMESTAMPTZ,                         -- ✅ TIMESTAMPTZ (optional)

    -- ❌ NEVER use TIMESTAMP without time zone
    -- bad_timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**WHY**: `TIMESTAMPTZ` stores all timestamps in UTC and automatically converts to the client's timezone. This prevents timezone-related bugs and makes audit trails reliable across different regions.

### RETURNING Clause for Inserts

Use `RETURNING` to get the generated ID in a single query:

```rust
pub async fn create_entity(&self, cmd: CreateEntityCommand) -> Result<i32, PimOrmError> {
    let query = r#"
        INSERT INTO entities (name, description, status)
        VALUES ($1, $2, $3)
        RETURNING id
    "#;

    let row = self.connection
        .query_one(query, &[&cmd.name, &cmd.description, &cmd.status])
        .await?;

    let id: i32 = row.get("id")?;
    Ok(id)
}
```

### CTEs for Complex Updates

Use Common Table Expressions (CTEs) to return full entity data after updates:

```rust
pub async fn update_entity(&self, cmd: UpdateEntityCommand) -> Result<Entity, PimOrmError> {
    let query = r#"
        WITH updated AS (
            UPDATE entities
            SET
                name = COALESCE($1, name),
                description = COALESCE($2, description),
                status = COALESCE($3, status),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $4
            RETURNING *
        )
        SELECT
            u.id,
            u.name,
            u.description,
            u.status,
            u.created_at::text,
            u.updated_at::text
        FROM updated u
    "#;

    let row = self.connection
        .query_one(query, &[&cmd.name, &cmd.description, &cmd.status, &cmd.id])
        .await?;

    Entity::from_row(row.as_ref())
}
```

**WHY**: CTEs allow you to update and return data in a single query, reducing round trips to the database. Casting timestamps to `text` ensures consistent serialization.

### Idempotent Operations

All migrations and data modifications should be idempotent:

```sql
-- ✅ Idempotent table creation
CREATE TABLE IF NOT EXISTS entities (...);

-- ✅ Idempotent index creation
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

-- ✅ Idempotent data insertion
INSERT INTO lookup_values (id, code, label)
VALUES (1, 'ACTIVE', 'Active')
ON CONFLICT (id) DO NOTHING;

-- ✅ Idempotent column addition
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'entities' AND column_name = 'new_column'
    ) THEN
        ALTER TABLE entities ADD COLUMN new_column TEXT;
    END IF;
END $$;
```

### Soft Deletes

Use `deleted_at` timestamp for soft deletes instead of boolean flags:

```sql
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    deleted_at TIMESTAMPTZ,  -- NULL = active, timestamp = deleted
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for active records
CREATE INDEX idx_entities_active ON entities(id) WHERE deleted_at IS NULL;
```

```rust
// Soft delete
let query = "UPDATE entities SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1";

// Query only active records
let query = "SELECT * FROM entities WHERE deleted_at IS NULL";

// Restore a soft-deleted record
let query = "UPDATE entities SET deleted_at = NULL WHERE id = $1";
```

**WHY**: Soft deletes preserve data for audit trails and allow restoration. Using a timestamp instead of a boolean provides additional information (when was it deleted).

### Parameterized Queries

Always use parameterized queries to prevent SQL injection:

```rust
// ✅ Correct: Parameterized
let query = "SELECT * FROM entities WHERE name = $1";
let entities = query_as_dyn(conn, query, &[&name]).await?;

// ❌ NEVER: String concatenation
let query = format!("SELECT * FROM entities WHERE name = '{}'", name);
```

---

## Documentation Pattern

**Pattern**: Use "WHY" comments to explain design decisions and architectural choices.

### WHY Comments

Explain the reasoning behind non-obvious decisions:

```rust
/// Register a new offline endpoint
///
/// WHY: We use machine_id (UUID) as the primary identifier instead of an
/// auto-increment ID because endpoints can register offline and we need
/// globally unique IDs without coordination. The assigned_machine_name
/// handles collision detection for human-readable names.
pub async fn register_endpoint(
    &self,
    machine_id: Uuid,
    machine_name: String,
    mac_address: String,
) -> Result<OfflineEndpoint, OfflineError> {
    // Implementation
}
```

### Migration Comments

Document the purpose and context of migrations:

```sql
-- Migration: Add allowed_special_chars to groups
-- Description: Allow per-group customization of special characters in passwords
-- Version: 031
-- Date: 2025-11-28
--
-- WHY: Different groups may have different password requirements based on
-- their target systems. Some legacy systems don't support certain special
-- characters, so we need group-level control.

ALTER TABLE offline_system_groups
ADD COLUMN IF NOT EXISTS allowed_special_chars TEXT;
```

### Schema Comments

Use PostgreSQL comments for database-level documentation:

```sql
COMMENT ON TABLE hsm_connections IS 'HSM connection configurations for PKCS#11 and cloud HSMs';
COMMENT ON COLUMN hsm_connections.pkcs11_library_path IS 'Path to PKCS#11 shared library (.so/.dll)';
COMMENT ON COLUMN hsm_connections.slot_id IS 'PKCS#11 slot identifier (0-based index)';
```

### Module-Level Documentation

Document the purpose and scope of each module:

````rust
//! # HSM Connection Management
//!
//! This module provides CRUD operations for HSM (Hardware Security Module)
//! connections, supporting both PKCS#11 on-premises HSMs and cloud HSM services.
//!
//! ## Architecture
//!
//! - **Schema**: Domain models representing database tables
//! - **Commands**: Write operations (create, update, delete)
//! - **Queries**: Read operations (get, list, search)
//! - **Migrations**: Database schema versioning
//!
//! ## Usage
//!
//! ```rust
//! use pim_orm_hsm::{HsmConnectionCommandHandler, CreateHsmConnectionCommand};
//!
//! let connection = pim_orm::db::global::connection().await?;
//! let handler = HsmConnectionCommandHandler::with_connection(connection);
//! let cmd = CreateHsmConnectionCommand { /* ... */ };
//! let id = handler.create_connection(cmd).await?;
//! ```
````

**WHY**: "WHY" comments capture the reasoning that isn't obvious from the code itself. They help future maintainers (including AI agents) understand the context and constraints that led to specific design decisions.

---

## Summary Checklist

When implementing a new PIM-ORM module, ensure you:

### Module Setup

- [ ] Choose a single-word tag/name (e.g., `hsm`, `vault`, `messaging`)
- [ ] Register module ID in the hierarchy (next available: 007)
- [ ] Use consistent table prefix: `{tag}_*` (e.g., `hsm_connections`, `hsm_vendors`)
- [ ] Create workspace with library (`src/`) and API (`api/`) crates

### Data Types

- [ ] Use `i32` for primary keys (default) or `i64` for high-volume tables
- [ ] Use `TIMESTAMPTZ` for all timestamps, `DateTime<Utc>` in Rust
- [ ] Store enums as `i32` with helper conversion methods
- [ ] Create standardized lookup tables for all enums
- [ ] Include `utoipa::ToSchema` on all schema types (OpenAPI by design)

### Architecture

- [ ] Initialize global connection pool once at application startup
- [ ] Separate commands (writes) from queries (reads) using CQRS
- [ ] Create handlers per-request, not stored in application state
- [ ] Use `#[derive(FromDatabaseRow)]` for schema structs
- [ ] Create separate command/request DTOs with `Option<T>` for updates
- [ ] Wrap ORM handlers in domain managers for business logic
- [ ] Keep API layer thin, business logic in library layer

### Migrations

- [ ] Use module-specific migration prefix (e.g., `006` for hsm)
- [ ] Make all migrations idempotent (safe to run multiple times)
- [ ] Use `IF NOT EXISTS`, `IF EXISTS`, `ON CONFLICT DO NOTHING`
- [ ] Seed lookup data with `INSERT ... ON CONFLICT DO NOTHING`
- [ ] Use `TIMESTAMPTZ` for all timestamp columns
- [ ] Add `COMMENT ON TABLE` and `COMMENT ON COLUMN` for documentation

### SQL Best Practices

- [ ] Use `COALESCE` for partial updates
- [ ] Use `RETURNING` clause for inserts
- [ ] Use CTEs for complex updates that return full entities
- [ ] Use soft deletes with `deleted_at TIMESTAMPTZ`
- [ ] Always use parameterized queries

### API & UI Integration

- [ ] Create lookup query handler with `list_*_types()` methods
- [ ] Expose lookup endpoints at `/api/lookups/{enum-name}-types`
- [ ] Document all endpoints with OpenAPI/utoipa
- [ ] Re-export commonly used types in module's `lib.rs`

### Documentation

- [ ] Add "WHY" comments for non-obvious design decisions
- [ ] Document tables and columns with PostgreSQL `COMMENT ON`
- [ ] Include module-level documentation in `lib.rs`
- [ ] Update this document's module registry with your new module

---

## Example: Creating pim-orm-hsm

Here's a quick reference for creating a new HSM module:

### 1. Module Structure

```
pim-orm-hsm/
├── Cargo.toml
├── migrations/
│   ├── 006000001_create_hsm_enum_lookups.sql
│   ├── 006000002_create_hsm_vendors.sql
│   ├── 006000003_create_hsm_connections.sql
│   └── 006000004_create_hsm_keys.sql
└── src/
    ├── lib.rs
    ├── migrations.rs
    ├── schema/
    │   ├── mod.rs
    │   ├── lookups.rs      # Lookup types
    │   ├── vendors.rs
    │   ├── connections.rs
    │   └── keys.rs
    ├── commands/
    │   ├── mod.rs
    │   ├── vendor_commands.rs
    │   ├── connection_commands.rs
    │   └── key_commands.rs
    └── queries/
        ├── mod.rs
        ├── lookup_queries.rs  # Lookup queries
        ├── vendor_queries.rs
        ├── connection_queries.rs
        └── key_queries.rs
```

### 2. Cargo.toml

```toml
[package]
name = "pim-orm-hsm"
version = "0.1.0"
edition = "2021"

[dependencies]
pim-orm-core = { workspace = true }
pim-orm-derive = { workspace = true }
tokio = { workspace = true }
async-trait = { workspace = true }
serde = { workspace = true }
chrono = { workspace = true }
thiserror = { workspace = true }
utoipa = { workspace = true }  # OpenAPI support
uuid = { workspace = true }
```

### 3. First Migration: Lookup Tables

```sql
-- migrations/006000001_create_hsm_enum_lookups.sql
-- pim-orm-hsm module migration
-- Part of HSM configuration management

-- Migration: Create HSM Enum Lookup Tables
-- Description: Standardized lookup tables for HSM enums
-- Version: 001
-- Date: 2025-12-29

-- ============================================================================
-- HSM TYPE LOOKUP
-- ============================================================================

CREATE TABLE IF NOT EXISTS hsm_types (
    id INTEGER PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO hsm_types (id, code, label, description, display_order) VALUES
    (1, 'PKCS11_HSM', 'PKCS#11 HSM', 'On-premises HSM using PKCS#11 interface', 1),
    (2, 'CLOUD_HSM', 'Cloud HSM', 'Cloud-based HSM service', 2)
ON CONFLICT (id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_hsm_types_active ON hsm_types(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE hsm_types IS 'HSM type enumeration';
COMMENT ON COLUMN hsm_types.code IS 'Machine-readable code (e.g., PKCS11_HSM, CLOUD_HSM)';
```

### 4. Schema with OpenAPI

```rust
// src/schema/connections.rs
use pim_orm_derive::FromDatabaseRow;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, FromDatabaseRow, Serialize, Deserialize, utoipa::ToSchema)]
#[from_database_row(database = "postgres")]
pub struct HsmConnection {
    pub id: i32,
    pub name: String,
    pub vendor_id: i32,
    pub hsm_type: i32,  // References hsm_types lookup
    pub host: String,
    pub port: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

// src/schema/lookups.rs
#[derive(Debug, Clone, FromDatabaseRow, Serialize, Deserialize, utoipa::ToSchema)]
#[from_database_row(database = "postgres")]
pub struct HsmType {
    pub id: i32,
    pub code: String,
    pub label: String,
    pub description: Option<String>,
    pub is_active: bool,
    pub display_order: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}
```

### 5. Update Command with COALESCE

```rust
// src/commands/connection_commands.rs
pub async fn update_connection(&self, cmd: UpdateHsmConnectionCommand) -> Result<(), PimOrmError> {
    let query = r#"
        UPDATE hsm_connections
        SET
            name = COALESCE($1, name),
            vendor_id = COALESCE($2, vendor_id),
            hsm_type = COALESCE($3, hsm_type),
            host = COALESCE($4, host),
            port = COALESCE($5, port),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $6
    "#;

    self.connection
        .execute(query, &[
            &cmd.name,
            &cmd.vendor_id,
            &cmd.hsm_type,
            &cmd.host,
            &cmd.port,
            &cmd.id,
        ])
        .await?;

    Ok(())
}
```

### 6. Add to pim-orm

```toml
# In pim-orm/Cargo.toml
[features]
hsm = ["dep:pim-orm-hsm"]

[dependencies]
pim-orm-hsm = { workspace = true, optional = true }
```

```rust
// In pim-orm/lib.rs
#[cfg(feature = "hsm")]
pub use pim_orm_hsm::{
    // Schema types
    HsmConnection, HsmVendor, HsmKey, HsmType,
    // Command types
    HsmConnectionCommandHandler, CreateHsmConnectionCommand, UpdateHsmConnectionCommand,
    // Query types
    HsmConnectionQueryHandler, LookupQueryHandler,
};
```

### 7. Update Module Registry

Add to the [System Architecture Hierarchy](#system-architecture-hierarchy) section:

```
| `006`     | hsm         | pim-orm-hsm          | HSM configuration management     |
```

---

## Modular Seeds Pattern

### Overview

The modular seeds pattern provides idempotent test/development data for each ORM module, following the same modular architecture as migrations. Seeds are executed via the `--seeds` flag in pim-server and are NOT tracked in the migrations table.

### Key Differences: Migrations vs Seeds

| Aspect | Migrations | Seeds |
|--------|------------|-------|
| **Tracking** | Recorded in `_sqlx_migrations` table | Not tracked |
| **Execution** | Once per version | Every time `--seeds` is used |
| **Purpose** | Schema changes | Test/dev data |
| **Idempotency** | Required | Required (via `ON CONFLICT DO NOTHING`) |
| **Module Function** | `run_migrations()` (required) | `run_seeds()` (optional, default no-op) |

### Architecture

```
pim-server --seeds
    ↓
pim-orm DatabasePool::run_seeds()
    ↓
├─→ pim-orm-jobs::run_seeds()     → seeds/*.sql (if implemented)
├─→ pim-orm-events::run_seeds()   → seeds/*.sql (if implemented)
├─→ pim-orm-offline::run_seeds()  → default no-op
└─→ pim-orm-hsm::run_seeds()      → default no-op
```

### OrmModule Trait

The `OrmModule` trait in `pim-orm-core/src/migrations.rs` defines the interface for all ORM modules:

```rust
#[async_trait]
pub trait OrmModule {
    /// Module name for logging
    fn module_name() -> &'static str;
    
    /// Module ID for migration/seed file prefixes
    fn module_id() -> u16;
    
    /// Run module migrations (REQUIRED)
    async fn run_migrations(pool: &sqlx::PgPool) 
        -> Result<(), sqlx::migrate::MigrateError>;
    
    /// Run module seeds (OPTIONAL - default is no-op)
    async fn run_seeds(_pool: &sqlx::PgPool) -> Result<(), sqlx::Error> {
        tracing::debug!("No seeds defined for {} module", Self::module_name());
        Ok(())
    }
}
```

**Benefits:**
- **Type Safety**: Ensures consistent interface across all modules
- **Optional Seeds**: Default no-op means modules without seeds don't need stub functions
- **Clean API**: No sqlx types leak out of ORM layer
- **Flexibility**: Modules can override `run_seeds()` when they have seed data

### Seed File Naming Convention

Seed files follow the same naming pattern as migrations:

```
{module_id}000{sequence}_{description}.sql
```

**Examples:**
- Jobs module (ID 001): `001000001_test_systems.sql`
- Events module (ID 002): `002000001_email_servers.sql`
- Offline module (ID 003): `003000001_offline_data.sql`
- HSM module (ID 006): `006000001_hsm_config.sql`

**Rules:**
- Module ID prefix ensures seeds are scoped to their module
- Sequence numbers start at 000001 for each module
- Use descriptive names that indicate the seed's purpose
- Files are executed in alphanumeric order

### Idempotency Requirements

All seed SQL must be idempotent (safe to run multiple times):

**Required Pattern:**
```sql
INSERT INTO table_name (columns...)
VALUES (...)
ON CONFLICT (unique_column) DO NOTHING;
```

**Alternative Patterns:**
```sql
-- Using WHERE NOT EXISTS
INSERT INTO table_name (columns...)
SELECT ...
WHERE NOT EXISTS (
    SELECT 1 FROM table_name WHERE condition
);

-- Using UPSERT for updates
INSERT INTO table_name (id, name, value)
VALUES (1, 'config', 'value')
ON CONFLICT (id) DO UPDATE
SET value = EXCLUDED.value;
```

**Why Idempotency Matters:**
- Seeds run every time `--seeds` flag is used
- No tracking in `_sqlx_migrations` table
- Must not fail or duplicate data on repeated execution
- Enables rapid development iteration

### Adding Seeds to a Module

#### Step 1: Create seeds/ Directory

```bash
cd pim-orm-{module}
mkdir seeds
```

#### Step 2: Create Seed Files

Create SQL files following the naming convention:

```sql
-- seeds/001000001_test_data.sql
INSERT INTO my_table (id, name, description)
VALUES
    (1, 'Test Item 1', 'First test item'),
    (2, 'Test Item 2', 'Second test item')
ON CONFLICT (id) DO NOTHING;
```

#### Step 3: Implement OrmModule Trait

In your module's `src/migrations.rs`:

```rust
use async_trait::async_trait;
use pim_orm_core::migrations::{
    run_module_migrations, run_module_seeds, MigrationConfig, OrmModule,
};

pub struct MyModule;

#[async_trait]
impl OrmModule for MyModule {
    fn module_name() -> &'static str {
        "my_module"
    }

    fn module_id() -> u16 {
        005  // Use your assigned module ID
    }

    async fn run_migrations(pool: &sqlx::PgPool) 
        -> Result<(), sqlx::migrate::MigrateError> 
    {
        let migrator = sqlx::migrate!("./migrations");
        let config = MigrationConfig::module("my_module", 005);
        run_module_migrations(pool, &migrator, &config).await?;
        Ok(())
    }

    // Override run_seeds() since we have seed files
    async fn run_seeds(pool: &sqlx::PgPool) -> Result<(), sqlx::Error> {
        let migrator = sqlx::migrate!("./seeds");
        let config = MigrationConfig::module("my_module", 005);
        run_module_seeds(pool, &migrator, &config).await?;
        Ok(())
    }
}

// Public API functions
pub async fn run_migrations(pool: &sqlx::PgPool) 
    -> Result<(), sqlx::migrate::MigrateError> 
{
    MyModule::run_migrations(pool).await
}

pub async fn run_seeds(pool: &sqlx::PgPool) -> Result<(), sqlx::Error> {
    MyModule::run_seeds(pool).await
}
```

#### Step 4: Update pim-orm Integration

In `pim-orm/src/db/pool.rs`, add your module to the `run_seeds()` function:

```rust
#[cfg(feature = "my_module")]
{
    tracing::info!("Running my_module seeds...");
    pim_orm_my_module::migrations::run_seeds(pool)
        .await
        .map_err(|e| PimOrmError::Migration(e.to_string()))?;
}
```

### Module Without Seeds

If your module doesn't need seeds, simply implement the trait without overriding `run_seeds()`:

```rust
#[async_trait]
impl OrmModule for MyModule {
    fn module_name() -> &'static str {
        "my_module"
    }

    fn module_id() -> u16 {
        005
    }

    async fn run_migrations(pool: &sqlx::PgPool) 
        -> Result<(), sqlx::migrate::MigrateError> 
    {
        // ... migration implementation
    }

    // No run_seeds() override - uses default no-op from trait
}
```

The default trait implementation will log a debug message and return `Ok(())`.

### Example Seed File Structure

#### Simple Reference Data

```sql
-- 002000001_email_servers.sql
INSERT INTO email_servers (id, server_name, smtp_host, smtp_port, use_tls)
VALUES
    (1, 'Development SMTP', 'localhost', 1025, FALSE),
    (2, 'Production SMTP', 'smtp.example.com', 587, TRUE)
ON CONFLICT (id) DO NOTHING;
```

#### Related Data with Foreign Keys

```sql
-- 002000002_email_destinations.sql
-- Depends on email_servers seed being run first

INSERT INTO email_destinations (
    id, 
    destination_name, 
    email_server_id, 
    from_address, 
    to_addresses
)
VALUES
    (1, 'Dev Alerts', 1, 'alerts@dev.local', ARRAY['dev@example.com']),
    (2, 'Prod Alerts', 2, 'alerts@example.com', ARRAY['ops@example.com'])
ON CONFLICT (id) DO NOTHING;
```

#### Complex Data with Timestamps

```sql
-- 001000002_test_jobs_and_schedules.sql
INSERT INTO base_job_info (
    job_type,
    job_operation,
    priority_base,
    priority_current,
    next_run_time_utc,
    last_result
) VALUES
    (1, 2, 10, 10, NOW() + INTERVAL '2 minutes', 1),
    (4, 5, 9, 9, NOW() + INTERVAL '3 minutes', 1)
ON CONFLICT DO NOTHING;

-- Schedules reference jobs by ID (assuming sequential IDs)
INSERT INTO schedule_job_info (
    base_job_id,
    every_n_days,
    every_n_hours,
    every_n_minutes,
    max_retries
) VALUES
    (1, 0, 0, 2, 3),
    (2, 0, 0, 3, 3)
ON CONFLICT DO NOTHING;
```

### Best Practices

1. **Keep Seeds Small**: One logical group per file (e.g., all email servers, all test systems)
2. **Order Dependencies**: Name files so dependencies execute first (001, 002, 003...)
3. **Use Realistic Data**: Seed data should represent actual use cases
4. **Document Purpose**: Add comments explaining what the seed data is for
5. **Test Idempotency**: Run `--seeds` multiple times to verify no errors
6. **Avoid Hardcoded IDs**: Use `ON CONFLICT` or `WHERE NOT EXISTS` instead of assuming IDs
7. **Use Relative Timestamps**: `NOW() + INTERVAL '5 minutes'` instead of fixed dates
8. **Clean Data**: Remove seeds when they're no longer needed

### Testing Seeds

```bash
# Run migrations and seeds
pim-server --seeds

# Run seeds multiple times to test idempotency
pim-server --seeds
pim-server --seeds

# Run without seeds to verify normal operation
pim-server
```

### Troubleshooting

**Problem**: Seeds fail with "relation does not exist"
- **Solution**: Ensure migrations have run first. Seeds depend on schema created by migrations.

**Problem**: Seeds fail with "duplicate key value"
- **Solution**: Add `ON CONFLICT DO NOTHING` or use `WHERE NOT EXISTS` pattern.

**Problem**: Seeds not found during compilation
- **Solution**: Ensure `seeds/` directory exists and `sqlx::migrate!("./seeds")` path is correct.

**Problem**: Module seeds not executing
- **Solution**: Check that module feature is enabled and module is added to `pim-orm/src/db/pool.rs`.

### Current Implementation Status

**Modules with Seeds:**
- ✅ **pim-orm-jobs** (6 files): Test systems, jobs, schedules, management sets, credentials, discovered systems, discovery properties
- ✅ **pim-orm-events** (10 files): Email, SMS, SIEM, webhooks, queues, alerts

**Modules without Seeds:**
- ✅ **pim-orm-offline**: Uses default no-op
- ✅ **pim-orm-hsm**: Uses default no-op

All modules implement the `OrmModule` trait for consistency.

---

## Test Infrastructure Pattern

**Pattern**: Centralized test harness in `pim-orm-core` that provides an embedded PostgreSQL database, real migrations and seeds, and SQL-free assertion utilities -- enabling fast, high-coverage tests of the library/manager layer without HTTP, CLI, Docker, or raw SQL in consumer code.

### Problem

PIM applications follow a layered architecture: thin API/CLI shells delegate to library managers, which delegate to ORM handlers. Testing the managers and ORM handlers today requires either a running server with a deployed database, or hand-rolled mocks scattered across crates with no shared infrastructure. This is slow, fragile, and results in low coverage.

Additionally, all SQL must live in the ORM layer (`mix-orm`). Consumer repos like `mix-server` enforce a strict no-raw-SQL contract -- if SQL appears in app code (even in tests), developers and agents treat it as precedent and start writing SQL in production code. Any test infrastructure must respect this boundary.

### Solution

Enable the `test-utils` feature on `pim-orm-core`:

```toml
[dev-dependencies]
pim-orm-core = { workspace = true, features = ["test-utils"] }
```

This provides:

- **`TestDatabase`** -- starts an embedded PostgreSQL instance, creates a uniquely-named database, and provides both a `PgPool` (for running migrations/seeds) and a `DatabasePool` (for the ORM abstraction layer). The global singleton is initialized from this ephemeral database, so managers and handlers work unchanged.
- **`TableInspector`** -- verifies raw database state (e.g., confirming encryption-at-rest) without any SQL appearing in consumer test files. All SQL generation is encapsulated inside `pim-orm-core`.
- **`TestDatabaseProvider` trait** -- abstracts the embedded database lifecycle. PostgreSQL via `postgresql_embedded` is the first provider; future providers (MSSQL via testcontainers, Oracle, MySQL) implement the same trait.

### Key APIs

| Component | Purpose |
|-----------|---------|
| `TestDatabase::new()` | Start embedded PG, create ephemeral database |
| `db.pg_pool()` | Raw `PgPool` for `run_migrations()` / `run_seeds()` |
| `db.connection()` | `Arc<dyn DatabaseConnection>` for handlers |
| `db.init_global()` | Arm the global singleton (managers work unchanged) |
| `db.inspector("table")` | SQL-free `TableInspector` for raw state assertions |

**TableInspector methods** -- all SQL is generated internally, none leaks into consumer code:

| Method | Returns | Purpose |
|--------|---------|---------|
| `get_bytes(col, key_col, key_val)` | `Option<Vec<u8>>` | Raw bytes (encryption verification) |
| `get_string(col, key_col, key_val)` | `Option<String>` | String column value |
| `get_i32(col, key_col, key_val)` | `Option<i32>` | Integer column value |
| `get_i64(col, key_col, key_val)` | `Option<i64>` | Large integer column value |
| `row_exists(key_col, key_val)` | `bool` | Check row existence |
| `count(key_col, key_val)` | `i64` | Count matching rows |
| `count_all()` | `i64` | Count all rows in table |

### Usage

A shared `tokio::runtime::Runtime` via `LazyLock` ensures all pool operations run on the same runtime that created the connections (avoids cross-runtime issues with sqlx). Tests use `#[test]` + `RT.block_on()` instead of `#[tokio::test]`.

See `pim-orm-perms/tests/smoke_test_utils.rs` for a complete working example covering: embedded PG startup, migrations, seeds, CRUD via handlers, and `TableInspector` assertions.

### Multi-Database Extensibility

The `TestDatabaseProvider` trait abstracts the embedded database lifecycle:

```rust
#[async_trait]
pub trait TestDatabaseProvider: Send + Sync {
    async fn start(&mut self) -> Result<String>;
    fn database_type(&self) -> DatabaseType;
    async fn stop(&mut self) -> Result<()>;
}
```

- **`EmbeddedPostgres`** is the default (and currently only) provider
- Future providers can wrap `testcontainers` for MSSQL/Oracle or native embedded crates
- `TableInspector` generates dialect-correct SQL (`$1` for PG, `?` for MySQL, `@p1` for MSSQL) based on `DatabaseType`
- `TestDatabase::with_provider(custom_provider)` allows tests to specify which backend to use

### Design Rules

1. **No SQL in consumer code, ever.** `TableInspector` encapsulates all raw inspection queries. No SQL strings appear in test files outside `pim-orm-core`.
2. **No application code changes.** Managers call `global_connection()` and get a real connection to the embedded DB. Handlers use `::with_connection()`. Nothing is refactored or injected differently than production.
3. **One TestDatabase per test binary.** Use `LazyLock` or equivalent. The embedded PG starts once (~2-3s on first download, instant after caching) and individual tests run in single-digit milliseconds.
4. **Write idempotent tests.** All tests in a binary share one DB. Use unique identifiers or clean up after tests.
5. **Embedded PG binaries are cached.** First run downloads ~70MB to `~/.theseus/postgresql`. Subsequent runs reuse the cached binaries. The temp database is destroyed on process exit.

### What This Tests vs. What It Doesn't

| Tested (library layer) | Not tested (thin API layer) |
|------------------------|-----------------------------|
| Managers and business logic | HTTP routing and middleware |
| ORM handlers and queries | Request/response serialization |
| Validation and domain rules | Authentication/authorization headers |
| Cross-cutting concerns (encryption, audit) | API error formatting |
| Migration correctness | CLI argument parsing |

The thin API layer is intentionally excluded -- it's tested separately at the integration level. This harness focuses on the library layer where the bulk of business logic lives.

---

## Deprecated Patterns

The following patterns exist in older code and are being actively removed. **Do not use them in new code.**

### ❌ `Handler::new()` with hidden `connection_blocking()`

```rust
// ❌ DEPRECATED — do not use
impl EntityCommandHandler {
    pub fn new() -> Self {
        let connection = pim_orm::db::global::connection_blocking();
        Self { connection }
    }
}

// ❌ DEPRECATED — caller hides the connection dependency
let handler = EntityCommandHandler::new();
```

**Why it's wrong:**

1. **Hides the connection dependency** — callers can't see that a database connection is being acquired, making the code harder to reason about.
2. **Blocks the async runtime** — `connection_blocking()` uses `tokio::task::block_in_place` + `block_on` to synchronously acquire a connection inside an async context.
3. **Panics on failure** — uses `.expect()` internally instead of returning `Result`, so a connection pool issue crashes the process.
4. **Prevents connection sharing** — each `::new()` call acquires its own connection reference independently, so two handlers in the same request can't share a connection obtained once.

### ✅ Correct replacement

```rust
// ✅ CORRECT — explicit connection, async, fallible
let connection = pim_orm::db::global::connection().await?;
let handler = EntityCommandHandler::with_connection(connection);
```

When multiple handlers are needed in the same operation, acquire the connection once and share it:

```rust
let connection = pim_orm::db::global::connection().await?;
let cmd_handler = EntityCommandHandler::with_connection(connection.clone());
let query_handler = EntityQueryHandler::with_connection(connection);
```

### ❌ `Default` impl that calls `new()`

Some handlers derive or implement `Default` by calling `new()`. These `Default` impls propagate the same anti-pattern and should be removed alongside `new()`.

### ❌ `connection_blocking()` anywhere

`connection_blocking()` is deprecated everywhere — in handlers, managers, and service layers. All code runs in async contexts, so use `connection().await?` instead.

### Migration status

This cleanup is tracked as a cross-project effort across `mix-orm` and `mix-server`. The `::new()` constructors and `Default` impls will be removed from all 22 affected handlers, and all ~70 call sites in `mix-server` will be migrated to `with_connection()`.

---

**End of Document**

For questions or clarifications, refer to existing modules:

- `pim-orm-jobs`: Job scheduling patterns, comprehensive seed data examples
- `pim-orm-events`: Event distribution patterns
- `pim-orm-offline`: Endpoint management patterns
