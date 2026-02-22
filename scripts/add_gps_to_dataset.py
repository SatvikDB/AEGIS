"""
Add GPS EXIF data to existing military vehicle dataset images.
This creates realistic test scenarios where military vehicles are detected
at specific Indian locations.
"""
import os
import random
from PIL import Image
import piexif
from pathlib import Path

def decimal_to_dms(decimal_degree):
    """Convert decimal degrees to degrees, minutes, seconds format for EXIF."""
    is_positive = decimal_degree >= 0
    decimal_degree = abs(decimal_degree)
    
    degrees = int(decimal_degree)
    minutes_decimal = (decimal_degree - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    return (
        (degrees, 1),
        (minutes, 1),
        (int(seconds * 100), 100)
    )

def add_gps_to_image(input_path, output_path, latitude, longitude, altitude=None):
    """Add GPS EXIF data to an existing image."""
    try:
        # Open the image
        img = Image.open(input_path)
        
        # Try to get existing EXIF data
        try:
            exif_dict = piexif.load(img.info.get('exif', b''))
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Prepare GPS data
        lat_dms = decimal_to_dms(latitude)
        lon_dms = decimal_to_dms(longitude)
        
        lat_ref = 'N' if latitude >= 0 else 'S'
        lon_ref = 'E' if longitude >= 0 else 'W'
        
        # Create GPS IFD
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: lat_ref.encode(),
            piexif.GPSIFD.GPSLatitude: lat_dms,
            piexif.GPSIFD.GPSLongitudeRef: lon_ref.encode(),
            piexif.GPSIFD.GPSLongitude: lon_dms,
        }
        
        # Add altitude if provided
        if altitude is not None:
            gps_ifd[piexif.GPSIFD.GPSAltitude] = (int(altitude * 10), 10)
            gps_ifd[piexif.GPSIFD.GPSAltitudeRef] = 0
        
        # Update GPS data
        exif_dict["GPS"] = gps_ifd
        
        # Add metadata
        if "0th" not in exif_dict:
            exif_dict["0th"] = {}
        exif_dict["0th"][piexif.ImageIFD.Make] = b"AEGIS Surveillance"
        exif_dict["0th"][piexif.ImageIFD.Model] = b"Military Detection System"
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save with GPS data
        img.save(output_path, "jpeg", exif=exif_bytes, quality=95)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Add GPS tags to military vehicle dataset images."""
    
    # Indian military locations with strategic context
    # Format: (latitude, longitude, altitude, location_name, context)
    military_locations = [
        # Northern Border (High Priority)
        (34.1526, 77.5771, 3524, "Leh Ladakh", "High altitude military base"),
        (34.4253, 75.7619, 3230, "Kargil Drass", "Strategic border position"),
        (35.4215, 77.1025, 5400, "Siachen Glacier", "World's highest battlefield"),
        (32.7266, 74.8570, 1585, "Jammu", "Northern command area"),
        (27.5860, 91.8590, 3048, "Tawang", "Eastern border strategic point"),
        
        # Western Border
        (31.6045, 74.5725, 221, "Wagah Border", "India-Pakistan border"),
        (26.9124, 70.9167, 229, "Jaisalmer", "Desert military operations"),
        (24.5854, 73.7125, 577, "Udaipur", "Rajasthan military zone"),
        (27.0238, 74.2179, 267, "Ajmer", "Central command region"),
        
        # Eastern Border
        (25.5788, 91.8933, 920, "Shillong", "Eastern command HQ"),
        (26.1445, 91.7362, 49, "Guwahati", "Northeast strategic hub"),
        (23.1645, 92.9376, 11, "Agartala", "Border surveillance area"),
        
        # Coastal Defense (Naval)
        (9.9674, 76.2430, 3, "Kochi Naval Base", "Southern naval command"),
        (17.6868, 83.2185, 45, "Visakhapatnam", "Eastern naval command"),
        (18.9220, 72.8347, 14, "Mumbai Naval Base", "Western naval command"),
        (11.9416, 79.8083, 7, "Pondicherry Coast", "Coastal surveillance"),
        
        # Central Strategic Locations
        (28.6129, 77.2295, 216, "New Delhi", "National capital region"),
        (21.1458, 79.0882, 310, "Nagpur", "Central air command"),
        (23.2599, 77.4126, 523, "Bhopal", "Central India operations"),
        (26.8467, 80.9462, 126, "Lucknow", "Northern plains command"),
        
        # Southern Strategic
        (12.9716, 77.5946, 920, "Bangalore", "Southern command HQ"),
        (13.0827, 80.2707, 7, "Chennai", "Southern coastal defense"),
        (17.3850, 78.4867, 542, "Hyderabad", "Central southern command"),
        (15.3173, 75.7139, 640, "Hubli", "Karnataka military zone"),
        
        # Air Force Bases
        (28.5665, 77.3211, 234, "Hindon Air Base", "Delhi NCR air defense"),
        (26.7606, 75.8013, 390, "Jaipur Air Base", "Rajasthan air operations"),
        (19.0896, 72.8656, 11, "Mumbai Air Base", "Western air command"),
        (12.9500, 77.6681, 915, "Bangalore Air Base", "Southern air defense"),
    ]
    
    # Source dataset directory
    source_dir = "military-vehicle.v6i.yolov8/test/images"
    
    # Output directory
    output_dir = "military_gps_test_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all images from test set
    if not os.path.exists(source_dir):
        print(f"❌ Error: Dataset directory not found: {source_dir}")
        print("Please ensure the military vehicle dataset is in the correct location.")
        return
    
    image_files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"❌ Error: No images found in {source_dir}")
        return
    
    print("=" * 80)
    print("AEGIS MODULE 6 — ADD GPS TO MILITARY VEHICLE DATASET")
    print("=" * 80)
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Images available: {len(image_files)}")
    print(f"Locations available: {len(military_locations)}")
    print()
    
    # Select random images and assign random locations
    num_images = min(30, len(image_files))  # Create 30 test images
    selected_images = random.sample(image_files, num_images)
    
    print(f"Creating {num_images} military vehicle images with GPS tags...\n")
    
    success_count = 0
    
    for i, image_file in enumerate(selected_images, 1):
        # Pick a random location
        lat, lon, alt, loc_name, context = random.choice(military_locations)
        
        # Input and output paths
        input_path = os.path.join(source_dir, image_file)
        output_filename = f"military_{i:02d}_{loc_name.replace(' ', '_').lower()}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"[{i}/{num_images}] Processing: {image_file}")
        print(f"  Location: {loc_name} ({context})")
        print(f"  GPS: {lat:.4f}°, {lon:.4f}° @ {alt}m")
        
        if add_gps_to_image(input_path, output_path, lat, lon, alt):
            print(f"  ✓ Saved: {output_filename}")
            success_count += 1
        else:
            print(f"  ✗ Failed to process")
        print()
    
    print("=" * 80)
    print(f"COMPLETE: {success_count}/{num_images} images processed successfully")
    print(f"Output directory: {output_dir}/")
    print("=" * 80)
    print("\n📍 REALISTIC TEST SCENARIO:")
    print("These images contain actual military vehicles from your dataset,")
    print("now tagged with GPS coordinates at strategic Indian locations.")
    print("\n🎯 TO TEST:")
    print("1. Start AEGIS: python3 app.py")
    print("2. Upload any image from military_gps_test_images/")
    print("3. AEGIS will:")
    print("   - Detect the military vehicle (YOLO)")
    print("   - Show GPS location where it was 'spotted'")
    print("   - Display threat assessment")
    print("   - Provide Google Maps link")
    print("\n💡 EXAMPLE:")
    print("Upload: military_01_leh_ladakh.jpg")
    print("Result: Tank detected at Leh Ladakh (34.15°N, 77.58°E, 3524m)")
    print("        High altitude military base - Strategic border position")

if __name__ == "__main__":
    main()
