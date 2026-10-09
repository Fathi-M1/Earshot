#!/bin/bash
# shot.sh in.html out.png W H [scale]
S=${5:-1}
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=$S --window-size=$3,$4 --default-background-color=00000000 --screenshot="$2" "file://$(realpath $1)" >/dev/null 2>&1
