# usage: mk SRC NAME SPEC [side]   (SPEC '' = no marks)
P=".venv/bin/python tools/ilis.py --no-open"; W=work/edi_outgoing
mk(){ local src="$1" name="$2" spec="$3" side="$4"; local s=""; [ "$side" = side ] && s="--side"
  $P prep "$src" "$W/img/$name.png" $s >/dev/null && $P prep "$src" "$W/mapping images/$name.png" $s --no-border >/dev/null || return 1
  if [ -n "$spec" ]; then
    $P mark "$W/img/$name.png" "$W/img/$name.png" --spec "$spec" | grep -v PREVIEW
    local mspec=$(echo "$spec" | sed -E 's/"n": *[0-9]+/"n":null/g')
    $P mark "$W/mapping images/$name.png" "$W/mapping images/$name.png" --spec "$mspec" >/dev/null
  fi; }
