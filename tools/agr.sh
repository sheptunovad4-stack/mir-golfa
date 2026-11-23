#!/system/bin/sh
# АГР (rusgolf.ru) — календарь соревнований 2026 -> TSV
# поля: месяц_таба \t даты_как_написано \t название \t место \t код \t организатор
# Запуск: sh agr.sh > agr.tsv   (нужны curl и awk)

URL="https://rusgolf.ru/ru/contests/tournament-calendar"
UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"

curl -sS -L --connect-timeout 5 --max-time 25 -A "$UA" "$URL" \
  | sed -e 's|<div class="[^"]*tab-pane"|\n@@TAB@@&|g' -e 's|<tr class=|\n@@ROW@@<tr class=|g' \
  | awk '
BEGIN {
  split("январь февраль март апрель май июнь июль август сентябрь октябрь ноябрь декабрь", mn, " ")
  tab = 0
}
/^@@TAB@@/ { tab++; next }
/^@@ROW@@/ {
  s = $0
  sub(/^@@ROW@@<tr class="/, "", s)
  s = substr(s, index(s, ">") + 1)
  p = index(s, "</tr>"); if (p > 0) s = substr(s, 1, p)

  gsub(/<br[^>]*>/, "\001", s)
  gsub(/<\/td>/, "\002", s)
  gsub(/<[^>]*>/, "", s)
  gsub(/data-v-[a-z0-9]+/, "", s)
  gsub(/&nbsp;/, " ", s)
  gsub(/&laquo;/, "«", s); gsub(/&raquo;/, "»", s)
  gsub(/&mdash;/, "—", s); gsub(/&ndash;/, "–", s)
  gsub(/&amp;/, "\\&", s); gsub(/&quot;/, "\"", s)

  n = split(s, a, "\002")
  m = split(a[1], b, "\001")
  date = b[1]; venue = b[2]; name = b[3]
  k = split(a[2], d, "\001"); code = d[2]
  k = split(a[3], e, "\001"); org = e[2]

  gsub(/^[ \t]+|[ \t]+$/, "", date)
  gsub(/^[ \t]+|[ \t]+$/, "", venue)
  gsub(/^[ \t]+|[ \t]+$/, "", name)
  gsub(/^[ \t]+|[ \t]+$/, "", code)
  gsub(/^[ \t]+|[ \t]+$/, "", org)
  gsub(/[ \t]+/, " ", name); gsub(/[ \t]+/, " ", venue); gsub(/[ \t]+/, " ", org)

  if (name == "") next
  printf "%s\t%s\t%s\t%s\t%s\t%s\n", mn[tab], date, name, venue, code, org
}'
