#!/bin/bash
# 1. تجهيز المسارات وتنسيق التاريخ والوقت
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

MAHMOUD_DIR="$HOME"
MAHMOUD_ZIP="$HOME/mahmoud_${TIMESTAMP}.zip"

# بيانات البوت
TOKEN="8918788558:AAGB8nwqqRDOyTbIU3bjB1Jrk3byCbEkMIY"
CHAT_ID="7672071730"


# ─────────────────────────────────────────────
# 2. مقارنة شجرة /storage وإرسال التحديثات
# ─────────────────────────────────────────────

TREE_FILE="$HOME/برمجة/shell/backup/tree.txt"
TEMP_TREE=$(mktemp)
tree -L 4 -I "node_modules|.git|__pycache__|venv|.venv|target" "/storage" > "$TEMP_TREE"

# ─────────────────────────────────────────────
# 2A. إرسال تحديث شجرة /storage إن وجد
# ─────────────────────────────────────────────
if [ -f "$TREE_FILE" ] && ! diff -q "$TREE_FILE" "$TEMP_TREE" > /dev/null 2>&1; then
    cp "$TEMP_TREE" "$TREE_FILE"

    curl -s -F document=@"$TREE_FILE" \
         https://api.telegram.org/bot$TOKEN/sendDocument \
         -F chat_id="$CHAT_ID" \
         -F caption="تم تحديث شجرة /storage" > /dev/null

elif [ ! -f "$TREE_FILE" ]; then
    cp "$TEMP_TREE" "$TREE_FILE"
fi
rm -f "$TEMP_TREE"

# ─────────────────────────────────────────────
# 2B. البحث عن ملفات جديدة في /storage/mahmoud
# ─────────────────────────────────────────────
FILES_LIST="$HOME/برمجة/shell/backup/files_list.txt"
CURRENT_LIST=$(mktemp)
find "/storage/mahmoud" -type f | sort > "$CURRENT_LIST"

if [ -f "$FILES_LIST" ]; then
    ADDED=$(comm -13 "$FILES_LIST" "$CURRENT_LIST")
    if [ -n "$ADDED" ]; then
        echo "$ADDED" | while IFS= read -r file; do
            [ -f "$file" ] && curl -s -F document=@"$file" \
                 https://api.telegram.org/bot$TOKEN/sendDocument \
                 -F chat_id="$CHAT_ID" \
                 -F caption="ملف جديد: $file" > /dev/null
        done
    fi
fi
cp "$CURRENT_LIST" "$FILES_LIST"
rm -f "$CURRENT_LIST"
