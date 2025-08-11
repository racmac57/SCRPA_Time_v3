# 🕒 2025-07-23-05-45-00
# SCRPA_Time_v2/llm_report_generator.py
# Author: R. A. Carucci
# Purpose: LLM-powered automated SCRPA report generation using local/open source models

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import json
import requests
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class SCRPAReportGenerator:
    """
    LLM-powered SCRPA report generator that creates formatted crime analysis reports
    from incident data using the exact format you provided.
    """
    
    def __init__(self, llm_config: Optional[Dict] = None):
        """Initialize report generator with LLM configuration."""
        self.llm_config = llm_config or self._get_default_llm_config()
        
        # Your exact report template
        self.report_template = """
I'm preparing a strategic-crime-reduction briefing for the Patrol Captain.  
You'll receive a list of RMS incident records with these key fields for each case:  
• Case Number  
• Incident Date & Time  
• Incident Type(s)  
• Full Address  
• Narrative  
• Vehicle Registration(s), Make(s) & Model(s) (if applicable)  
• Suspect Description(s)  
• Victim Details (gender, adult/juvenile, relationship for sexual offenses)  
• Loss Details (items and values)  
• Scene/Entry Details (point of entry, tools used, signs of force)  
• Parking/Location Context (driveway, street, lot, garage, business, etc.)  
• Grid / Zone (if available)  
• Status (Active Investigation, Cleared/Closed)

**Global instructions:**  
- **Sort** every section **chronologically** (oldest → newest).  
- **Flag** any missing or ambiguous fields as **Data Incomplete**.  
- Use `##` for section headers and `-` for bullets.  
- **Standardize** all monetary values with commas and two decimals (e.g. `$1,024.00`).  
- At the end include a **Key Takeaways & Recommendations** block with totals, hotspots, and suggested patrol focus.  
- Also provide a **summary table**:

  | Case #   | Type           | Date/Time       | Loss Total  | Status             |
  |----------|----------------|-----------------|-------------|--------------------|
  | 25-060392| Burglary–Auto  | 07/18/25 20:30  | $0.00       | Active Investigation |

---

Generate a professional SCRPA report using this exact format for the provided incident data.
"""
    
    def _get_default_llm_config(self) -> Dict:
        """Get default LLM configuration for open source models."""
        return {
            "provider": "ollama",  # Local Ollama installation
            "model": "llama3.1:8b",  # or "mistral:7b", "codellama:13b"
            "api_url": "http://localhost:11434/api/generate",
            "max_tokens": 4000,
            "temperature": 0.3,  # Lower for factual reports
            "fallback_providers": [
                {
                    "provider": "openai_compatible",
                    "api_url": "https://api.together.xyz/v1/chat/completions",
                    "model": "meta-llama/Llama-3-8b-chat-hf",
                    "api_key": None  # Set via environment
                },
                {
                    "provider": "huggingface",
                    "model": "microsoft/DialoGPT-large",
                    "api_url": "https://api-inference.huggingface.co/models/"
                }
            ]
        }
    
    def generate_scrpa_report(self, incident_data: pd.DataFrame, 
                            report_period: str = "7-Day") -> str:
        """
        Generate SCRPA report using LLM from incident data.
        
        Args:
            incident_data: DataFrame with processed incident records
            report_period: Analysis period (e.g., "7-Day", "28-Day")
            
        Returns:
            Formatted SCRPA report string
        """
        logger.info(f"🤖 Generating SCRPA report for {len(incident_data)} incidents")
        
        # Prepare incident data for LLM
        formatted_incidents = self._format_incidents_for_llm(incident_data)
        
        # Create prompt with your template
        prompt = self._build_report_prompt(formatted_incidents, report_period)
        
        # Generate report using LLM
        try:
            report = self._call_llm(prompt)
            
            # Post-process and validate report
            final_report = self._post_process_report(report, incident_data)
            
            logger.info("✅ SCRPA report generation complete")
            return final_report
            
        except Exception as e:
            logger.error(f"❌ Error generating report: {e}")
            # Fallback to template-based report
            return self._generate_fallback_report(incident_data, report_period)
    
    def _format_incidents_for_llm(self, df: pd.DataFrame) -> str:
        """Format incident data as structured text for LLM processing."""
        formatted_incidents = []
        
        for _, row in df.iterrows():
            incident_text = f"""
CASE: {row.get('case_number', 'Unknown')}
DATE_TIME: {row.get('incident_date', '')} {row.get('incident_time', '')}
TYPE: {row.get('incident_type', 'Unknown')}
ADDRESS: {row.get('address', 'Unknown')}
GRID_ZONE: {row.get('grid', 'Unknown')} / {row.get('zone', 'Unknown')}
NARRATIVE: {row.get('narrative', 'Data Incomplete')}
OFFICER: {row.get('officer', 'Unknown')}
STATUS: {row.get('case_status', 'Unknown')}
LOSS_TOTAL: {row.get('total_value_stolen', '$0.00')}
VEHICLE_INFO: {row.get('make1', '')} {row.get('model1', '')} ({row.get('registration_1', '')})
SUSPECT_DESC: {row.get('suspect_description', 'Data Incomplete')}
"""
            formatted_incidents.append(incident_text.strip())
        
        return "\n\n---\n\n".join(formatted_incidents)
    
    def _build_report_prompt(self, incidents: str, period: str) -> str:
        """Build complete prompt for LLM report generation."""
        prompt = f"""
{self.report_template}

INCIDENT DATA FOR {period} ANALYSIS:

{incidents}

Please generate a complete SCRPA report following the exact format specified above. 
Ensure all incidents are categorized properly and sorted chronologically within each section.
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API to generate report."""
        provider = self.llm_config["provider"]
        
        if provider == "ollama":
            return self._call_ollama(prompt)
        elif provider == "openai_compatible":
            return self._call_openai_compatible(prompt)
        elif provider == "huggingface":
            return self._call_huggingface(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama instance."""
        payload = {
            "model": self.llm_config["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.llm_config["temperature"],
                "num_predict": self.llm_config["max_tokens"]
            }
        }
        
        response = requests.post(
            self.llm_config["api_url"],
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _call_openai_compatible(self, prompt: str) -> str:
        """Call OpenAI-compatible API (Together AI, etc.)."""
        fallback_config = next(
            (fb for fb in self.llm_config["fallback_providers"] 
             if fb["provider"] == "openai_compatible"), 
            None
        )
        
        if not fallback_config or not fallback_config.get("api_key"):
            raise Exception("OpenAI-compatible API key not configured")
        
        headers = {
            "Authorization": f"Bearer {fallback_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": fallback_config["model"],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.llm_config["max_tokens"],
            "temperature": self.llm_config["temperature"]
        }
        
        response = requests.post(
            fallback_config["api_url"],
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API error: {response.status_code}")
    
    def _call_huggingface(self, prompt: str) -> str:
        """Call Hugging Face Inference API."""
        fallback_config = next(
            (fb for fb in self.llm_config["fallback_providers"] 
             if fb["provider"] == "huggingface"), 
            None
        )
        
        if not fallback_config:
            raise Exception("Hugging Face config not found")
        
        # Truncate prompt if too long
        max_length = 2000
        if len(prompt) > max_length:
            prompt = prompt[:max_length] + "..."
        
        api_url = fallback_config["api_url"] + fallback_config["model"]
        
        payload = {"inputs": prompt}
        
        response = requests.post(api_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            return str(result)
        else:
            raise Exception(f"Hugging Face API error: {response.status_code}")
    
    def _post_process_report(self, raw_report: str, incident_data: pd.DataFrame) -> str:
        """Post-process and validate the generated report."""
        # Clean up common LLM formatting issues
        processed = raw_report.strip()
        
        # Ensure proper case number formatting
        processed = re.sub(r'Case (\d{2}-\d{6})', r'Case \1', processed)
        
        # Ensure proper date formatting
        processed = re.sub(r'(\d{1,2}/\d{1,2}/\d{2})', self._format_date, processed)
        
        # Ensure proper monetary formatting
        processed = re.sub(r'\$(\d+)([^\d])', r'$\1.00\2', processed)
        processed = re.sub(r'\$(\d{1,3}),(\d{3})([^\d])', r'$\1,\2.00\3', processed)
        
        # Add report header if missing
        if not processed.startswith("# Strategic Crime Reduction Plan Analysis Report"):
            period_code = self._generate_period_code(incident_data)
            header = f"# Strategic Crime Reduction Plan Analysis Report - **{period_code}**\n\n"
            processed = header + processed
        
        return processed
    
    def _generate_period_code(self, df: pd.DataFrame) -> str:
        """Generate period code (like C08W29) based on incident data."""
        if df.empty:
            return "Unknown"
        
        # Get the date range
        dates = pd.to_datetime(df['incident_date'], errors='coerce').dropna()
        if dates.empty:
            return "Unknown"
        
        # Use the latest date for period code
        latest_date = dates.max()
        
        # Format as CyyWww (Crime, year, week)
        year_code = str(latest_date.year)[-2:]  # Last 2 digits of year
        week_code = f"{latest_date.week:02d}"   # Week number, zero-padded
        
        return f"C{year_code}W{week_code}"
    
    def _format_date(self, match) -> str:
        """Format date match to MM/DD/YY standard."""
        date_str = match.group(1)
        try:
            # Parse and reformat date
            parts = date_str.split('/')
            if len(parts) == 3:
                month, day, year = parts
                return f"{month.zfill(2)}/{day.zfill(2)}/{year.zfill(2)}"
        except:
            pass
        return date_str
    
    def _generate_fallback_report(self, df: pd.DataFrame, period: str) -> str:
        """Generate basic report without LLM if API fails."""
        logger.info("📋 Generating fallback report (template-based)")
        
        period_code = self._generate_period_code(df)
        
        # Group incidents by type
        by_type = df.groupby('incident_type')
        
        report_sections = []
        report_sections.append(f"# Strategic Crime Reduction Plan Analysis Report - **{period_code}**\n")
        
        section_num = 1
        
        for incident_type, group in by_type:
            report_sections.append(f"## **{section_num}. {incident_type}**\n")
            
            # Sort chronologically
            group_sorted = group.sort_values('incident_date')
            
            for _, row in group_sorted.iterrows():
                case_text = f"""**Case {row.get('case_number', 'Unknown')} | {row.get('incident_date', 'Unknown')} {row.get('incident_time', 'Unknown')} | {incident_type}**
- **Location:** {row.get('address', 'Unknown')}
- **Grid/Zone:** {row.get('grid', 'Unknown')} / {row.get('zone', 'Unknown')}
- **Officer:** {row.get('officer', 'Unknown')}
- **Status:** {row.get('case_status', 'Unknown')}
"""
                report_sections.append(case_text)
            
            section_num += 1
        
        # Add summary
        total_incidents = len(df)
        report_sections.append(f"""
---

## **Key Takeaways & Recommendations**
- **Total incidents:** {total_incidents}
- **Report period:** {period}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## **Summary Table**

| Case # | Type | Date/Time | Status |
|--------|------|-----------|---------|""")
        
        for _, row in df.iterrows():
            report_sections.append(
                f"| {row.get('case_number', 'Unknown')} | {row.get('incident_type', 'Unknown')} | "
                f"{row.get('incident_date', 'Unknown')} {row.get('incident_time', 'Unknown')} | "
                f"{row.get('case_status', 'Unknown')} |"
            )
        
        return "\n".join(report_sections)
    
    def save_report(self, report: str, output_path: Optional[str] = None) -> str:
        """Save generated report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"SCRPA_Report_{timestamp}.md"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"💾 Report saved: {output_path}")
        return str(output_path)

# Example usage and integration
def integrate_llm_with_processor():
    """Example of integrating LLM report generation with unified processor."""
    
    # Initialize components
    from unified_data_processor import UnifiedDataProcessor
    
    processor = UnifiedDataProcessor()
    report_generator = SCRPAReportGenerator()
    
    # Process data
    # cad_df = processor.process_cad_data("path/to/cad_export.xlsx")
    # rms_df = processor.process_rms_data("path/to/rms_export.xlsx")
    # combined_df = processor.combine_data_sources(cad_df, rms_df)
    
    # For demonstration, using your provided sample data
    sample_data = pd.DataFrame([
        {
            'case_number': '25-059260',
            'incident_date': '2025-07-15',
            'incident_time': '20:00',
            'incident_type': 'Burglary - Auto',
            'address': '18 Lodi Street, Hackensack, NJ',
            'grid': 'E2',
            'zone': '6',
            'officer': 'P.O. Laura Lopez-Amaya 374',
            'narrative': 'Vehicle burglary with $7,000 cash stolen',
            'case_status': 'Cleared/Closed',
            'total_value_stolen': '$7,000.00'
        }
        # Add more sample incidents...
    ])
    
    # Generate report
    report = report_generator.generate_scrpa_report(sample_data)
    
    # Save report
    report_path = report_generator.save_report(report)
    
    return report_path

if __name__ == "__main__":
    # Test the report generator
    integrate_llm_with_processor()