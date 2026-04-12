## Executive Summary
SQLite is increasingly recognized for production use in single-server, moderate-write environments, offering significant operational simplicity and cost reduction by eliminating a dedicated database server. Performance is optimized through explicit transactions for batching inserts and diligent connection reuse. While WAL mode enhances concurrency by allowing simultaneous reads and a single write, applications must handle SQLITE_BUSY errors, and BEGIN IMMEDIATE is advised for write-heavy transactions. Key challenges include ensuring data integrity during blue/green deployments with shared storage across containers, preventing corruption during backups (requiring .backup or sqlite3_rsync over cp), and managing its flexible type system (though STRICT tables offer mitigation). Its in-process design inherently limits horizontal write scaling, making client-server RDBMS like PostgreSQL a common alternative for future growth or high-concurrency needs.

## Main Technical Arguments
* Explicitly wrapping multiple data modifications within a single transaction significantly amortizes the "flushing" overhead, yielding substantial performance improvements for batch inserts and updates.
* Maintaining and reusing a single SQLite connection instance across multiple logical units of work is critical to avoid the performance penalty associated with repeatedly opening and closing the database file on disk.
* WAL (Write-Ahead Logging) mode is a fundamental configuration for production SQLite, enabling concurrent read operations while a single write transaction is active. This minimizes SQLITE_BUSY occurrences but requires application-level retry logic for write conflicts.
* To prevent transaction failures under high write load, it is recommended to use BEGIN IMMEDIATE when a transaction is known to involve writes, rather than allowing a read transaction to implicitly upgrade, which can lead to unrecoverable conflicts.
* SQLite employs a flexible type affinity system with five fundamental storage classes (NULL, INTEGER, REAL, TEXT, BLOB). While simplifying schema design, it allows storing data of a different type than declared in the column, potentially leading to data integrity issues if not strictly managed by the application or by using STRICT tables.
* The .backup command or sqlite3_rsync utility are the prescribed methods for creating crash-consistent backups of a live SQLite database. Direct file copying (cp) is explicitly warned against, especially with WAL mode, due to high risk of data corruption.
* For single-server deployments, tools like Litestream or ZFS replication enable continuous archiving and failover. However, blue/green deployments in containerized environments (e.g., Kamal) present challenges due to the shared memory requirements of WAL mode and the need for careful orchestration to prevent data corruption during switchovers.
* SQLite's architecture as an in-process library fundamentally limits its horizontal write scalability. While suitable for single-server, moderate-write applications, scaling to multiple application instances or high write throughput typically necessitates a client-server RDBMS.
* Performance benchmarks, particularly for I/O-bound operations, can be highly misleading when run on local development machines versus cloud infrastructure, as local SSDs often provide significantly higher IOPS than typical cloud database volumes.
* SQLite's SQL dialect has specific nuances and omissions (e.g., lack of ILIKE, different JSON path operators, behavior of AUTOINCREMENT and ROWID gaps) that require careful consideration and adaptation when porting applications or expecting PostgreSQL-like behavior.
* The ecosystem for managing and observing SQLite databases in production is less mature than for client-server databases. Tools like Datasette can provide web-based interfaces, but direct SSH access and raw SQL are often required for troubleshooting. The sqlite_sequence table is noted as a useful debugging tool for tracking auto-increment values.

## Pros of Using this Tech in Production
* Achieves massive performance gains by batching inserts within explicit transactions.
* Improves performance by reusing SQLite connection instances, avoiding repeated file opening overhead.
* Offers significant operational simplicity and cost savings by eliminating the need for a separate database server.
* Facilitates easy snapshotting and portability of the database file.
* WAL (Write-Ahead Logging) mode enables concurrent reads while allowing a single write operation.
* Features robust documentation, aiding in understanding its behavior.
* Utilizes a simplified datatype system with 5 core types, which can be a "breath of fresh air" for developers.
* Memory mapping can provide substantial speed improvements.
* Considered a rock-solid, in-process database solution ideal for desktop and mobile applications.
* Supports reliable live backups using the .backup command or sqlite3_rsync, ensuring crash-consistency.

## Cons and Risks
* Experiences concurrency issues with multiple simultaneous writers; writes are serialized, leading to SQLITE_BUSY errors that require application-level handling (e.g., busy_timeout and retry logic).
* Read transactions that are implicitly upgraded to write transactions are prone to failure under high write load and cannot be automatically restarted by SQLite.
* SQLite's internal locking mechanism can be unfair, potentially causing writers to experience timeouts under high contention, even with WAL mode.
* High risk of data corruption if backups are performed by direct file copying (cp) on a live database, especially when WAL mode is active.
* Blue/green deployment strategies, particularly with shared filesystems across containers (e.g., Kamal), can lead to data corruption due to complexities with WAL shared memory or improper database file switchover.
* Lacks certain advanced SQL features (e.g., ILIKE) and its default dynamic typing can mask data integrity issues, though STRICT tables offer a solution.
* Performance benchmarks conducted on development machines may not accurately reflect cloud environment performance due to differing IOPS capabilities.
* Not inherently designed for multi-server or high-concurrency write scaling, posing a "future-proofing" concern for applications anticipating growth.
* Limited mature tooling for accessing and maintaining SQLite databases in production environments compared to client-server RDBMS, often necessitating SSH and raw SQL or specialized web UIs like Datasette.
* Offers no inherent business liability coverage or formal support contracts, which can be a significant concern for regulated industries requiring stringent audit compliance.
* Can lead to Out-Of-Memory (OOM) issues on resource-constrained machines when running multiple concurrent processes (e.g., web, DB, exec containers).

## Alternative Tools Mentioned
* PostgreSQL
* MySQL
* DuckDB
* rqlite
* Firebird embedded
* Oracle
* MSSQL
* gobackup
* Litestream
* sqld (libsql/sqld)
* Shopify
