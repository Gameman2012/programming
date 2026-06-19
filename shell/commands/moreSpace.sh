#!/bin/bash

# التحقق: إذا فُتح من مدير الملفات/المتصفح (SHLVL=1) ولم تكن نافذة الترمينال قد فُتحت بعد
if [ "$SHLVL" -eq 1 ] && [ -z "$TERMINAL_OPENED" ]; then
    export TERMINAL_OPENED=1
    konsole --hold -e "$0" "$@"
    exit
fi

# تفقد المساحة المستخدمة قبل التنظيف (بالكيلوبايت)
BEFORE=$(df / | awk 'NR==2{print $3}')

# بدء طباعة العناوين الملونة عبر lolcat بشكل ديناميكي دون تخريب الـ stdin
echo "==========================================" | lolcat
echo " Starting Total System Cleanup... " | lolcat
echo "==========================================" | lolcat

echo "🔄 جاري إغلاق المتصفحات والتطبيقات (Vivaldi, Teams, Brave) بشكل آمن..."
for app in vivaldi teams-for-linux brave; do
    pkill "$app" && sleep 0.5 || pkill -9 "$app" 2>/dev/null
done

echo "🧹 جاري تنظيف ملفات النظام المؤقتة (Temporary Files)..."
sudo systemd-tmpfiles --clean

echo "💥 جاري حذف سجلات انهيار النظام القديمة (Coredumps) لتوفير المساحة..."
sudo rm -rf /var/lib/systemd/coredump/*

echo "📜 جاري تقليص حجم سجلات النظام (Journal Logs) وجعل حدها الأقصى 50 ميجابايت فقط..."
sudo journalctl --vacuum-size=50M

echo "📦 جاري تنظيف كاش حزم Pacman المحذوفة والمثبتة والإبقاء على آخر إصدار فقط..."
sudo paccache -rk1
sudo paccache -ruk0

echo "📦 جاري مسح كاش حزم (AUR & Pacman) ومستودعاتها بالكامل بشكل إجباري..."
sudo rm -rf /var/cache/pacman/pkg/download-* 2>/dev/null
echo -e "y\ny\n" | sudo pacman -Scc
yay -Scc --noconfirm

echo "🤖 جاري تنظيف مخلفات وحزم Flatpak القديمة والمعزولة (Unused Runtimes)..."
if command -v flatpak &> /dev/null; then
    flatpak uninstall --unused -y
else
    echo "👍 لا توجد حزم flatpak معزولة."
fi

echo "🗑 جاري البحث عن الحزم المعزولة (Orphans) وحذفها لتخفيف عبء مجلد /usr..."
if pacman -Qtdq > /dev/null 2>&1; then
    sudo pacman -Rns $(pacman -Qtdq) --noconfirm
else
    echo "👍 لا توجد حزم معزولة متبقية في النظام."
fi

echo "🌐 جاري تنظيف ملفات الكاش الداخلية والمخفية لمتصفحات Vivaldi و Brave وتطبيق Teams..."
CACHE_PATHS=(
    ~/.config/vivaldi/SODA/ ~/.config/vivaldi/SODALanguagePacks/ ~/.config/vivaldi/screen_ai/
    ~/.config/vivaldi/component_crx_cache/ ~/.config/vivaldi/"Crash Reports"/
    ~/.config/vivaldi/GrShaderCache/ ~/.config/vivaldi/ShaderCache/ ~/.config/vivaldi/Default/Cache/
    ~/.config/vivaldi/Default/"Code Cache"/ ~/.config/vivaldi/Default/GPUCache/
    ~/.config/vivaldi/Default/"Service Worker"/CacheStorage/ ~/.config/vivaldi/Default/WebStorage/
    ~/.config/teams-for-linux/Partitions/teams-4-linux/WebStorage/
    ~/.config/teams-for-linux/Partitions/teams-4-linux/GPUCache/
    ~/.config/teams-for-linux/Partitions/teams-4-linux/DawnGraphiteCache/
    ~/.config/teams-for-linux/Partitions/teams-4-linux/DawnWebGPUCache/
    ~--------------/GPUCache/ ~/.config/teams-for-linux/DawnGraphiteCache/
    ~/.config/teams-for-linux/DawnWebGPUCache/ ~/.config/teams-for-linux/Cache/
    ~/.config/teams-for-linux/"Code Cache"/
    ~/.config/BraveSoftware/Brave-Browser/Default/Cache/
    ~/.config/BraveSoftware/Brave-Browser/Default/"Code Cache"/
    ~/.config/BraveSoftware/Brave-Browser/Default/GPUCache/
    ~/.config/discord/Cache/ ~/.config/discord/"Code Cache"/
    ~/.config/Youtube/
    ~/.local/share/org.keshavnrj.ubuntu/WhatSie/QtWebEngine/Service\ Worker/Cache/
)

for path in "${CACHE_PATHS[@]}"; do
    rm -rf "$path" 2>/dev/null
done

echo "🗂 جاري تصفير مجلد الكاش الرئيسي للمستخدم الحالي (~/.cache)..."
rm -rf ~/.cache/*

if [ -d ~/.local/share/Trash/ ]; then
    echo "🗑 جاري إفراغ سلة المهملات المحلية للمستندات..."
    rm -rf ~/.local/share/Trash/* 2>/dev/null
fi

echo "--------------------------------" | lolcat
echo "DONE! Your system is now clean and fast." | lolcat

# حساب المساحة بعد التنظيف
AFTER=$(df / | awk 'NR==2{print $3}')
FREED=$(( (BEFORE - AFTER) / 1024 ))

if [ "$FREED" -le 0 ]; then
    echo "💾 النظام كان نظيفاً بالفعل! المساحة المستعادة: 0 MB" | lolcat
else
    echo "💾 تم تحرير مساحة فعلية قدرها: ${FREED} MB" | lolcat
fi

echo "--------------------------------" | lolcat

# ==================================================================
# 🔐 بداية جزء فحص الـ Btrfs الذكي بعد تصحيح لغز معرف الهوم 0/257
# ==================================================================
echo "⏳ جاري استدعاء صلاحيات الجذور لجلب بيانات Btrfs..."

if ! command -v bc &> /dev/null; then
    echo "❌ خطأ: حزمة bc غير مثبتة."
    exit 1
fi

TOTAL_DF_GB=$(df -BG / | awk 'NR==2 {print $3}' | sed 's/G//')
BTRFS_USAGE_RAW=$(sudo btrfs filesystem usage / 2>/dev/null)
QGROUP_DATA_RAW=$(sudo btrfs qgroup show -pcre / 2>/dev/null)

# 1. جلب حجم المساحة المستخدمة الكلية للبيانات (Data)
DATA_RAW=$(echo "$BTRFS_USAGE_RAW" | grep -A2 "Data" | grep "used" | awk '{print $2}')
if [ -z "$DATA_RAW" ]; then
    DATA_RAW=$(echo "$BTRFS_USAGE_RAW" | grep -E "Data,.*used" | awk -F"used=" '{print $2}' | awk '{print $1}')
fi
DATA_VAL=$(echo "$DATA_RAW" | grep -oE "[0-9.]+")
DATA_UNIT=$(echo "$DATA_RAW" | grep -oE "[A-Za-z]+")

if [[ "$DATA_UNIT" == "MiB" || "$DATA_UNIT" == "M" ]]; then
    DATA_USED_GB=$(echo "scale=2; $DATA_VAL / 1024" | bc)
elif [[ "$DATA_UNIT" == "KiB" || "$DATA_UNIT" == "K" ]]; then
    DATA_USED_GB=$(echo "scale=2; $DATA_VAL / 1024 / 1024" | bc)
else
    DATA_USED_GB=$DATA_VAL
fi
if [ -z "$DATA_USED_GB" ] || [ "$DATA_USED_GB" == "" ]; then DATA_USED_GB="$TOTAL_DF_GB"; fi

# 2. حساب تأثير السنابشوتس الكلي (تمت إضافة استثناء الصارم لـ 0/257)
SNAPSHOT_IMPACT=$(echo "$QGROUP_DATA_RAW" | awk '
NR>2 {
    qid=$1; ref=$2; exc=$3; path=$4;
    if (qid == "0/5" || qid == "0/257" || path ~ /@home/ || path ~ /@root/ || path ~ /@cache/ || path ~ /@tmp/ || path ~ /@log/ || path ~ /@swap/ || path == "<toplevel>" || path == "@") {
        next;
    }
    val = exc; sub(/[A-Za-z]+/,"",val);
    unit = exc; gsub(/[0-9.]+/,"",unit);
    
    if (unit ~ /MiB/ || unit ~ /M/) { gb = val / 1024; }
    else if (unit ~ /KiB/ || unit ~ /K/) { gb = val / 1024 / 1024; }
    else { gb = val; }
    sum += gb;
}
END { printf "%.2f", sum }')

if [ -z "$SNAPSHOT_IMPACT" ] || [ "$SNAPSHOT_IMPACT" == "" ]; then SNAPSHOT_IMPACT="0.00"; fi

# 3. جلب الميتاداتا بدقة واحتساب حجمها
METADATA_RAW=$(echo "$BTRFS_USAGE_RAW" | grep -A2 "Metadata" | grep "used" | awk '{print $2}')
METADATA_VAL=$(echo "$METADATA_RAW" | grep -oE "[0-9.]+")
METADATA_UNIT=$(echo "$METADATA_RAW" | grep -oE "[A-Za-z]+")

if [[ "$METADATA_UNIT" == "MiB" || "$METADATA_UNIT" == "M" ]]; then
    METADATA_GB=$(echo "scale=2; $METADATA_VAL / 1024" | bc)
elif [[ "$METADATA_UNIT" == "KiB" || "$METADATA_UNIT" == "K" ]]; then
    METADATA_GB=$(echo "scale=2; $METADATA_VAL / 1024 / 1024" | bc)
else
    METADATA_GB=$METADATA_VAL
fi
if [ -z "$METADATA_GB" ] || [ "$METADATA_GB" == "" ]; then METADATA_GB="1.25"; fi

# 4. الحسابات الإجمالية لتصحيح الأرقام الحية
LIVE_FILES_GB=$(echo "scale=2; $DATA_USED_GB - $SNAPSHOT_IMPACT" | bc)
if (( $(echo "$LIVE_FILES_GB < 0" | bc -l) )); then LIVE_FILES_GB="0.00"; fi
LIVE_FILES_GB=$(printf "%.2f" "$LIVE_FILES_GB")

UNACCOUNTED=$(echo "scale=2; $TOTAL_DF_GB - ($LIVE_FILES_GB + $SNAPSHOT_IMPACT + $METADATA_GB)" | bc)
if (( $(echo "$UNACCOUNTED < 0" | bc -l) )); then UNACCOUNTED="0.00"; fi

echo ""
echo "=========================================================================================="
printf "📊 \033[1;32m%s\033[0m\n" "التقرير الإجمالي لمساحة القرص ونظام Btrfs"
echo "=========================================================================================="
printf "%-35s | %-12s | %-40s\n" "المكون" "المساحة" "طريقة الحساب / الشرح الفني"
echo "------------------------------------------------------------------------------------------"
printf "%-35s | %-12s | %-40s\n" "📁 ملفاتك الحية الحالية" "${LIVE_FILES_GB} GiB" "حجم ملفاتك الفعلية الحية الحالية (قراءة ncdu)."
printf "%-35s | %-12s | %-40s\n" "📸 تأثير السنابشوتس والباكاب الكلي" "${SNAPSHOT_IMPACT} GiB" "إجمالي المساحة الحصرية المحبوسة في كل السنابشوتس والباكاب المتبقية."
printf "%-35s | %-12s | %-40s\n" "⚙ ميتاداتا Btrfs (Metadata)" "${METADATA_GB} GiB" "مساحة تنظيم شجرة الملفات وعناوين الـ Copy-on-Write."
printf "%-35s | %-12s | %-40s\n" "🔍 مساحة غير محسوبة (Slack/System)" "${UNACCOUNTED} GiB" "الفروقات التقريبية بين نظام الثنائي (GiB) والعشري."
echo "------------------------------------------------------------------------------------------"
printf "\033[1;36m%-35s | %-12s | %-40s\033[0m\n" "📑 إجمالي المساحة المستخدمة الكلية" "${TOTAL_DF_GB}.00 GiB" "الرقم الفعلي الظاهر أمامك الآن في أمر df -h /"
==========================================================================================

echo ""
echo "=========================================================================================="
printf "📸 \033[1;34m%s\033[0m\n" "تفاصيل المساحة المؤثرة (الحصرية) لكل سنابشوت وباكاب على حدة"
echo "=========================================================================================="
printf "%-10s | %-15s | %-15s | %-35s\n" "ID" "المساحة المرجعية" "المساحة المؤثرة" "المسار / الاسم (Path)"
echo "------------------------------------------------------------------------------------------"

# إصلاح جدول العرض هنا أيضاً ليتجاهل 0/257 لكي لا تراه كـ none مجدداً
echo "$QGROUP_DATA_RAW" | awk '
NR>2 {
    qid=$1; ref=$2; exc=$3; path=$4;
    if (qid == "0/5" || qid == "0/257" || path ~ /@home/ || path ~ /@root/ || path ~ /@cache/ || path ~ /@tmp/ || path ~ /@log/ || path ~ /@swap/ || path == "<toplevel>" || path == "@") {
        next;
    }
    display_path = path;
    if (display_path == "-" || display_path == "") {
        display_path = "Subvolume ID: " qid;
    }
    printf "%-10s | %-15s | \033[1;33m%-15s\033[0m | %-35s\n", qid, ref, exc, display_path;
}'
echo "=========================================================================================="

echo "💡 المساحة المؤثرة (Exclusive): المساحة الفعلية التي تسترجعها لو حذفت السنابشوت."
echo "💡 المساحة المرجعية (Referenced): حجم الملفات الكلي (قد يكون مشتركاً مع غيرها)."

if [ "$TOTAL_DF_GB" -gt 40 ]; then
    echo ""
    echo "⚠ استهلاك القرص مرتفع. راجع أكبر مساحة مؤثرة بالأعلى."
fi

echo "--------------------------------" | lolcat
echo "💡 اضغط [Enter] لفتح ncdu (مع تجاهل السنابشوتس)، أو [Ctrl+C] للخروج..."
read -p ""
ncdu / --exclude /.snapshots --exclude /storage

echo 'تقدر تنفذ الامر التالي من اجل معرفة حجم التطبيقات:
expac -H M '\''%m\t%n'\'' | sort -h | awk '\''BEGIN { total = 0 } { print $0; total += $1 } END { printf "\n\033[1;32m-----------------------------------\033[0m\n\033[1;32mالحجم الإجمالي الكلي للحزم المثبتة:\033[0m\n-> %.2f MiB\n-> %.2f GiB\n\033[1;32m-----------------------------------\033[0m\n", total, (total / 1024) }'\'''
