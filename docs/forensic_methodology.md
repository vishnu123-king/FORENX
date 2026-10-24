# Forensic Methodology & Chain of Custody

## 1. Evidence Ingestion Workflow
1. **Case Association:** Evidence items must be tied to a distinct, versioned case ID.
2. **Pre-Copy Hash Calculation:** Streaming 64KB block SHA-256 calculation of the target source file.
3. **Controlled Copy:** Evidence bytes are duplicated into `forenx_workspace/evidence_vault/<case_id>/<evidence_id>/`.
4. **Post-Copy Verification:** SHA-256 is re-calculated on the acquired file. If the source was concurrently modified, the copy is aborted with `InconsistentEvidenceError`.
5. **SQLite Sidecar Accounting:** If `-wal` or `-shm` files exist, they are preserved alongside the main database.
6. **Working Copy Isolation:** A separate working replica is provisioned in `forenx_workspace/working_copies/` to guarantee that forensic analysis never touches vault originals.

## 2. Integrity Verification
A recorded hash proves consistency between the acquired bytes and the current stored file. It detects:
- Accidental file truncation.
- Unauthorized modifications.
- Bit-rot on underlying storage media.
It does **not** prove authenticity of the evidence before it was provided to the examiner.
