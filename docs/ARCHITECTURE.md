# Architecture
Data Flow: Attack -> Telemetry -> Collection -> Normalization -> SIEM -> Detection -> Enrichment -> Case Management -> SOAR -> Response -> Evidence -> Reporting.
All components are containerized with pinned versions, non-root users, and resource limits.