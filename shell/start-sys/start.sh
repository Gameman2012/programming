#!/bin/bash
content='open teams-discord-telegram'

# عرض التنبيه باستخدام zenity
zenity --info --text="$content" --title="تنبيه" --width=300
#المايك
wpctl set-volume 53 0.50  
