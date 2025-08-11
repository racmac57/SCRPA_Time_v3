# 🕒 2025-01-27-22-40-00
# SCRPA_Analysis/cmd_navigation_guide
# Author: R. A. Carucci
# Purpose: Command line navigation guide for SCRPA project file management and execution

## 🚀 **Essential CMD Commands for Your SCRPA Project**

### **1. Navigate to Your Project Directory**
```cmd
cd C:\Users\carucci_r\SCRPA_LAPTOP\archive\scripts
```

### **2. See Current Directory**
```cmd
dir
```
**Shows**: All files in current folder (main.py, config.py, etc.)

### **3. Edit Config File (Fix MV Theft Pattern)**
```cmd
notepad config.py
```
**Action**: Opens config.py in Notepad to change "AUTO THEFT" to "Motor Vehicle Theft"

### **4. View File Contents (Check Settings)**
```cmd
type config.py | findstr "MV Theft"
```
**Shows**: Just the MV Theft line from config.py

### **5. Run Your SCRPA System**
```cmd
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" main.py true true true 30 false 2025_01_27
```

## 📁 **Quick Directory Navigation**

### **Move Between Key Folders**:
```cmd
# Go to main scripts folder
cd C:\Users\carucci_r\SCRPA_LAPTOP\archive\scripts

# Go to output reports folder
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports"

# Go to ArcGIS project folder  
cd C:\Users\carucci_r\SCRPA_LAPTOP\projects

# Go back one folder level
cd ..

# Go to root of C: drive
cd \
```

## 🔍 **Check Your Files**

### **List All Python Files**:
```cmd
dir *.py
```

### **Find Specific File**:
```cmd
dir config.py
dir main.py
```

### **Check Output Files**:
```cmd
dir "C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports\C05W24_2025_01_27_7Day" /s
```

## ⚡ **Quick SCRPA Workflow Commands**

### **1. Navigate to Scripts**
```cmd
cd C:\Users\carucci_r\SCRPA_LAPTOP\archive\scripts
```

### **2. Fix MV Theft Config** 
```cmd
notepad config.py
```
*Change line: `"MV Theft": "AUTO THEFT"` to `"MV Theft": "Motor Vehicle Theft"`*

### **3. Test MV Theft Only**
```cmd
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" main.py true false false 30 false 2025_01_27
```

### **4. Run Full System**
```cmd
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" main.py true true true 30 false 2025_01_27
```

### **5. Check Results**
```cmd
explorer "C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports\C05W24_2025_01_27_7Day"
```

## 🛠 **Useful CMD Shortcuts**

### **Auto-Complete**:
- Type first few letters + **TAB** (completes folder/file names)
- Example: `cd C:\Users\car` + **TAB** → `cd C:\Users\carucci_r\`

### **Command History**:
- **↑ Arrow** = Previous command
- **↓ Arrow** = Next command

### **Copy/Paste in CMD**:
- **Right-click** = Paste
- **Ctrl+C** = Copy (when text is selected)

### **Clear Screen**:
```cmd
cls
```

## 🎯 **Common SCRPA Tasks**

### **Task 1: Fix Config and Test**
```cmd
cd C:\Users\carucci_r\SCRPA_LAPTOP\archive\scripts
notepad config.py
# (Make your changes, save, close Notepad)
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" main.py true false false 30 false 2025_01_27
```

### **Task 2: Check What Files Were Created**
```cmd
dir "C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports\C05W24_2025_01_27_7Day\MV_Theft"
```

### **Task 3: Open Output Folder in Explorer**
```cmd
explorer "C:\Users\carucci_r\OneDrive - City of Hackensack\_25_SCRPA\TIME_Based\Reports\C05W24_2025_01_27_7Day"
```

## 🚨 **Emergency Commands**

### **If CMD Gets Stuck**:
- **Ctrl+C** = Stop current command
- **Ctrl+Break** = Force stop

### **If You Get Lost**:
```cmd
cd C:\Users\carucci_r\SCRPA