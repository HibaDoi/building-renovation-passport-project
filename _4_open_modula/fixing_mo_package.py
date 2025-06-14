#!/usr/bin/env python3
"""
ONE-LINER FIX FOR YOUR TEASER PROJECT
Run this once and your models will work with IBPSA!
"""

import os
import re
from pathlib import Path

# 🎯 CHANGE THIS TO YOUR PROJECT PATH
PROJECT_PATH = r"_3_Pre_Ene_Sys_Mod/output/Project"

def instant_fix():
    """Fix all files instantly"""
    
    print("🚀 INSTANT FIX STARTING...")
    
    project_path = Path(PROJECT_PATH)
    mo_files = list(project_path.rglob("*.mo"))
    
    print(f"📁 Processing {len(mo_files)} files...")
    
    # Super fast batch replacements
    replacements = [
        (r'within\s+Project\s*;', 'within ;'),
        (r'AixLib\.', 'IBPSA.'),
    ]
    
    fixed = 0
    for mo_file in mo_files:
        try:
            with open(mo_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original = content
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            if content != original:
                with open(mo_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed += 1
                
        except:
            pass
    
    print(f"✅ DONE! Fixed {fixed} files in seconds!")
    print("🎯 Now run your simulation script!")

if __name__ == "__main__":
    instant_fix()