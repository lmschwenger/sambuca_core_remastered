from sambuca.core import SIOPManager
from sambuca.core.inversion import InversionParameters
from sambuca.core.inversion import LookUpTable
from sambuca.core.sensors import S2

sensor_name = 'sentinel2'
wavelengths = [S2.B02.wavelength, S2.B03.wavelength, S2.B04.wavelength]

inv_params = InversionParameters(
    chl=(0.1, 3),
    depth=(0, 10),  # If we set a range, it will be estimated through inversion
    fixed_cdom=0.001,  # Fixed CDOM value, not a range -- this is a constant value for the inversion
    wavelengths=wavelengths
)
print(f"Default Inversion Parameters: {inv_params}")
print(f"chl range: {inv_params.chl}")
print(f"Fixed cdom: {inv_params.fixed_cdom}")
print(f"nap: {inv_params.nap} ")

sm = SIOPManager(siop_directory='../../data/siops')
sm.register_sensor(sensor_name=sensor_name, wavelengths=wavelengths)

inv_params.update_from_siop_manager(siop_manager=sm, sensor_name=sensor_name)

lut = LookUpTable(inversion_parameters=inv_params)
lut.build_table(grid_size=10)
print(f"Default LookUpTable: {lut}")

print(f"{lut.param_names = }")
print(f"{lut.grid_shape = }")

print("We now have a LookUpTable containing spectra (rrs for the input wavelengths) for all combinations of the parameters")
print(
    f"{lut.spectra_array.shape = } -->  grid_size^n_params x n_wavelengths = {lut.grid_shape[0]}^{len(lut.param_names)} x {len(wavelengths)}")
