@echo off
setlocal
cd /d "C:\Dev\SCRPA_Time_v3"

echo == Ensure origin remote ==
git remote add origin https://github.com/racmac57/SCRPA_Time_v3.git 2>nul
git remote set-url origin https://github.com/racmac57/SCRPA_Time_v3.git

echo == Park oversized assets OUTSIDE Git tracking ==
set PARK="_large_offrepo"
if not exist %PARK% mkdir %PARK%

rem These were flagged by GitHub (adjust if paths change)
if exist "08_json\arcgis_pro_layers\Geo_Json.zip" move /y "08_json\arcgis_pro_layers\Geo_Json.zip" %PARK%>nul
if exist "10_Refrence_Files\NJ_Geocode.loz" move /y "10_Refrence_Files\NJ_Geocode.loz" %PARK%>nul
if exist "08_json\arcgis_pro_layers\Burglary_Auto\Burglary_Auto_7d.geojson" move /y "08_json\arcgis_pro_layers\Burglary_Auto\Burglary_Auto_7d.geojson" %PARK%>nul

echo == Write .gitignore (Python + build/output + giant data) ==
(
  echo # Python
  echo __pycache__/
  echo *.py[cod]
  echo *.pyo
  echo *.pyd
  echo .Python
  echo .venv/
  echo venv/
  echo env/
  echo
  echo # Editors/OS noise
  echo .vscode/
  echo .idea/
  echo desktop.ini
  echo Thumbs.db
  echo
  echo # Logs and temp
  echo *.log
  echo *.tmp
  echo .tmp.driveupload/
  echo
  echo # Project outputs / exports
  echo 03_output/
  echo logs/
  echo 05_Exports/
  echo
  echo # Known heavy data locations
  echo 08_json/arcgis_pro_layers/
  echo 10_Refrence_Files/*.loz
) > ".gitignore"

echo == Build a CLEAN history without large assets ==
git checkout --orphan clean-main
git add .
git commit -m "Initial import (large assets kept outside Git)"
git branch -M main

echo == Force-push clean main to GitHub ==
git push -f origin main

echo == Done ==
echo Oversized files were moved to %PARK% inside this folder.
echo If you need them off-site, store them in OneDrive/SharePoint and keep links in README.
pause
endlocal
