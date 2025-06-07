# 🔐 Copernicus Marine Credentials Setup

## Overview

The Sentinel-3 data fetcher supports multiple ways to provide your Copernicus Marine credentials securely. Here are all the options:

## 🌟 **Recommended: Environment Variables**

### Option 1: Set Environment Variables (Windows)
```cmd
set COP_MARINE_USER=your_username
set COP_MARINE_PASS=your_password
```

### Option 2: Set Environment Variables (Linux/Mac)
```bash
export COP_MARINE_USER=your_username
export COP_MARINE_PASS=your_password
```

### Option 3: Add to Your Shell Profile
Add to `~/.bashrc`, `~/.zshrc`, or `~/.profile`:
```bash
export COP_MARINE_USER="your_username"
export COP_MARINE_PASS="your_password"
```

## 📄 **Using .env File**

Create a `.env` file in your project directory:
```env
COP_MARINE_USER=your_username
COP_MARINE_PASS=your_password
```

Then load it in Python:
```python
from dotenv import load_dotenv
load_dotenv()

# Now run your script
```

## 🖥️ **Command Line Options**

You can also pass credentials directly via command line:

```bash
python scripts/fetch_sentinel3_data.py \
    --aoi "11.8,56.6,12.0,56.8" \
    --date "2024-06-15" \
    --username your_username \
    --password your_password
```

## 🔄 **Using Stored Credentials**

If you've already logged in with copernicusmarine:
```bash
copernicusmarine login
```

The script will automatically use these stored credentials if no environment variables are found.

## 🧪 **Testing Your Setup**

### Check Environment Variables
```bash
python scripts/setup_credentials.py
```

### Test with Actual Data Fetch
```bash
python scripts/fetch_sentinel3_data.py \
    --aoi "11.8,56.6,12.0,56.8" \
    --date "2024-06-15" \
    --parameters chl \
    --verbose
```

## 📋 **How It Works in the Code**

The `Sentinel3Fetcher` class automatically:

1. **Checks environment variables** (`COP_MARINE_USER`, `COP_MARINE_PASS`)
2. **Sets up authentication** before each API call
3. **Falls back to stored credentials** if environment variables aren't found
4. **Provides clear error messages** if authentication fails

### Code Location

The credential handling is implemented in:
- **`__init__` method**: Loads credentials from environment
- **`setup_authentication` method**: Configures authentication
- **`fetch_data_copernicusmarine` method**: Uses credentials for API calls

```python
# In __init__
self.username = os.getenv('COP_MARINE_USER')
self.password = os.getenv('COP_MARINE_PASS')

# In setup_authentication
if self.username and self.password:
    os.environ['COPERNICUSMARINE_SERVICE_USERNAME'] = self.username
    os.environ['COPERNICUSMARINE_SERVICE_PASSWORD'] = self.password
```

## 🔒 **Security Best Practices**

### ✅ **Recommended**
- Use environment variables
- Use `.env` files (add to `.gitignore`)
- Use stored credentials (`copernicusmarine login`)

### ❌ **Not Recommended**
- Hardcoding credentials in scripts
- Passing credentials via command line in production
- Committing credentials to version control

## 🚨 **Troubleshooting**

### "No credentials found"
```
WARNING - No Copernicus Marine credentials found in environment variables
WARNING - Set COP_MARINE_USER and COP_MARINE_PASS or run: copernicusmarine login
```

**Solution**: Set environment variables or run `copernicusmarine login`

### "Authentication failed" 
**Check**:
1. Username/password are correct
2. Account is active at https://data.marine.copernicus.eu/
3. No typos in environment variable names

### "Dataset access denied"
**Check**:
1. Your account has access to ocean color datasets
2. You've accepted the license terms
3. Try logging in via web interface first

## 🎯 **Quick Setup for Anholt Test**

```bash
# 1. Set credentials
export COP_MARINE_USER=your_username
export COP_MARINE_PASS=your_password

# 2. Test credentials
python scripts/setup_credentials.py

# 3. Fetch data
python scripts/fetch_sentinel3_data.py \
    --aoi "11.8,56.6,12.0,56.8" \
    --date "2024-06-15" \
    --parameters chl nap cdom \
    --verbose
```

## 📞 **Getting Credentials**

1. **Register**: https://data.marine.copernicus.eu/register
2. **Confirm email** and **activate account**
3. **Log in** to verify access
4. **Use your login credentials** with the scripts

The same username/password you use on the Copernicus website works with the API! 🌊
