import datetime
import os
import unicodedata

import numpy as np
import pandas as pd


BASE = r"C:\Users\Batuhan\Desktop\CE 49X Files\CE49X\Week04_Matplotlib_Visualization"
LAB_DATA = os.path.join(BASE, "lab", "data")
RAW = os.path.join(LAB_DATA, "raw")
PROCESSED = os.path.join(LAB_DATA, "processed")
DOCS = os.path.join(LAB_DATA, "docs")

LEGACY_RAW = os.path.join(BASE, "data", "raw")
LEGACY_PROCESSED = os.path.join(BASE, "data", "processed")


def resolve_input_path(preferred_path: str, legacy_path: str) -> str:
    return preferred_path if os.path.exists(preferred_path) else legacy_path


def norm_key(value: str) -> str:
    text = str(value).strip()
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return "".join(ch for ch in text.upper() if ch.isalnum())


def score_0_100(series: pd.Series) -> pd.Series:
    vals = pd.Series(series, dtype="float64")
    lo, hi = vals.quantile(0.01), vals.quantile(0.99)
    vals = vals.clip(lo, hi)
    return 100 * (vals - vals.min()) / (vals.max() - vals.min() + 1e-9)


def main() -> None:
    os.makedirs(LAB_DATA, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(PROCESSED, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)

    scen_path = resolve_input_path(
        os.path.join(RAW, "ibb_deprem_senaryosu_analiz_sonuclari.csv"),
        os.path.join(LEGACY_RAW, "ibb_deprem_senaryosu_analiz_sonuclari.csv"),
    )
    pop_path = resolve_input_path(
        os.path.join(RAW, "ibb_nufus_bilgileri.xlsx"),
        os.path.join(LEGACY_RAW, "ibb_nufus_bilgileri.xlsx"),
    )
    eq_path = resolve_input_path(
        os.path.join(RAW, "afad_earthquakes_marmara.csv"),
        os.path.join(LEGACY_RAW, "afad_earthquakes_marmara.csv"),
    )
    cent_path = resolve_input_path(
        os.path.join(PROCESSED, "istanbul_district_centroids_osm.csv"),
        os.path.join(LEGACY_PROCESSED, "istanbul_district_centroids_osm.csv"),
    )

    # Scenario data
    scenario = pd.read_csv(scen_path, sep=";", encoding="cp1254")
    num_cols = [
        "cok_agir_hasarli_bina_sayisi",
        "agir_hasarli_bina_sayisi",
        "orta_hasarli_bina_sayisi",
        "hafif_hasarli_bina_sayisi",
        "can_kaybi_sayisi",
        "agir_yarali_sayisi",
        "hastanede_tedavi_sayisi",
        "hafif_yarali_sayisi",
        "dogalgaz_boru_hasari",
        "icme_suyu_boru_hasari",
        "atik_su_boru_hasari",
        "gecici_barinma",
    ]
    for col in num_cols:
        scenario[col] = pd.to_numeric(scenario[col], errors="coerce").fillna(0)
    scenario.to_csv(os.path.join(PROCESSED, "ibb_scenario_clean.csv"), index=False)

    district = scenario.groupby("ilce_adi", as_index=False)[num_cols].sum()
    district["building_metric"] = district["cok_agir_hasarli_bina_sayisi"] + district["agir_hasarli_bina_sayisi"]
    district["human_impact_metric"] = district["can_kaybi_sayisi"] + district["agir_yarali_sayisi"]
    district["district_key"] = district["ilce_adi"].map(norm_key)

    # Population data
    pop = pd.read_excel(pop_path)
    age_cols = [c for c in pop.columns if c not in ["Yıl", "İlçe", "ilce_kodu"]]
    pop["population"] = pop[age_cols].sum(axis=1)
    latest_year = int(pop["Yıl"].max())
    pop_latest = pop.loc[pop["Yıl"] == latest_year, ["İlçe", "population"]].copy()
    pop_latest["district_key"] = pop_latest["İlçe"].map(norm_key)
    pop_latest = pop_latest.groupby("district_key", as_index=False)["population"].sum()

    district = district.merge(pop_latest, on="district_key", how="left")
    district["population"] = district["population"].fillna(district["population"].median())
    district["building_per_10k"] = 10000 * district["building_metric"] / district["population"].clip(lower=1)
    district.to_csv(os.path.join(PROCESSED, "district_risk_input.csv"), index=False)

    # AFAD catalog
    eq = pd.read_csv(eq_path)
    eq["latitude"] = pd.to_numeric(eq.get("latitude"), errors="coerce")
    eq["longitude"] = pd.to_numeric(eq.get("longitude"), errors="coerce")
    eq["magnitude"] = pd.to_numeric(eq.get("magnitude"), errors="coerce")
    eq = eq.dropna(subset=["latitude", "longitude", "magnitude"])
    eq = eq.loc[eq["magnitude"] >= 3.0].copy()
    eq.to_csv(os.path.join(PROCESSED, "earthquake_catalog_clean.csv"), index=False)

    # Centroids (supplementary)
    cent = pd.read_csv(cent_path)
    cent["district_key"] = cent["ilce_adi"].map(norm_key)
    district = district.merge(cent[["district_key", "latitude", "longitude"]], on="district_key", how="left")

    # Historical seismicity near district centroids (20 km radius)
    r_earth = 6371.0
    lat1 = np.radians(district["latitude"].values)[:, None]
    lon1 = np.radians(district["longitude"].values)[:, None]
    lat2 = np.radians(eq["latitude"].values)[None, :]
    lon2 = np.radians(eq["longitude"].values)[None, :]
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    dist_km = 2 * r_earth * np.arcsin(np.minimum(1, np.sqrt(a)))
    district["historical_eq_density"] = (dist_km <= 20).sum(axis=1)

    # Proxy scoring (until legend-based geology polygons are digitized)
    district["amplification_score"] = score_0_100(district["building_per_10k"])
    district["hazard_score"] = score_0_100(district["human_impact_metric"])
    district["historical_eq_score"] = score_0_100(district["historical_eq_density"])
    district["exposure_score"] = score_0_100(district["population"])
    district["building_vuln_score"] = score_0_100(district["building_metric"])

    district["composite_risk_score"] = (
        0.35 * district["amplification_score"]
        + 0.25 * district["hazard_score"]
        + 0.15 * district["historical_eq_score"]
        + 0.15 * district["exposure_score"]
        + 0.10 * district["building_vuln_score"]
    )

    unified = pd.DataFrame(
        {
            "location_id": [f"IST_{i+1:03d}" for i in range(len(district))],
            "district": district["ilce_adi"],
            "latitude": district["latitude"],
            "longitude": district["longitude"],
            "geology_unit": "Not yet digitized from IBB microzonation legend",
            "soil_class": "Not yet digitized from IBB microzonation legend",
            "ground_type": "Proxy from IBB scenario severe-damage rate",
            "amplification_score": district["amplification_score"],
            "hazard_score": district["hazard_score"],
            "historical_eq_density": district["historical_eq_density"],
            "population": district["population"],
            "building_metric": district["building_metric"],
            "composite_risk_score": district["composite_risk_score"],
        }
    )
    unified.to_csv(os.path.join(PROCESSED, "unified_risk_schema.csv"), index=False)
    unified.sort_values("composite_risk_score", ascending=False).head(10).to_csv(
        os.path.join(PROCESSED, "top10_risk_locations.csv"), index=False
    )

    source_registry = pd.DataFrame(
        [
            {
                "source_name": "IBB Deprem Senaryosu Analiz Sonuclari",
                "url": "https://data.ibb.gov.tr/dataset/deprem-senaryosu-analiz-sonuclari",
                "date_accessed": datetime.date.today().isoformat(),
                "local_path": scen_path,
                "records": len(scenario),
                "notes": "CSV, cp1254 encoding, semicolon separator",
            },
            {
                "source_name": "IBB Nufus Bilgileri (TUİK kaynaklı)",
                "url": "https://data.ibb.gov.tr/dataset/nufus-bilgileri",
                "date_accessed": datetime.date.today().isoformat(),
                "local_path": pop_path,
                "records": len(pop),
                "notes": f"Latest year used for district population: {latest_year}",
            },
            {
                "source_name": "AFAD Earthquake Catalog API",
                "url": "https://deprem.afad.gov.tr/apiv2/event/filter",
                "date_accessed": datetime.date.today().isoformat(),
                "local_path": eq_path,
                "records": len(eq),
                "notes": "Marmara bbox 40.0-41.5N, 26.5-32.5E, M>=3.0",
            },
            {
                "source_name": "IBB Microzonation Reports",
                "url": "https://depremzemin.ibb.istanbul/tr/istanbul-ili-mikrobolgeleme-projeleri",
                "date_accessed": datetime.date.today().isoformat(),
                "local_path": DOCS,
                "records": 5,
                "notes": "PDF reports downloaded for legend-based geologic class extraction",
            },
            {
                "source_name": "OSM Nominatim (supplementary)",
                "url": "https://nominatim.openstreetmap.org",
                "date_accessed": datetime.date.today().isoformat(),
                "local_path": cent_path,
                "records": len(cent),
                "notes": "Used only for district centroid coordinates in visualization",
            },
        ]
    )
    source_registry.to_csv(os.path.join(LAB_DATA, "source_registry.csv"), index=False)

    preview = unified.sort_values("composite_risk_score", ascending=False).head(10)[
        ["district", "composite_risk_score"]
    ]
    # Avoid Windows console encoding errors for Turkish characters.
    print(preview.to_string(index=False).encode("ascii", errors="ignore").decode("ascii"))


if __name__ == "__main__":
    main()
