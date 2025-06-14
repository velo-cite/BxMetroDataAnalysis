from urllib.error import HTTPError

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as pl
import numpy as np
import pandas as pd
from dotenv import dotenv_values
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely.geometry import Polygon
from tqdm import tqdm

pl.ion()
config = dotenv_values(".env.local")

def main(date_range_start: str,
        date_range_end: str,
        bus_line_id: tuple[str]=None,
        bounding_box: tuple=None,
        vmax: float=None):

    '''
    Affiche les vitesses des bus de la Metropole de Bordeaux.

    Parameters:
        date_range_start (str): La date de début de la plage de dates au format ISO 8601.
        date_range_end (str): La date de fin de la plage de dates au format ISO 8601.
        bus_line_id (str, optional): L'ID de la ligne de bus à analyser. Par défaut, None.
        bounding_box (tuple, optional): La bounding box définissant la zone géographique à analyser. Par défaut, None.
    '''

    BX_METRO_DATASET = "sv_vehic_p"
    CRS_STRING = "epsg:4326"
    BASE_URL = fr"https://data.bordeaux-metropole.fr/geojson/features/{BX_METRO_DATASET}?crs={CRS_STRING}"
    BXMETRO_API_KEY = config['BXMETRO_API_KEY']
    DATA_QUERY_FREQUENCY = 10 # en secondes

    if bus_line_id is not None:
        filter = f'{{"rs_sv_ligne_a":{{"$in":[{",".join(str(v) for v in bus_line_id)}]}}}}'
    else:
        filter = "{}"

    backintimes = pd.date_range(date_range_start, date_range_end, freq=f"{DATA_QUERY_FREQUENCY}s")
    df_bus  = pd.DataFrame()

    pbar = tqdm(backintimes)
    for backintime in pbar:
        pbar.set_description(f"{backintime.isoformat()}")
        url = f"{BASE_URL}&backintime={backintime.isoformat()}&filter={filter}&key={BXMETRO_API_KEY}"
        delta_t = pd.Timedelta(DATA_QUERY_FREQUENCY, "seconds")
        try:
            df = gpd.read_file(url)
            df = df.to_crs(epsg=3857)
            df_bus_single = df.copy()
            df_bus_single = df_bus_single.loc[
                (
                    (
                        pd.to_datetime(backintime).tz_localize("Europe/Paris")
                        - pd.to_datetime(df_bus_single["mdate"], utc=True).dt.tz_convert(
                            "Europe/Paris"
                        )
                    )
                    < delta_t
                )
            ]
            df_bus = pd.concat([df_bus, df_bus_single], ignore_index=True)
        except HTTPError:
            print("HTTPError: HTTP Error 502: Proxy Error")

    if bounding_box:
        lat_min, lat_max, lon_min, lon_max = bounding_box
        lon_point_list = [lon_min, lon_max, lon_max, lon_min]
        lat_point_list = [lat_min, lat_min, lat_max, lat_max]
        polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
        crs = {"init": "epsg:3857"}
        polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
        df_bus = df_bus.sjoin(polygon)

    df_bus = df_bus.drop_duplicates()

    # Plotting
    vitesse = df_bus["vitesse"].values
    pl.figure()
    pl.hist(vitesse[np.nonzero(vitesse)], bins=25)
    pl.xlabel("Vitesse [km/h]")
    pl.ylabel("Nombre de mesures")
    pl.title("Distribution des vitesses des vehicules")

    pl.figure()
    pl.hist(vitesse[np.nonzero(vitesse)], bins=25, cumulative=True, density=True)
    pl.xlabel("Vitesse [km/h]")
    pl.ylabel("Nombre de mesures")
    pl.title("Distribution cumulée des vitesses des vehicules")

    fig, ax = pl.subplots(1, 1)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    df_bus.plot(column="vitesse", cmap="viridis", legend=True, ax=ax, cax=cax)
    df_bus.loc[df_bus["vitesse"] > 30].plot(facecolor="none", edgecolor="red", ax=ax)
    ctx.add_basemap(ax, zoom=17, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_title("Distribution des vitesses des vehicules")
    return df_bus

if __name__ == "__main__":
    date_range_start = "2025-06-13T17:25:00"
    date_range_end = "2025-06-13T17:35:00"
    # bounding_box
    # lat_min, lat_max, lon_min, lon_max
    bounding_box = [5597637, 5598470,-65827, -64165]
    # bus_line_id
    # Utiliser la clé GID du jeu de donnée: https://opendata.bordeaux-metropole.fr/explore/dataset/sv_ligne_a/table/
    bus_line_id = (104,)
    #
    df_bus = main(date_range_start, date_range_end, bus_line_id, bounding_box, vmax=30)
