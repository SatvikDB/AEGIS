"""
services/geo_service.py
Extract GPS coordinates from image EXIF data and reverse geocode to location name.
"""
import logging
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

log = logging.getLogger(__name__)

def _get_exif(image_path):
    """Extract EXIF data from image."""
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        exif = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value
        return exif
    except Exception as e:
        log.debug(f'Could not read EXIF: {e}')
        return None

def _get_gps_data(exif):
    """Extract GPS info from EXIF."""
    if not exif or 'GPSInfo' not in exif:
        return None
    gps_info = {}
    for key in exif['GPSInfo'].keys():
        decode = GPSTAGS.get(key, key)
        gps_info[decode] = exif['GPSInfo'][key]
    return gps_info

def _convert_to_degrees(value):
    """Convert GPS coordinates to degrees."""
    try:
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)
    except (TypeError, ValueError) as e:
        log.debug(f'Could not convert GPS value to degrees: {e}')
        return None

def _get_lat_lon(gps_info):
    """Extract lat/lon from GPS info."""
    try:
        lat = _convert_to_degrees(gps_info['GPSLatitude'])
        if lat is None:
            return None, None
        if gps_info['GPSLatitudeRef'] == 'S':
            lat = -lat
        lon = _convert_to_degrees(gps_info['GPSLongitude'])
        if lon is None:
            return None, None
        if gps_info['GPSLongitudeRef'] == 'W':
            lon = -lon
        return lat, lon
    except (KeyError, TypeError) as e:
        log.debug(f'Could not extract lat/lon: {e}')
        return None, None

def _reverse_geocode(lat, lon):
    """Get location name from coordinates using Nominatim (free)."""
    try:
        import ssl
        import certifi
        from geopy.geocoders import Nominatim
        
        # Create SSL context with certifi certificates
        ctx = ssl.create_default_context(cafile=certifi.where())
        geolocator = Nominatim(
            user_agent='aegis_geo_intel_v2',
            ssl_context=ctx
        )
        location = geolocator.reverse((lat, lon), timeout=5, language='en')
        
        if location and location.raw.get('address'):
            addr = location.raw['address']
            parts = []
            for key in ['city', 'town', 'village', 'county', 'state', 'country']:
                if key in addr and addr[key] not in parts:
                    parts.append(addr[key])
            return ', '.join(parts[:3]) if parts else location.address
        return None
    except Exception as e:
        log.warning(f'Geocoding failed: {e}')
        # Always return coordinates as fallback - never return None
        ns = 'N' if lat >= 0 else 'S'
        ew = 'E' if lon >= 0 else 'W'
        return f'{abs(lat):.4f}° {ns}, {abs(lon):.4f}° {ew}'

def extract_gps(image_path):
    """
    Extract GPS data from image and return location info.
    Returns dict with lat, lon, location_name, altitude, etc., or None if no GPS.
    """
    try:
        exif = _get_exif(image_path)
        if not exif:
            return None
        
        gps_info = _get_gps_data(exif)
        if not gps_info:
            return None
        
        lat, lon = _get_lat_lon(gps_info)
        if lat is None or lon is None:
            return None
        
        # Validate coordinates are within valid ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            log.warning(f'Invalid GPS coordinates: lat={lat}, lon={lon}')
            return None
        
        # Get location name
        location_name = _reverse_geocode(lat, lon)
        
        # Get altitude if present
        altitude = None
        if 'GPSAltitude' in gps_info:
            try:
                alt_value = gps_info['GPSAltitude']
                log.debug(f'GPSAltitude raw value: {alt_value}, type: {type(alt_value)}')
                # Try to convert to float (handles int, float, and IFDRational)
                try:
                    altitude = float(alt_value)
                    log.debug(f'Parsed altitude as float: {altitude}')
                except (TypeError, ValueError):
                    # Handle tuple/rational number (numerator/denominator)
                    if hasattr(alt_value, '__iter__') and len(alt_value) == 2:
                        altitude = float(alt_value[0]) / float(alt_value[1])
                        log.debug(f'Parsed altitude from rational: {altitude}')
            except (TypeError, ValueError, ZeroDivisionError) as e:
                log.debug(f'Could not parse altitude: {e}')
        
        log.info(f'GPS extracted: {lat:.4f}, {lon:.4f} -> {location_name}')
        
        return {
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'location_name': location_name or 'Unknown location',
            'altitude': round(altitude, 1) if altitude else None,
            'maps_link': f'https://www.google.com/maps?q={lat},{lon}',
        }
    except Exception as e:
        log.error(f'Unexpected error in extract_gps: {e}')
        return None
