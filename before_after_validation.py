#!/usr/bin/env python3
"""
Before/After Validation Report
Compare original broken processing vs fixed column mapping
"""

import pandas as pd
from pathlib import Path

def compare_before_after():
    """Generate comprehensive before/after comparison"""
    print("=== BEFORE/AFTER VALIDATION REPORT ===")
    
    # Load the broken (before) data
    powerbi_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2\04_powerbi")
    broken_files = list(powerbi_dir.glob("*rms_data_standardized.csv"))
    
    if broken_files:
        broken_file = max(broken_files, key=lambda p: p.stat().st_mtime)
        broken_df = pd.read_csv(broken_file)
        print(f"BEFORE (Broken): {broken_file.name}")
    else:
        print("WARNING: No broken files found for comparison")
        broken_df = None
    
    # Load the fixed (after) data
    fixed_files = list(Path(".").glob("RMS_Fixed_ColumnMapping_*.csv"))
    if fixed_files:
        fixed_file = max(fixed_files, key=lambda p: p.stat().st_mtime)
        fixed_df = pd.read_csv(fixed_file)
        print(f"AFTER (Fixed): {fixed_file.name}")
    else:
        print("ERROR: No fixed files found")
        return
    
    print(f"\n=== RECORD PRESERVATION COMPARISON ===")
    if broken_df is not None:
        print(f"BEFORE: {len(broken_df)} records")
    print(f"AFTER:  {len(fixed_df)} records")
    print(f"TARGET: 140 records (raw export)")
    
    if broken_df is not None:
        record_improvement = len(fixed_df) - len(broken_df)
        if record_improvement > 0:
            print(f"IMPROVEMENT: +{record_improvement} records recovered")
        elif record_improvement == 0:
            print(f"STATUS: Same record count")
        else:
            print(f"CONCERN: {abs(record_improvement)} records lost")
    
    print(f"\n=== CRITICAL FIELD POPULATION COMPARISON ===")
    critical_fields = ['location', 'incident_type', 'incident_time', 'grid', 'post']
    
    for field in critical_fields:
        print(f"\n{field.upper()}:")
        
        if broken_df is not None and field in broken_df.columns:
            broken_count = broken_df[field].notna().sum()
            broken_pct = (broken_count / len(broken_df)) * 100
            print(f"  BEFORE: {broken_count}/{len(broken_df)} ({broken_pct:.1f}%)")
        else:
            print(f"  BEFORE: Field missing or no data")
            broken_count = 0
        
        if field in fixed_df.columns:
            fixed_count = fixed_df[field].notna().sum()
            fixed_pct = (fixed_count / len(fixed_df)) * 100
            print(f"  AFTER:  {fixed_count}/{len(fixed_df)} ({fixed_pct:.1f}%)")
            
            if broken_df is not None:
                improvement = fixed_count - broken_count
                if improvement > 0:
                    print(f"  IMPROVEMENT: +{improvement} records (+{improvement/len(fixed_df)*100:.1f}%)")
                elif improvement == 0:
                    print(f"  STATUS: No change")
                else:
                    print(f"  CONCERN: {abs(improvement)} records lost")
        else:
            print(f"  AFTER: Field missing")
    
    print(f"\n=== SAMPLE DATA COMPARISON ===")
    
    if broken_df is not None:
        print("BEFORE (Broken) Sample:")
        broken_sample = broken_df[critical_fields].head(2)
        print(broken_sample.to_string(index=False))
    
    print("\nAFTER (Fixed) Sample:")
    fixed_sample = fixed_df[critical_fields].head(2)
    print(fixed_sample.to_string(index=False))
    
    print(f"\n=== SUCCESS METRICS ===")
    
    if broken_df is not None:
        # Calculate success metrics
        total_critical_fields = len(critical_fields)
        successful_fixes = 0
        
        for field in critical_fields:
            if field in fixed_df.columns:
                fixed_count = fixed_df[field].notna().sum()
                if fixed_count > 0:  # Field now has data
                    successful_fixes += 1
        
        success_rate = (successful_fixes / total_critical_fields) * 100
        print(f"Critical fields fixed: {successful_fixes}/{total_critical_fields} ({success_rate:.1f}%)")
        
        # Record preservation success
        record_preservation = (len(fixed_df) / 140) * 100  # Against target of 140
        print(f"Record preservation: {len(fixed_df)}/140 ({record_preservation:.1f}%)")
        
        # Overall assessment
        if success_rate >= 100 and record_preservation >= 100:
            print(f"OVERALL STATUS: COMPLETE SUCCESS")
        elif success_rate >= 80 and record_preservation >= 95:
            print(f"OVERALL STATUS: SUCCESS WITH MINOR ISSUES")
        else:
            print(f"OVERALL STATUS: PARTIAL SUCCESS - REVIEW NEEDED")
    else:
        print("OVERALL STATUS: VALIDATION COMPLETE - FIXED DATA READY")

if __name__ == "__main__":
    compare_before_after()