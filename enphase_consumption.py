"""
Legacy wrapper for enphase_consumption.py.
Redirects to the unified, single-query enphase_export.py module.
"""
import asyncio
from enphase_export import main

if __name__ == "__main__":
    asyncio.run(main())
