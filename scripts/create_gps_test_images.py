"""
Create test images with GPS EXIF data for Indian locations.
This script generates sample images with embedded GPS coordinates.
"""
import os
from PIL import Image
import piexif
from io import BytesIO

def decimal_to_dms(decimal_degree):
    """Convert decimal degrees to degrees, minutes, seconds format for EXIF."""
    is_positive = decimal_degree >= 0
    decimal_degree = abs(decimal_degree)
    
    degrees = int(decimal_degree)
    minutes_decimal = (decimal_degree - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    # EXIF format: (numerator, denominator) for each component
    return (
        (degrees, 1),
        (minutes, 1),
        (int(seconds * 100), 100)  # Store seconds with 2 decimal precision
    )

def create_image_with_gps(output_path, latitude, longitude, altitude=None, location_name=""):
    """Create a test image with GPS EXIF data."""
    try:
        # Create a simple colored image (640x480)
        img = Image.new('RGB', (640, 480), color=(73, 109, 137))
        
        # Add some text to the image
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # Draw location info on image
        text = f"GPS Test Image\n{location_name}\nLat: {latitude:.4f}\nLon: {longitude:.4f}"
        draw.text((20, 20), text, fill=(255, 255, 255))
        
        # Prepare GPS data
        lat_dms = decimal_to_dms(latitude)
        lon_dms = decimal_to_dms(longitude)
        
        lat_ref = 'N' if latitude >= 0 else 'S'
        lon_ref = 'E' if longitude >= 0 else 'W'
        
        # Create GPS IFD
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: lat_ref,
            piexif.GPSIFD.GPSLatitude: lat_dms,
            piexif.GPSIFD.GPSLongitudeRef: lon_ref,
            piexif.GPSIFD.GPSLongitude: lon_dms,
        }
        
        # Add altitude if provided
        if altitude is not None:
            gps_ifd[piexif.GPSIFD.GPSAltitude] = (int(altitude * 10), 10)
            gps_ifd[piexif.GPSIFD.GPSAltitudeRef] = 0  # 0 = above sea level
        
        # Create EXIF data
        exif_dict = {
            "GPS": gps_ifd,
            "0th": {
                piexif.ImageIFD.Make: "AEGIS Test",
                piexif.ImageIFD.Model: "GPS Test Generator",
                piexif.ImageIFD.Software: "AEGIS Module 6",
            }
        }
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save image with EXIF data
        img.save(output_path, "jpeg", exif=exif_bytes, quality=95)
        
        print(f"✓ Created: {output_path}")
        print(f"  Location: {location_name}")
        print(f"  GPS: {latitude:.6f}, {longitude:.6f}")
        if altitude:
            print(f"  Altitude: {altitude}m")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating {output_path}: {e}")
        return False

def main():
    """Generate test images for various Indian locations."""
    
    # Create output directory
    output_dir = "test_images_gps"
    os.makedirs(output_dir, exist_ok=True)
    
    # Indian locations with GPS coordinates
    # Format: (filename, latitude, longitude, altitude, location_name)
    locations = [
        # Major cities
        ("delhi_india_gate.jpg", 28.6129, 77.2295, 216, "India Gate, New Delhi"),
        ("mumbai_gateway.jpg", 18.9220, 72.8347, 14, "Gateway of India, Mumbai"),
        ("bangalore_vidhana_soudha.jpg", 12.9791, 77.5913, 920, "Vidhana Soudha, Bangalore"),
        ("kolkata_victoria.jpg", 22.5448, 88.3426, 9, "Victoria Memorial, Kolkata"),
        ("chennai_marina.jpg", 13.0499, 80.2824, 7, "Marina Beach, Chennai"),
        
        # Strategic locations
        ("jaisalmer_fort.jpg", 26.9124, 70.9167, 229, "Jaisalmer Fort, Rajasthan"),
        ("leh_ladakh.jpg", 34.1526, 77.5771, 3524, "Leh, Ladakh (High Altitude)"),
        ("kargil_drass.jpg", 34.4253, 75.7619, 3230, "Drass, Kargil (Cold Desert)"),
        ("siachen_base.jpg", 35.4215, 77.1025, 5400, "Siachen Region (Glacier)"),
        
        # Border areas
        ("wagah_border.jpg", 31.6045, 74.5725, 221, "Wagah Border, Punjab"),
        ("tawang_arunachal.jpg", 27.5860, 91.8590, 3048, "Tawang, Arunachal Pradesh"),
        
        # Coastal regions
        ("kochi_naval_base.jpg", 9.9674, 76.2430, 3, "Kochi, Kerala (Naval Base)"),
        ("visakhapatnam_port.jpg", 17.6868, 83.2185, 45, "Visakhapatnam Port, Andhra Pradesh"),
        
        # Central India
        ("nagpur_central.jpg", 21.1458, 79.0882, 310, "Nagpur, Maharashtra"),
        ("bhopal_upper_lake.jpg", 23.2599, 77.4126, 523, "Bhopal, Madhya Pradesh"),
    ]
    
    print("=" * 70)
    print("AEGIS MODULE 6 — GPS TEST IMAGE GENERATOR")
    print("=" * 70)
    print(f"Creating {len(locations)} test images with Indian GPS coordinates...\n")
    
    success_count = 0
    for filename, lat, lon, alt, name in locations:
        output_path = os.path.join(output_dir, filename)
        if create_image_with_gps(output_path, lat, lon, alt, name):
            success_count += 1
    
    print("=" * 70)
    print(f"COMPLETE: {success_count}/{len(locations)} images created successfully")
    print(f"Output directory: {output_dir}/")
    print("=" * 70)
    print("\nTo test:")
    print("1. Start AEGIS server: python3 app.py")
    print("2. Upload any image from test_images_gps/ folder")
    print("3. GPS panel should appear with location details")
    print("4. Click 'VIEW ON GOOGLE MAPS' to verify coordinates")

if __name__ == "__main__":
    main()
