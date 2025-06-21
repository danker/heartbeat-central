Check database status and recent healthcheck records

---

echo "Database location: healthchecks.db" && echo -e "\nHealthcheck count by status (last 24 hours):" && sqlite3 healthchecks.db "SELECT status, COUNT(*) as count FROM healthcheck_results WHERE timestamp > datetime('now', '-1 day') GROUP BY status;" 2>/dev/null || echo "No database found yet" && echo -e "\nLatest 5 healthcheck results:" && sqlite3 healthchecks.db "SELECT datetime(timestamp) as time, name, status, response_time FROM healthcheck_results ORDER BY timestamp DESC LIMIT 5;" 2>/dev/null || echo "No results yet"