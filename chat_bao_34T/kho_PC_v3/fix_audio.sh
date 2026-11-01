#!/bin/bash
# Làm rõ giọng đọc: lọc ù, giảm đục, tăng dải 3–5 kHz, nén nhẹ, chuẩn hoá âm lượng (-15 LUFS, đỉnh -1.5 dB).
# Dùng: ./fix_audio.sh vao.mp4 ra.mp4   (giữ nguyên hình, chỉ xử lý tiếng)
IN="$1"; OUT="$2"
PRE="aresample=48000,highpass=f=90,equalizer=f=250:t=q:w=1:g=-3,equalizer=f=3000:t=q:w=1.2:g=5,equalizer=f=5500:t=q:w=1.5:g=3,acompressor=threshold=-22dB:ratio=3:attack=5:release=120:makeup=2"
J=$(ffmpeg -v info -i "$IN" -af "$PRE,loudnorm=I=-15:TP=-1.5:LRA=7:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
LN="loudnorm=I=-15:TP=-1.5:LRA=7:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
ffmpeg -y -i "$IN" -map 0:v -map 0:a -c:v copy -af "$PRE,$LN,aresample=48000" -c:a aac -b:a 96k -ac 1 -ar 48000 -movflags +faststart "$OUT"
