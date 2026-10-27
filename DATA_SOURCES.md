# Data sources and provenance

This file distinguishes project-level sources from direct file-download
provenance. The URLs below are provided by the project brief. The extracted
notebooks do not contain source URLs, and the CSV files do not include download
receipts or full source metadata. Verify the exact product, time range, and
download method before making a more specific provenance claim.

## Sources identified for the project

| Source | URL supplied in the project brief | Local data relationship / verification status |
|---|---|---|
| SanctSound Stellwagen Bank portal | https://sanctsound.ioos.us/s_sbnms.html | Project-level source reference. The local files are named for SanctSound SB01 deployments, but the exact download steps are not recorded. |
| NOAA Passive Acoustic Data Archive | https://www.ncei.noaa.gov/products/passive-acoustic-data | Archive-level reference for passive acoustic products. Exact accession/download metadata is not present locally. |
| Hourly one-third-octave sound levels | https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaaSanctSound_SB01_13_TOL_1h.graph | The acoustic CSV contains `noaaSanctSound_SB01_*_TOL_1h.csv` source-file values and 33 frequency bands. The exact download request is not recorded. |
| Humpback-whale presence example | https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaaSanctSound_SB01_01_humpbackwhale_1d.html | A matching daily NetCDF filename exists in the extracted animal raw directory. Exact download steps are not recorded. |
| Vessel-detection example | https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaaSanctSound_SB01_18_ships.html | Hourly vessel observations are present in `ships_hourly.csv`; this particular product URL is an example, not independently verified as the source for every row. |
| NOAA National Data Buoy Center | https://www.ndbc.noaa.gov/ | Organization-level reference for weather/ocean observations. Exact station data request is not recorded. |
| NDBC Station 44098 | https://www.ndbc.noaa.gov/station_page.php?station=44098 | Weather table includes wave fields suffixed `_44098`; the exact extraction method and variable units still need to be recorded. |

## Additional products to verify

The animal raw filenames identify 105 deployment/species NetCDF files covering
Atlantic cod, blue whale, dolphins, fin whale, humpback whale, minke whale,
north Atlantic right whale, and sei whale. Filenames also indicate daily (`1d`)
and hourly (`1h`) products for some species. The exact ERDDAP URL for every
animal/deployment combination is not present in the repository.

Record a source URL only after checking it against a file's metadata, a
download log, the original notebook, or the source portal. For each dataset,
the team should capture the direct URL, retrieval date, time zone, units,
license/distribution terms, and any transformations applied. Do not infer units
or fill missing source details from a similar product.
