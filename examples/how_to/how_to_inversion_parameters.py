from sambuca.core.inversion import InversionParameters


inv_params = InversionParameters(
    chl=(0.1, 3),
    depth=(0, 10), # If we set a range, it will be estimated through inversion
    fixed_cdom = 0.001  # Fixed CDOM value, not a range -- this is a constant value for the inversion
)

print(f"Default Inversion Parameters: {inv_params}")


print(f"chl range: {inv_params.chl}")
print(f"Fixed cdom: {inv_params.fixed_cdom}")
print(f"nap: {inv_params.nap} ")
