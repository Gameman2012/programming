#!/usr/bin/fish

# 1. تحديد مسارات الحفظ
set BACKUP_DIR "/storage/mahmoud/programming/shell/start-sys/backup/Backup_KDE_"(date +%Y-%m-%d)
set TAR_FILE "$BACKUP_DIR.tar.gz"

# إنشاء المجلدات بصمت
mkdir -p "$BACKUP_DIR/kwin_configs"

# 2. نسخ ملفات الإعدادات والـ KWin
cp "$HOME/.config/kglobalshortcutsrc" "$BACKUP_DIR/" 2>/dev/null
cp "$HOME/.config/kwinrc" "$BACKUP_DIR/kwin_configs/" 2>/dev/null

if test -d "$HOME/.local/share/kwin/scripts/"
    cp -r "$HOME/.local/share/kwin/scripts" "$BACKUP_DIR/kwin_configs/" 2>/dev/null
end

# 3. توليد شجرة ملفات الديسكتوب الأساسية من النظام وحفظها مباشرة (دون نسخ الملفات)
echo "--- User Applications ---" > "$BACKUP_DIR/desktop_tree.txt"
if test -d "$HOME/.local/share/applications"
    tree "$HOME/.local/share/applications" >> "$BACKUP_DIR/desktop_tree.txt" 2>/dev/null
end

echo -e "\n--- Autostart Applications ---" >> "$BACKUP_DIR/desktop_tree.txt"
if test -d "$HOME/.config/autostart"
    tree "$HOME/.config/autostart" >> "$BACKUP_DIR/desktop_tree.txt" 2>/dev/null
end

# 4. ضغط المجلد بالكامل بصمت
tar -czf "$TAR_FILE" -C (dirname "$BACKUP_DIR") (basename "$BACKUP_DIR") 2>/dev/null

# 5. تنظيف المجلد المؤقت
rm -rf "$BACKUP_DIR"
