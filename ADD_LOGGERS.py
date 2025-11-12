#!/usr/bin/env python3
"""
اسکریپت اضافه کردن logger به فایل‌های Python
"""

import os
import sys

def add_logger_to_file(filepath):
    """اضافه کردن logger به یک فایل"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # اگر logger دارد، skip
        if 'logger' in content or 'logging' in content:
            return False
        
        # اگر فایل خالی یا خیلی کوچک است
        if len(content.strip()) < 50:
            return False
        
        lines = content.split('\n')
        
        # پیدا کردن جای مناسب برای اضافه کردن import
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif line.strip() and not line.startswith('#'):
                # اولین خط غیر import و غیر comment
                if import_index == 0:
                    import_index = i
                break
        
        # اضافه کردن logger import
        logger_import = "import logging\nlogger = logging.getLogger(__name__)\n"
        
        if import_index == 0:
            # اگر هیچ import ندارد، به ابتدا اضافه کن
            lines.insert(0, logger_import)
        else:
            # بعد از آخرین import
            lines.insert(import_index, logger_import)
        
        # نوشتن فایل
        new_content = '\n'.join(lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error in {filepath}: {e}")
        return False

def main():
    """تابع اصلی"""
    print("╔════════════════════════════════════════════════╗")
    print("║   📝 اضافه کردن Logger به فایل‌ها             ║")
    print("╚════════════════════════════════════════════════╝\n")
    
    added_count = 0
    skipped_count = 0
    
    # فایل‌هایی که نباید logger داشته باشند
    skip_files = ['__init__.py', 'states.py', 'config.py']
    
    for root, dirs, files in os.walk('bot'):
        # حذف __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and file not in skip_files:
                filepath = os.path.join(root, file)
                
                if add_logger_to_file(filepath):
                    print(f"  ✅ Added logger: {filepath}")
                    added_count += 1
                else:
                    skipped_count += 1
    
    print("\n" + "="*60)
    print(f"\n✅ Logger اضافه شد به: {added_count} فایل")
    print(f"⏭️  Skip شد: {skipped_count} فایل")
    print("\n💡 حالا دوباره اجرا کنید: python FULL_DEBUG.py\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
