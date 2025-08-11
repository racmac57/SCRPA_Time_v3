#!/usr/bin/env python3
"""
Reference Integration Functions for SCRPA Data Processing
Handles geocoding, zone/grid lookups, and other reference data integrations.
"""

import pandas as pd
import numpy as np
import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)

class NJGeocodingService:
    """NJ State Geocoding Service Integration"""
    
    def __init__(self, service_url: str = None, api_key: str = None):
        self.service_url = service_url or "https://geocoding.nj.gov/geocode"
        self.api_key = api_key
        self.cache = {}  # Simple in-memory cache
        
    def parse_address(self, address: str) -> Dict[str, str]:
        """Parse address into components"""
        if pd.isna(address):
            return {}
            
        # Basic address parsing
        parts = address.split(',')
        result = {}
        
        if len(parts) >= 1:
            result['street'] = parts[0].strip()
        if len(parts) >= 2:
            result['city'] = parts[1].strip()
        if len(parts) >= 3:
            result['state'] = parts[2].strip()
        if len(parts) >= 4:
            result['zip'] = parts[3].strip()
            
        return result
    
    def validate_address(self, address: str) -> Dict[str, Any]:
        """Validate address format and components"""
        parsed = self.parse_address(address)
        
        validation = {
            'is_valid': True,
            'issues': [],
            'standardized': address
        }
        
        # Check for required components
        if not parsed.get('street'):
            validation['is_valid'] = False
            validation['issues'].append('Missing street address')
            
        if not parsed.get('city'):
            validation['is_valid'] = False
            validation['issues'].append('Missing city')
            
        # Check for NJ addresses
        if parsed.get('state') and parsed['state'].upper() not in ['NJ', 'NEW JERSEY']:
            validation['issues'].append('Address not in New Jersey')
            
        # Standardize format
        if validation['is_valid']:
            standardized_parts = []
            if parsed.get('street'):
                standardized_parts.append(parsed['street'].title())
            if parsed.get('city'):
                standardized_parts.append(parsed['city'].title())
            if parsed.get('state'):
                standardized_parts.append('NJ')
            if parsed.get('zip'):
                standardized_parts.append(parsed['zip'])
                
            validation['standardized'] = ', '.join(standardized_parts)
            
        return validation
    
    def geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode a single address"""
        # Check cache first
        if address in self.cache:
            return self.cache[address]
        
        # Validate address first
        validation = self.validate_address(address)
        
        result = {
            'input_address': address,
            'standardized_address': validation['standardized'],
            'x_coordinate': None,
            'y_coordinate': None,
            'accuracy': None,
            'status': 'FAILED',
            'error_message': None
        }
        
        if not validation['is_valid']:
            result['error_message'] = '; '.join(validation['issues'])
            self.cache[address] = result
            return result
        
        try:
            # This would be the actual geocoding API call
            # For now, returning mock coordinates for Hackensack addresses
            if 'hackensack' in address.lower():
                # Mock coordinates for Hackensack, NJ area
                result.update({
                    'x_coordinate': -74.0431,  # Longitude
                    'y_coordinate': 40.8859,   # Latitude
                    'accuracy': 'STREET_LEVEL',
                    'status': 'SUCCESS'
                })
            else:
                result['error_message'] = 'Address not found in NJ geocoding service'
                
        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"Geocoding failed for address '{address}': {e}")
        
        # Cache the result
        self.cache[address] = result
        return result
    
    def batch_geocode(self, addresses: List[str]) -> List[Dict[str, Any]]:
        """Geocode multiple addresses"""
        results = []
        for address in addresses:
            results.append(self.geocode_address(address))
        return results

class ZoneGridService:
    """Zone and Grid lookup service"""
    
    def __init__(self, lookup_data: pd.DataFrame = None):
        self.lookup_data = lookup_data if lookup_data is not None else pd.DataFrame()
        self.address_cache = {}
        
    def normalize_address(self, address: str) -> str:
        """Normalize address for consistent matching"""
        if pd.isna(address):
            return ""
            
        # Convert to string and clean
        addr = str(address).strip().upper()
        
        # Replace common patterns
        replacements = {
            ' & ': ' / ',
            ' AND ': ' / ',
            'STREET': 'ST',
            'AVENUE': 'AVE',
            'ROAD': 'RD',
            'DRIVE': 'DR',
            'COURT': 'CT',
            'PLACE': 'PL',
            'BOULEVARD': 'BLVD',
            'LANE': 'LN',
            'CIRCLE': 'CIR'
        }
        
        for old, new in replacements.items():
            addr = addr.replace(old, new)
            
        return addr
    
    def lookup_zone_grid(self, address: str) -> Dict[str, Any]:
        """Look up zone and grid for an address"""
        if address in self.address_cache:
            return self.address_cache[address]
        
        result = {
            'input_address': address,
            'normalized_address': self.normalize_address(address),
            'grid': None,
            'zone': None,
            'pd_zone': None,
            'match_status': 'NOT_FOUND'
        }
        
        if self.lookup_data.empty:
            result['match_status'] = 'NO_LOOKUP_DATA'
            self.address_cache[address] = result
            return result
        
        normalized = result['normalized_address']
        
        # Try exact match first
        exact_matches = self.lookup_data[
            self.lookup_data['CrossStreetName'].str.upper() == normalized
        ]
        
        if not exact_matches.empty:
            match = exact_matches.iloc[0]
            result.update({
                'grid': match.get('Grid'),
                'zone': match.get('Zone'),
                'pd_zone': match.get('PDZone'),
                'match_status': 'EXACT_MATCH'
            })
        else:
            # Try partial match
            partial_matches = self.lookup_data[
                self.lookup_data['CrossStreetName'].str.contains(normalized.split()[0], na=False, case=False)
            ]
            
            if not partial_matches.empty:
                match = partial_matches.iloc[0]
                result.update({
                    'grid': match.get('Grid'),
                    'zone': match.get('Zone'),
                    'pd_zone': match.get('PDZone'),
                    'match_status': 'PARTIAL_MATCH'
                })
        
        self.address_cache[address] = result
        return result
    
    def batch_lookup(self, addresses: List[str]) -> List[Dict[str, Any]]:
        """Batch lookup for multiple addresses"""
        results = []
        for address in addresses:
            results.append(self.lookup_zone_grid(address))
        return results

class CallTypeService:
    """Call Type and Response Type lookup service"""
    
    def __init__(self, calltype_data: pd.DataFrame = None):
        self.calltype_data = calltype_data if calltype_data is not None else pd.DataFrame()
        self.incident_cache = {}
        
    def lookup_response_type(self, incident_type: str) -> Dict[str, Any]:
        """Look up response type for incident type"""
        if incident_type in self.incident_cache:
            return self.incident_cache[incident_type]
        
        result = {
            'incident_type': incident_type,
            'response_type': None,
            'category': None,
            'priority': None,
            'match_status': 'NOT_FOUND'
        }
        
        if self.calltype_data.empty:
            result['match_status'] = 'NO_LOOKUP_DATA'
            self.incident_cache[incident_type] = result
            return result
        
        # Try exact match
        exact_matches = self.calltype_data[
            self.calltype_data['Incident'].str.upper() == str(incident_type).upper()
        ]
        
        if not exact_matches.empty:
            match = exact_matches.iloc[0]
            result.update({
                'response_type': match.get('Response Type'),
                'category': match.get('Category Type'),
                'match_status': 'EXACT_MATCH'
            })
        else:
            # Try partial match
            partial_matches = self.calltype_data[
                self.calltype_data['Incident'].str.contains(str(incident_type), na=False, case=False)
            ]
            
            if not partial_matches.empty:
                match = partial_matches.iloc[0]
                result.update({
                    'response_type': match.get('Response Type'),
                    'category': match.get('Category Type'),
                    'match_status': 'PARTIAL_MATCH'
                })
        
        # Determine priority based on response type
        if result['response_type']:
            priority_map = {
                'emergency': 'HIGH',
                'urgent': 'MEDIUM',
                'routine': 'LOW'
            }
            result['priority'] = priority_map.get(result['response_type'].lower(), 'MEDIUM')
        
        self.incident_cache[incident_type] = result
        return result

class ArcGISIntegration:
    """ArcGIS/ArcPy integration for spatial operations"""
    
    def __init__(self):
        self.arcpy_available = False
        self.spatial_reference = None
        
        try:
            import arcpy
            self.arcpy = arcpy
            self.arcpy_available = True
            # Set spatial reference to NJ State Plane (feet)
            self.spatial_reference = arcpy.SpatialReference(2900)
            logger.info("ArcPy is available and initialized")
        except ImportError:
            logger.warning("ArcPy is not available - spatial operations will be limited")
    
    def create_point_features(self, coordinates_df: pd.DataFrame, output_path: str) -> bool:
        """Create point features from coordinates"""
        if not self.arcpy_available:
            logger.warning("ArcPy not available - cannot create point features")
            return False
        
        try:
            # Create feature class
            self.arcpy.CreateFeatureclass_management(
                os.path.dirname(output_path),
                os.path.basename(output_path),
                "POINT",
                spatial_reference=self.spatial_reference
            )
            
            # Add fields
            fields_to_add = [
                ("ADDRESS", "TEXT", "", "", 255),
                ("CASE_NUMBER", "TEXT", "", "", 50),
                ("INCIDENT_TYPE", "TEXT", "", "", 100)
            ]
            
            for field_name, field_type, field_precision, field_scale, field_length in fields_to_add:
                self.arcpy.AddField_management(output_path, field_name, field_type, 
                                             field_precision, field_scale, field_length)
            
            # Insert points
            with self.arcpy.da.InsertCursor(output_path, ["SHAPE@", "ADDRESS", "CASE_NUMBER", "INCIDENT_TYPE"]) as cursor:
                for _, row in coordinates_df.iterrows():
                    if pd.notna(row.get('x_coordinate')) and pd.notna(row.get('y_coordinate')):
                        point = self.arcpy.Point(row['x_coordinate'], row['y_coordinate'])
                        point_geometry = self.arcpy.PointGeometry(point, self.spatial_reference)
                        
                        cursor.insertRow([
                            point_geometry,
                            row.get('address', ''),
                            row.get('case_number', ''),
                            row.get('incident_type', '')
                        ])
            
            logger.info(f"Created point features: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create point features: {e}")
            return False
    
    def buffer_analysis(self, input_features: str, buffer_distance: str, output_path: str) -> bool:
        """Perform buffer analysis on features"""
        if not self.arcpy_available:
            return False
        
        try:
            self.arcpy.Buffer_analysis(input_features, output_path, buffer_distance)
            logger.info(f"Buffer analysis completed: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Buffer analysis failed: {e}")
            return False

class ReferenceDataIntegrator:
    """Main class for integrating all reference data services"""
    
    def __init__(self, reference_data_path: str):
        self.reference_path = reference_data_path
        
        # Initialize services
        self.geocoding_service = NJGeocodingService()
        self.zone_grid_service = None
        self.calltype_service = None
        self.arcgis_integration = ArcGISIntegration()
        
        # Load reference data
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load all reference data"""
        try:
            # Load CallType categories
            calltype_path = os.path.join(self.reference_path, "CallType_Categories.xlsx")
            if os.path.exists(calltype_path):
                calltype_data = pd.read_excel(calltype_path)
                self.calltype_service = CallTypeService(calltype_data)
                logger.info(f"Loaded {len(calltype_data)} call type categories")
            
            # Load zone/grid data
            zone_grid_path = os.path.join(self.reference_path, "zone_grid_data")
            if os.path.exists(zone_grid_path):
                import glob
                lookup_files = glob.glob(os.path.join(zone_grid_path, "*.xlsx"))
                lookup_files = [f for f in lookup_files if "master" not in os.path.basename(f).lower()]
                
                if lookup_files:
                    dfs = [pd.read_excel(f) for f in lookup_files]
                    combined_lookup = pd.concat(dfs, ignore_index=True)
                    combined_lookup = combined_lookup.drop_duplicates()
                    self.zone_grid_service = ZoneGridService(combined_lookup)
                    logger.info(f"Loaded {len(combined_lookup)} zone/grid lookup records")
                    
        except Exception as e:
            logger.error(f"Failed to load reference data: {e}")
    
    def enhance_dataset(self, df: pd.DataFrame, 
                       address_col: str = None,
                       incident_col: str = None,
                       case_number_col: str = None) -> pd.DataFrame:
        """Enhance dataset with all reference data"""
        enhanced_df = df.copy()
        
        # Geocoding enhancement
        if address_col and address_col in enhanced_df.columns:
            logger.info("Adding geocoding data...")
            addresses = enhanced_df[address_col].dropna().unique()
            geocoding_results = self.geocoding_service.batch_geocode(addresses)
            
            # Create geocoding lookup
            geocoding_df = pd.DataFrame(geocoding_results)
            geocoding_lookup = geocoding_df.set_index('input_address')
            
            # Merge geocoding results
            enhanced_df = enhanced_df.merge(
                geocoding_lookup[['x_coordinate', 'y_coordinate', 'accuracy', 'status']],
                left_on=address_col, right_index=True, how='left', suffixes=('', '_geo')
            )
        
        # Zone/Grid enhancement
        if self.zone_grid_service and address_col and address_col in enhanced_df.columns:
            logger.info("Adding zone/grid data...")
            addresses = enhanced_df[address_col].dropna().unique()
            zone_results = self.zone_grid_service.batch_lookup(addresses)
            
            # Create zone/grid lookup
            zone_df = pd.DataFrame(zone_results)
            zone_lookup = zone_df.set_index('input_address')
            
            # Merge zone/grid results
            enhanced_df = enhanced_df.merge(
                zone_lookup[['grid', 'zone', 'pd_zone', 'match_status']],
                left_on=address_col, right_index=True, how='left', suffixes=('', '_lookup')
            )
        
        # Call type enhancement
        if self.calltype_service and incident_col and incident_col in enhanced_df.columns:
            logger.info("Adding call type data...")
            incidents = enhanced_df[incident_col].dropna().unique()
            calltype_results = [self.calltype_service.lookup_response_type(inc) for inc in incidents]
            
            # Create call type lookup
            calltype_df = pd.DataFrame(calltype_results)
            calltype_lookup = calltype_df.set_index('incident_type')
            
            # Merge call type results
            enhanced_df = enhanced_df.merge(
                calltype_lookup[['response_type', 'category', 'priority']],
                left_on=incident_col, right_index=True, how='left', suffixes=('', '_calltype')
            )
        
        logger.info(f"Dataset enhancement completed: {enhanced_df.shape}")
        return enhanced_df
    
    def export_to_arcgis(self, df: pd.DataFrame, output_path: str, 
                        x_col: str = 'x_coordinate', y_col: str = 'y_coordinate') -> bool:
        """Export enhanced data to ArcGIS feature class"""
        if not self.arcgis_integration.arcpy_available:
            logger.warning("ArcGIS integration not available")
            return False
        
        # Filter records with valid coordinates
        valid_coords = df.dropna(subset=[x_col, y_col])
        
        if valid_coords.empty:
            logger.warning("No valid coordinates found for ArcGIS export")
            return False
        
        return self.arcgis_integration.create_point_features(valid_coords, output_path)

def main():
    """Test the reference integration functions"""
    base_path = r"C:\Users\carucci_r\OneDrive - City of Hackensack\01_DataSources\SCRPA_Time_v2"
    reference_path = os.path.join(base_path, "10_Refrence_Files")
    
    # Initialize integrator
    integrator = ReferenceDataIntegrator(reference_path)
    
    # Test with sample data
    sample_data = pd.DataFrame({
        'case_number': ['25-000813', '25-002564'],
        'address': ['309 Lookout Avenue, Hackensack, NJ, 07601', '135 First Street, Hackensack, NJ, 07601'],
        'incident_type': ['Theft', 'Assault']
    })
    
    # Enhance the sample data
    enhanced = integrator.enhance_dataset(
        sample_data,
        address_col='address',
        incident_col='incident_type',
        case_number_col='case_number'
    )
    
    print("Enhanced sample data:")
    print(enhanced)
    
    return enhanced

if __name__ == "__main__":
    main()