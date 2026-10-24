# Scope & Forensic Limitations

1. **Academic Nature:** ForenX is built for scientific research, education, and benchmark evaluation. It is not ISO 17025 accredited or certified as a courtroom evidence acquisition suite.
2. **Admissibility:** Software outputs must be corroborated with manual SQLite inspection and secondary verification.
3. **Deleted Record Recovery:** ForenX parses active B-tree SQLite records; it does not perform automated carver operations over unallocated SQLite page freelists.
4. **Encrypted Profiles:** ForenX assumes unencrypted SQLite databases. DPAPI or NSS master-password encrypted artifacts require pre-ingestion decryption.
