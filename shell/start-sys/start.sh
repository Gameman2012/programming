#!/bin/bash
content='open teams-discord-telegram'

# عرض التنبيه باستخدام zenity
zenity --info --text="$content" --title="تنبيه" --width=300 &
#المايك
wpctl set-volume 53 0.50  
#سكربتات
/home/mahmoud/programming/shell/start-sys/backup/backup.sh   &
/home/mahmoud/programming/shell/start-sys/backup/backup-settings.sh &
#start sound
brightness=$(brightnessctl -m | cut -d, -f4 | tr -d '%')
volume=$(pactl get-sink-volume @DEFAULT_SINK@ | head -n1 | awk '{print $5}' | tr -d '%')

if [ "$brightness" -eq 100 ] && [ "$volume" -ge 30 ]; then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.30  && mpv --no-video /home/mahmoud/programming/shell/start-sys/Windows\ XP\ Startup.mp3 &
fi
