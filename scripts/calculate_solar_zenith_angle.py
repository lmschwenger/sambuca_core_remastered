import numpy as np
from datetime import datetime, timezone
import math


def calculate_solar_zenith_angle(latitude, longitude, timestamp):
    """
    Calculate the solar zenith angle at a specific location and time.

    Parameters:
    -----------
    latitude : float
        Latitude in decimal degrees (-90 to 90).
    longitude : float
        Longitude in decimal degrees (-180 to 180).
    timestamp : datetime object or string
        Date and time when the satellite image was captured.
        If string, format should be 'YYYY-MM-DD HH:MM:SS'

    Returns:
    --------
    float
        Solar zenith angle in degrees.
    """
    # Convert string timestamp to datetime object if needed
    if isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    # Ensure datetime is timezone aware and in UTC
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    # Calculate day of year (DOY)
    doy = timestamp.timetuple().tm_yday

    # Calculate decimal hour
    decimal_hour = timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600

    # Convert latitude and longitude to radians
    lat_rad = math.radians(latitude)
    lng_rad = math.radians(longitude)

    # Calculate the declination angle (radians)
    # Solar declination using Spencer's formula
    declination = 0.006918 - 0.399912 * math.cos(2 * math.pi * doy / 365) + 0.070257 * math.sin(
        2 * math.pi * doy / 365) - \
                  0.006758 * math.cos(4 * math.pi * doy / 365) + 0.000907 * math.sin(4 * math.pi * doy / 365) - \
                  0.002697 * math.cos(6 * math.pi * doy / 365) + 0.00148 * math.sin(6 * math.pi * doy / 365)

    # Calculate equation of time (in minutes)
    eot = 229.18 * (0.000075 + 0.001868 * math.cos((2 * math.pi * doy) / 365) - 0.032077 * math.sin(
        (2 * math.pi * doy) / 365) - \
                    0.014615 * math.cos((4 * math.pi * doy) / 365) - 0.040849 * math.sin((4 * math.pi * doy) / 365))

    # Calculate solar time offset (minutes)
    time_offset = eot + 4 * longitude  # 4 minutes per degree longitude

    # Calculate solar time (hours)
    solar_time = decimal_hour + time_offset / 60
    while solar_time > 24:
        solar_time -= 24
    while solar_time < 0:
        solar_time += 24

    # Calculate hour angle (radians)
    hour_angle = math.radians(15 * (solar_time - 12))

    # Calculate solar zenith angle (radians)
    solar_zenith_rad = math.acos(math.sin(lat_rad) * math.sin(declination) +
                                 math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle))

    # Convert to degrees
    solar_zenith_deg = math.degrees(solar_zenith_rad)

    return solar_zenith_deg


def main():
    """
    Example usage of the solar zenith angle calculator.
    """
    # Example: Calculate solar zenith angle for a specific location and time
    latitude = 37.7749  # San Francisco, CA
    longitude = -122.4194
    timestamp = datetime(2025, 5, 7, 12, 0, 0, tzinfo=timezone.utc)  # Noon UTC on May 7, 2025

    zenith_angle = calculate_solar_zenith_angle(latitude, longitude, timestamp)
    print(f"Solar zenith angle: {zenith_angle:.2f} degrees")

    # Example with string input
    timestamp_str = "2025-05-07 12:00:00"
    zenith_angle = calculate_solar_zenith_angle(latitude, longitude, timestamp_str)
    print(f"Solar zenith angle (from string): {zenith_angle:.2f} degrees")

    # Calculate for a satellite image with metadata
    print("\nExample with satellite image metadata:")
    image_metadata = {
        "capture_time": "2025-05-07 10:30:19",
        "capture_location": {
            "latitude": 56.7047,  # New York City
            "longitude": 11.5071
        }
    }

    zenith_angle = calculate_solar_zenith_angle(
        image_metadata["capture_location"]["latitude"],
        image_metadata["capture_location"]["longitude"],
        image_metadata["capture_time"]
    )

    print(
        f"Location: {image_metadata['capture_location']['latitude']}, {image_metadata['capture_location']['longitude']}")
    print(f"Capture time: {image_metadata['capture_time']}")
    print(f"Solar zenith angle: {zenith_angle:.2f} degrees")


if __name__ == "__main__":
    main()