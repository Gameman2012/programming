#!/bin/bash

# ==================== الإعدادات والمسارات ====================
# مسار مجلد الميديا على جهازك
MEDIA_DIR="/home/mahmoud/meadia/"

# اسم الريموت الحالي والمجلد الوجهة على Google Drive
REMOTE_MEDIA="backup:meadia"

# وقت الانتظار بين كل دورة مزامنة للميديا (1800 ثانية = نصف ساعة)
SLEEP_TIME=1800
# ============================================================

echo "=== [1] تشغيل مراقبة الأكواد عبر Gitwatch ==="

# التأكد من تشغيل الـ Gitwatch للمجلدين إذا لم يكونوا يعملوا بالفعل
if ! pgrep -f "gitwatch watch" > /dev/null; then
    echo "جاري تشغيل مراقبة المجلد الكبير (programming)..."
    gitwatch watch -m "Auto-commit" -r origin /home/mahmoud/programming/ > /dev/null 2>&1 &

    echo "جاري تشغيل مراقبة المجلد الصغير (studysrvr)..."
    gitwatch watch -m "Auto-commit" -r origin /home/mahmoud/programming/html/studysrvr/ > /dev/null 2>&1 &

    echo "✔ تم تفعيل مراقبة الجت بنجاح."
else
    echo "ℹ أداة Gitwatch تعمل بالفعل في الخلفية."
fi

echo "=== [2] بدء خدمة مزامنة الميديا عبر Rclone ==="

# حلقة المزامنة المستمرة للميديا
while true; do
    echo "بدأت مزامنة الميديا إلى Google Drive في: $(date)"

    # مزامنة الميديا صامتاً
    rclone sync "$MEDIA_DIR" "$REMOTE_MEDIA"

    echo "✔ انتهت مزامنة الميديا بنجاح. المزامنة القادمة بعد نصف ساعة."
    sleep $SLEEP_TIME
done
