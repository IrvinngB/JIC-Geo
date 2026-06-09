# DEM Sources

Place DEM raster files here. Supported sources in order of preference:

| Source | Resolution | File format | Notes |
|---|---|---|---|
| Copernicus DEM | 10m | GeoTIFF | Recommended |
| ALOS AW3D30 | 12.5m | GeoTIFF | Good alternative |
| SRTM | 30m | HGT / GeoTIFF | Fallback, noisy in dense forest |
| LiDAR / UAV | 1m | GeoTIFF | Best quality, project-specific |

## Loading a DEM into PostGIS

```bash
# Convert and load a GeoTIFF into PostGIS Raster
raster2pgsql -s 4326 -I -C -M your_dem.tif -F public.dem_10m | psql -d jicgeo

# Verify
psql jicgeo -c "SELECT rid, ST_BandNoDataValue(rast) FROM dem_10m LIMIT 1;"
```

Then register the source in the `dem_sources` table:

```sql
INSERT INTO dem_sources (name, resolution_m, priority, rast_table)
VALUES ('copernicus_10m', 10.0, 100, 'dem_10m');
```
