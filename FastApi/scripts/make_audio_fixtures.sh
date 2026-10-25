#!/usr/bin/env bash
# Regenerates the Postman audio fixtures in FastApi/postman/fixtures/.
#
# Always writes the small synthetic files used with the fake STT engine (valid WebM/EBML header so the
# API's content sniffing accepts them). When `say` (macOS) and `ffmpeg` exist it also records a real
# spoken sample, `question.real.webm`, for runs against Whisper.
set -euo pipefail
dir="$(cd "$(dirname "$0")/../postman/fixtures" && pwd)"
ebml='\x1a\x45\xdf\xa3'

# 64 bytes: accepted by the API, answered by the fake STT engine.
{ printf "$ebml"; head -c 60 /dev/zero; } > "$dir/question.webm"
# 4 KiB: over the 2048-byte limit used for the 413 scenario (VA_MAX_AUDIO_BYTES=2048).
{ printf "$ebml"; head -c 4092 /dev/zero; } > "$dir/large.webm"
# Declared as audio/webm but the bytes are an executable header: must be rejected with 415.
{ printf 'MZ'; head -c 62 /dev/zero; } > "$dir/fake.exe.webm"
: > "$dir/empty.webm"
printf 'this is not audio\n' > "$dir/not-audio.txt"

if command -v say >/dev/null && command -v ffmpeg >/dev/null; then
  say -o "$dir/.question.aiff" "How do I create a controller and a service in Java"
  ffmpeg -y -v error -i "$dir/.question.aiff" -ac 1 -ar 16000 -c:a libopus "$dir/question.real.webm"
  rm -f "$dir/.question.aiff"
  echo "wrote question.real.webm"
else
  echo "say/ffmpeg not found: skipped question.real.webm (record a short spoken sample yourself)"
fi
echo "fixtures in $dir"
