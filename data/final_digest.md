## Executive Summary
SQLite is widely adopted for production, particularly in embedded, local, and single-server web applications due to its operational simplicity, low latency, and minimal overhead. While it excels in read-heavy workloads with WAL mode enabling concurrent reads and serialized writes, its primary limitation is concurrent write performance, which can lead to "database locked" errors under high write contention or specific deployment patterns (e.g., blue-green deploys with shared storage without careful synchronization). Solutions like Litestream and LiteFS address backup and replication for single-writer, multi-reader architectures, but horizontal write scaling remains a challenge, often necessitating a shift to client-server databases like PostgreSQL for truly write-heavy or distributed systems.

## Main Technical Arguments
* SQLite's WAL (Write-Ahead Logging) mode allows one writer and multiple concurrent readers, but does not support multiple concurrent writers. Transactions that may write should use BEGIN IMMEDIATE to ensure serialized isolation and prevent errors.
* The primary performance bottleneck is write transactions per second, not raw data volume. Individual writes are fast (~1ms or ~250 microseconds on EBS-backed EC2), but frequent, short-lived write transactions (e.g., in Django with ATOMIC_REQUESTS=True and N+1 queries) can quickly lead to "database is locked" errors.
* Blue-green deployment strategies (e.g., Kamal) with shared SQLite files are prone to data corruption if both old and new containers concurrently access the database without meticulous synchronization. While WAL mode's mmap'd index file should work across containers on the same underlying filesystem, issues arise with network filesystems (NFS) or misconfigurations.
* SQLite's default dynamic typing (affinity) allows storing different data types in columns, which can hide bugs. Newer STRICT tables address this by enforcing type constraints. Developers are advised to define meaningful types and use CHECK constraints/triggers for data validity.
* Local developer machine benchmarks are often misleading due to significantly higher IOPS compared to cloud environments. Small datasets (e.g., 100k rows) easily fit into memory, obscuring performance characteristics for larger, disk-bound workloads.
* Direct file copying (cp) of a live SQLite database is unsafe and prone to corruption. Safe backup methods include SQLite's .backup API or VACUUM INTO. For replication and failover, tools like Litestream (streaming backups to object storage) and LiteFS (distributed replication for multi-server setups) are used.
* SQLite is well-suited for vertical scaling on a single, powerful server where the application embeds the database. For distributed systems or horizontal scaling, solutions like LiteFS or managed services (Turso) are explored, or sharding by customer with separate SQLite files.
* Regular ANALYZE or PRAGMA OPTIMIZE is necessary to update index statistics and prevent the query planner from becoming confused, ensuring optimal query performance.
* Explicitly managing database connection lifetimes (e.g., using with contexts in Python) is crucial to prevent connection leaks or excessive connections, which can lead to "database locked" errors or other low-level failures.
* Batching writes can improve performance but adds complexity and risk of data loss on crash if not handled carefully (re-implementing database features).
* Django is designed to have SQLite deadlocks; a trivial fix (not included by default) allows moderate loads. Setting SQLite PRAGMAs via Django settings is an upcoming feature.

## Pros of Using this Tech in Production
* Operational simplicity due to being a single file, simplifying deployment, administration, and backup processes for single-server applications.
* Low latency and high performance for individual read and write operations (often sub-millisecond), enabling complex serial queries and excellent performance for read-heavy workloads.
* Embedded, in-process nature eliminates network overhead and the need for a separate database server process, reducing infrastructure complexity and potential points of failure.
* Cost-effectiveness, capable of running on very cheap cloud instances with minimal resource requirements, ideal for hobby projects or small-to-mid-sized businesses.
* Robust backups via tools like Litestream, providing continuous, streaming backups to object storage (S3-compatible, R2, B2) with generous free tiers, ensuring data durability.
* WAL mode enables multiple readers to access the database concurrently while a single writer is active, making it suitable for read-heavy applications.
* Trivial to debug and test with a local copy of production data, enhancing developer productivity.
* Supports STRICT tables for type safety and standard SQL features like foreign key checks, constraints, and triggers.
* Widely adopted in billions of instances across various applications (desktop, mobile, web frameworks like Laravel 11, Windows base install), demonstrating reliability and versatility.
* Vertical scalability by upgrading server hardware (e.g., NVMe drives are particularly beneficial), often sufficient for many applications.
* Encourages services to access only their own data, promoting modularity and architectural hygiene.
* PRAGMA journal_mode=WAL is generally recommended and can double serial transactions per second on network-attached storage by halving flush FS commands.

## Cons and Risks
* SQLite fundamentally supports only one active writer at a time, even with WAL mode, which is the primary bottleneck for write-heavy applications or those requiring high write concurrency.
* Frequent "database is locked" errors can occur under high write contention, rapid-fire deploys, or inefficient transaction management (e.g., long-running transactions, N+1 queries in write contexts).
* Blue-green deployments or multi-container setups sharing a single SQLite file are prone to data corruption if not meticulously synchronized, as concurrent writes from multiple application instances can lead to inconsistencies.
* SQLite has major caveats when used over Network File Systems (NFS), including lack of WAL support and unreliable locking, leading to potential data corruption or persistent lock errors.
* Local development machine benchmarks are not representative of cloud production environments due to differences in IOPS and memory characteristics.
* SQLite's default dynamic typing can allow incorrect data types to be stored, potentially masking bugs that would be caught by stricter schema enforcement in other databases.
* SQLite does not natively support materialized views, requiring manual implementation (e.g., triggers or custom logic) for performance-critical pre-computed aggregations.
* Less community knowledge and established tuning practices specifically for SQLite in web application production environments compared to client-server databases like PostgreSQL.
* Synchronizing data across multiple local SQLite instances (e.g., for desktop/mobile apps) or updating read-only caches from remote systems is a significant pain point and often requires custom solutions.
* Graceful application upgrades without downtime can be challenging, often requiring a brief service interruption (seconds to minutes for migrations).
* Catastrophic failure recovery time can be several minutes (e.g., 6-10 minutes on AWS for a large dataset), which might be unacceptable for high-availability requirements.
* Writes can slow down significantly when tables reach 8-9 figures during fresh loads for ETL pipelines.
* The `json_extract` function returns native types, which can lead to silent failures if comparisons are made against string literals without explicit casting to TEXT.

## Alternative Tools Mentioned
* PostgreSQL: Recommended for write-heavy workloads, horizontal scaling, and when a traditional client-server database with robust concurrency is required.
* MySQL (InnoDB): A viable client-server database alternative, with the InnoDB engine providing ACID compliance and crash consistency.
* DuckDB: An in-process OLAP database that can read/write SQLite files, offering improved syntax and performance for analytical queries, though with its own concurrency model limitations.
* Litestream: A tool for streaming SQLite database changes to object storage (S3, DigitalOcean Spaces, Cloudflare R2, Backblaze B2) for continuous backups and disaster recovery.
* LiteFS: A file-system based replication layer for SQLite that enables distributed read replicas and failover across multiple application servers.
* Turso (libSQL/sqld): A managed database service for SQLite, offering a client-server distribution model and edge network capabilities.
* Firebird: An alternative embedded database option for local-only applications.
* gobackup: A containerized backup solution that can backup to multiple locations.
* sqlitestress: A tool for simulating SQLite workloads to test for "database locked" scenarios.
* OsQuery: An SQLite extension providing SQL access to operating system status and configuration via virtual tables.
* ZFS replication: An alternative to Litestream for snapshotting and replicating SQLite files.
