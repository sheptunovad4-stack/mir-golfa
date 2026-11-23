#!/system/bin/sh
# Белорусская ассоциация гольфа (ingolf.by) — календарный план 2026 -> TSV
# поля: start \t end \t место_и_даты \t название \t вид_спорта_и_категории
# Запуск: sh baf.sh > baf.tsv

URL="https://ingolf.by/turniryi/kalendarnyij-plan-na-2026"
UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"

curl -sS -L --connect-timeout 5 --max-time 25 -A "$UA" "$URL" \
  | awk 'BEGIN{RS="calendar-timeline-card\""}
NR>1 {
  s = $0
  p = index(s, "</article>"); if (p > 0) s = substr(s, 1, p)

  start = ""; end = ""; meta = ""; title = ""; subt = ""
  if (match(s, /data-start="[^"]*"/)) { start = substr(s, RSTART + 12, RLENGTH - 13) }
  if (match(s, /data-end="[^"]*"/))   { end   = substr(s, RSTART + 10, RLENGTH - 11) }

  if (match(s, /calendar-event-card__meta">[^<]*/)) {
    meta = substr(s, RSTART, RLENGTH); sub(/^[^>]*>/, "", meta)
    gsub(/[\r\n]+/, " ", meta)
    gsub(/^[ \t]+|[ \t]+$/, "", meta); gsub(/[ \t][ \t]+/, " ", meta)
  }
  if (match(s, /calendar-event-card__title">[^<]*/)) {
    title = substr(s, RSTART, RLENGTH); sub(/^[^>]*>/, "", title)
    gsub(/^[ \t]+|[ \t]+$/, "", title)
  }
  if (match(s, /calendar-event-card__subtitle">[^<]*/)) {
    subt = substr(s, RSTART, RLENGTH); sub(/^[^>]*>/, "", subt)
    gsub(/^[ \t]+|[ \t]+$/, "", subt)
  }
  if (title == "") next
  printf "%s\t%s\t%s\t%s\t%s\n", start, end, meta, title, subt
}'
