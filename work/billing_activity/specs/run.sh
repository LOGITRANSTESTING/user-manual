#!/bin/bash
# usage: run.sh <spec.json> <src_dir> <prefix> [side_shots...]
cd "$(dirname "$0")/../../.."
I=".venv/bin/python tools/ilis.py --no-open"; W=work/billing_activity
SPEC=$1; SRC=$2; P=$3; shift 3; SIDE=" $* "
for k in $(.venv/bin/python -c "import json,sys;print(' '.join(json.load(open('$SPEC'))))"); do
  f="$SRC/$k.png"; [ -f "$W/edits/${P}_$k.png" ] && f="$W/edits/${P}_$k.png"; flag=""; [[ "$SIDE" == *" $k "* ]] && flag="--side"
  spec=$(.venv/bin/python -c "import json;print(json.dumps(json.load(open('$SPEC'))['$k']))")
  map=$(.venv/bin/python -c "import json;s=json.load(open('$SPEC'))['$k'];[d.__setitem__('n',None) for d in s];print(json.dumps(s))")
  $I prep "$f" $W/build/${P}_$k.png $flag >/dev/null
  $I prep "$f" "$W/build/map_${P}_$k.png" $flag --no-border >/dev/null
  if [ "$spec" = "[]" ]; then cp $W/build/${P}_$k.png $W/img/${P}_$k.png; cp $W/build/${P}_$k.png.json $W/img/${P}_$k.png.json 2>/dev/null; cp "$W/build/map_${P}_$k.png" "$W/mapping images/${P}_$k.png"
  else
    $I mark $W/build/${P}_$k.png $W/img/${P}_$k.png --spec "$spec" | grep -v PREVIEW
    $I mark "$W/build/map_${P}_$k.png" "$W/mapping images/${P}_$k.png" --spec "$map" >/dev/null
  fi
done
