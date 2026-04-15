SecureChain
Tamper-Resistant Digital Evidence Chain-of-Custody System

SecureChain is a lightweight cybersecurity platform designed to ensure the integrity, traceability, and authenticity of digital evidence using a Dual-Chain Hashing with Integrity Verification (DCH-IV) approach.

Unlike blockchain-based solutions, SecureChain provides strong tamper detection with minimal overhead, making it suitable for practical forensic and compliance environments.

Features
Dual-Chain Hashing (EIC + CPC)
SHA-256 based integrity verification
Cross-chain binding mechanism
Continuous tamper detection on every access
Role-Based Access Control (RBAC)
Immutable chain-of-custody tracking
REST API using FastAPI
PostgreSQL backend
No blockchain dependency
Core Concept

SecureChain uses two cryptographic chains:

Evidence Integrity Chain (EIC):
SHA-256 hash of the evidence file to ensure file integrity
Custody Provenance Chain (CPC):
Hash chain of all evidence interactions including user, action, and timestamp

These are combined using:

Bound Hash = SHA256(EIC + CPC)

This ensures that both the evidence content and its custody history are cryptographically linked, making any unauthorized modification immediately detectable.

System Architecture
Users interact through a client interface
Requests are handled by a FastAPI backend
Core modules include:
Authentication and RBAC
Evidence Management
Custody Tracking
Integrity Verification
Storage:
Evidence files stored in file system
Metadata and logs stored in PostgreSQL
Workflow
Evidence is uploaded and hashed (EIC generated)
File and metadata are stored
Each interaction creates a custody record (CPC)
Cross-chain binding is applied
Integrity is verified on every access
Tech Stack
Backend: FastAPI (Python)
Database: PostgreSQL
Security: SHA-256 hashing, JWT authentication
Architecture: REST-based design
Use Cases
Digital forensics
Legal evidence management
Cybersecurity auditing
Compliance systems
Limitations
Relies on SHA-256 security assumptions
Evaluated in single-node setup
No protection against hardware failures or DoS attacks
Scalability not evaluated for very large datasets
Future Work
Integration of anomaly detection techniques
Exploration of post-quantum cryptography
Distributed deployment for fault tolerance
Performance optimization at scale
Research Paper

This project is based on the research work titled:
“A Dual-Chain Hashing Framework for Tamper-Resistant Digital Evidence Chain-of-Custody”
