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
if test (brightnessctl -m | cut -d, -f4 | tr -d '%') -eq 100 -a (pactl get-sink-volume @DEFAULT_SINK@ | head -n1 | awk '{print $5}' | tr -d '%') -ge 30
        mpv --no-video /home/mahmoud/programming/shell/start-sys/Windows\ XP\ Startup.mp3  &
end
