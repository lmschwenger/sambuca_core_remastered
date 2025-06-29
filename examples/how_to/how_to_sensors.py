from sambuca.core.sensors import S2

b01_wavelength = S2.B01.wavelength
b02_wavelength = S2.B02.wavelength

print(f"B01 Wavelength: {b01_wavelength} nm")
print(f"B01 Resolution: {S2.B01.resolution} m")
print(f"B01 Description: {S2.B01.description}")