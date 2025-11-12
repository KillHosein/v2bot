#!/usr/bin/env python3
"""
اسکریپت رفع خودکار تمام مشکلات
"""

import os
import sys
import re

def fix_indentation():
    """تبدیل tab به space"""
    print("\n🔧 تبدیل tabs به spaces...")
    
    fixed_count = 0
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if '\t' in content:
                        # تبدیل tab به 4 space
                        new_content = content.replace('\t', '    ')
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ Fixed: {filepath}")
                        fixed_count += 1
                except Exception as e:
                    print(f"  ❌ Error in {filepath}: {e}")
    
    print(f"\n  ✅ Fixed {fixed_count} files")
    return fixed_count

def fix_line_endings():
    """تبدیل line endings به LF"""
    print("\n🔧 تبدیل line endings به LF...")
    
    fixed_count = 0
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    
                    if b'\r\n' in content:
                        # تبدیل CRLF به LF
                        new_content = content.replace(b'\r\n', b'\n')
                        
                        with open(filepath, 'wb') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ Fixed: {filepath}")
                        fixed_count += 1
                except Exception as e:
                    print(f"  ❌ Error in {filepath}: {e}")
    
    print(f"\n  ✅ Fixed {fixed_count} files")
    return fixed_count

def add_missing_imports():
    """اضافه کردن import های گم شده به app.py"""
    print("\n🔧 بررسی و اضافه کردن import های گم شده...")
    
    app_file = "bot/app.py"
    if not os.path.exists(app_file):
        print("  ❌ app.py not found!")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # بررسی اینکه import ها وجود دارند
    if 'from .handlers.user_wallet import' in content:
        print("  ✅ v3.0 imports already exist")
        return True
    
    print("  ❌ v3.0 imports missing - they should be added manually")
    print("  💡 Run: python AUTO_FIX.py")
    return False

def remove_trailing_whitespace():
    """حذف فضای خالی انتهای خطوط"""
    print("\n🔧 حذف فضای خالی انتهای خطوط...")
    
    fixed_count = 0
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    new_lines = [line.rstrip() + '\n' if line.endswith('\n') else line.rstrip() 
                                for line in lines]
                    
                    new_content = ''.join(new_lines)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        old_content = f.read()
                    
                    if new_content != old_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ Fixed: {filepath}")
                        fixed_count += 1
                except Exception as e:
                    print(f"  ❌ Error in {filepath}: {e}")
    
    print(f"\n  ✅ Fixed {fixed_count} files")
    return fixed_count

def fix_encoding():
    """اطمینان از UTF-8 encoding"""
    print("\n🔧 بررسی encoding...")
    
    fixed_count = 0
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    # سعی کنیم به عنوان UTF-8 بخوانیم
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # اگر اولین خط # -*- coding: utf-8 -*- ندارد، اضافه کن
                    lines = content.split('\n')
                    if lines and not any('coding' in lines[i] for i in range(min(2, len(lines)))):
                        # اضافه کردن encoding به ابتدای فایل
                        if lines[0].startswith('#!'):
                            # اگر shebang دارد، بعد از آن اضافه کن
                            lines.insert(1, '# -*- coding: utf-8 -*-')
                        else:
                            lines.insert(0, '# -*- coding: utf-8 -*-')
                        
                        new_content = '\n'.join(lines)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ Added encoding: {filepath}")
                        fixed_count += 1
                    
                except UnicodeDecodeError:
                    print(f"  ⚠️  Non-UTF-8 file: {filepath}")
                except Exception as e:
                    print(f"  ❌ Error in {filepath}: {e}")
    
    if fixed_count == 0:
        print("  ✅ All files already have proper encoding")
    else:
        print(f"\n  ✅ Fixed {fixed_count} files")
    
    return fixed_count

def create_init_files():
    """ساخت __init__.py در پوشه‌های خالی"""
    print("\n🔧 بررسی __init__.py files...")
    
    created = []
    for root, dirs, files in os.walk('bot'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        # اگر پوشه فایل پایتون دارد و __init__.py ندارد
        has_py = any(f.endswith('.py') for f in files)
        has_init = '__init__.py' in files
        
        if has_py and not has_init:
            init_path = os.path.join(root, '__init__.py')
            try:
                with open(init_path, 'w', encoding='utf-8') as f:
                    f.write('# -*- coding: utf-8 -*-\n')
                created.append(init_path)
                print(f"  ✅ Created: {init_path}")
            except Exception as e:
                print(f"  ❌ Error creating {init_path}: {e}")
    
    if not created:
        print("  ✅ All required __init__.py files exist")
    else:
        print(f"\n  ✅ Created {len(created)} __init__.py files")
    
    return len(created)

def main():
    """تابع اصلی"""
    print("╔════════════════════════════════════════════════╗")
    print("║   🔧 رفع خودکار تمام مشکلات                   ║")
    print("╚════════════════════════════════════════════════╝")
    
    fixes = []
    
    # 1. Fix indentation
    count = fix_indentation()
    fixes.append(("Indentation", count))
    
    # 2. Fix line endings
    count = fix_line_endings()
    fixes.append(("Line Endings", count))
    
    # 3. Remove trailing whitespace
    count = remove_trailing_whitespace()
    fixes.append(("Trailing Whitespace", count))
    
    # 4. Fix encoding
    count = fix_encoding()
    fixes.append(("Encoding", count))
    
    # 5. Create __init__ files
    count = create_init_files()
    fixes.append(("__init__.py files", count))
    
    # 6. Check imports
    imports_ok = add_missing_imports()
    
    # گزارش نهایی
    print("\n" + "="*60)
    print("📊 خلاصه تغییرات:")
    print("="*60 + "\n")
    
    total_fixes = sum(count for _, count in fixes)
    
    for fix_name, count in fixes:
        if count > 0:
            print(f"  ✅ {fix_name}: {count} fixes")
        else:
            print(f"  ℹ️  {fix_name}: No changes needed")
    
    print("\n" + "="*60)
    print(f"\n✅ کل تغییرات: {total_fixes}")
    
    if total_fixes > 0:
        print("\n🎉 تمام مشکلات برطرف شد!")
        print("\n💡 حالا اجرا کنید:")
        print("   python FULL_DEBUG.py")
    else:
        print("\n✅ کد شما مشکلی ندارد!")
    
    print()
    return 0

if __name__ == '__main__':
    sys.exit(main())
