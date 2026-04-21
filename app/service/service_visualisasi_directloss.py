from app.repository.repo_visualisasi_directloss import GedungRepository

class GedungService:
    @staticmethod
    def get_geojson(bbox=None, prov=None, kota=None, limit=None):
        return GedungRepository.fetch_geojson(bbox=bbox, prov=prov, kota=kota, limit=limit)

    @staticmethod
    def get_provinsi_list():
        return GedungRepository.fetch_provinsi()

    @staticmethod
    def get_kota_list(provinsi):
        return GedungRepository.fetch_kota(provinsi)

    @staticmethod
    def get_aal_geojson(provinsi=None):
        return GedungRepository.fetch_aal_geojson(provinsi)

    @staticmethod
    def get_aal_provinsi_list():
        return GedungRepository.fetch_aal_provinsi_list()

    @staticmethod
    def get_aal_data(provinsi):
        return GedungRepository.fetch_aal_data(provinsi)

    # ————————————————
    # Service untuk CSV
    @staticmethod
    def get_directloss_csv():
        return GedungRepository.stream_directloss_csv()

    @staticmethod
    def get_aal_csv():
        return GedungRepository.stream_aal_csv()

    # ————————————————
    # Service AAL per Kota
    @staticmethod
    def get_aal_kota_geojson(cv='0.15', scheme='1'):
        return GedungRepository.fetch_aal_kota_geojson(cv=cv, scheme=scheme)

    @staticmethod
    def get_aal_kota_csv():
        return GedungRepository.stream_aal_kota_csv()

    @staticmethod
    def get_rekap_aset_kota_geojson():
        return GedungRepository.fetch_rekap_aset_kota_geojson()

    @staticmethod
    def get_aal_drought_geojson(year=None, cc=None):
        return GedungRepository.fetch_aal_drought_geojson(year=year, cc=cc)

    @staticmethod
    def get_aal_flood_sawah_geojson(year=None, cc=None):
        return GedungRepository.fetch_aal_flood_sawah_geojson(year=year, cc=cc)

    @staticmethod
    def get_aal_flood_building(kota=None, cv=None):
        return GedungRepository.fetch_aal_flood_building(kota=kota, cv=cv)

    @staticmethod
    def get_aal_flood_building_skema2(kota=None):
        return GedungRepository.fetch_aal_flood_building_skema2(kota=kota)

