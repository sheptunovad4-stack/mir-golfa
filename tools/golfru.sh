#!/system/bin/sh
# ГОЛЬФ.РУ — любительские турниры -> TSV: дата_дд.мм.гггг \t название \t путь_карточки
# Страница показывает только ближайшие события; архива прошедших турниров нет.
# Запуск: sh golfru.sh > golfru.tsv

URL="https://golf.ru/when_play/lubitelskie/"
UA="Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"

curl -sS -L --connect-timeout 5 --max-time 25 -A "$UA" "$URL" \
  | awk 'BEGIN{RS="<dt>"} NR>1 {
  s = $0; d = ""; t = ""; h = ""
  if (match(s, /class="date">[^<]*/)) d = substr(s, RSTART + 13, RLENGTH - 13)
  if (match(s, /<a href="[^"]*"/))    h = substr(s, RSTART + 9, RLENGTH - 10)
  if (match(s, /<a [^>]*>[^<]*/)) { t = substr(s, RSTART, RLENGTH); sub(/^[^>]*>/, "", t) }
  if (d != "") printf "%s\t%s\t%s\n", d, t, h
}'
