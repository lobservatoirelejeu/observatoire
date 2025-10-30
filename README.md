

ffmpeg -ss 00:00:00 -i 1643.mp4 -vframes 1 -q:v 1 intro.jpg
ffmpeg -ss 00:00:21 -to 00:00:26 -i 1643.mp4 -vf "scale=iw:ih" -r 30 output.gif

crop=iw*0.6:ih*0.82:iw*0.2:0

ffmpeg -ss 00:00:21 -to 00:00:26 -i '.\videos\L_Observatoire - Chant à déterminer.mp4' -vf "fps=30,scale=iw:ih:flags=lanczos,crop=iw*0.6:ih*0.82:iw*0.2:0" -c:v libwebp -lossless 1 -loop 0 -q:v 100 thinking.webp

