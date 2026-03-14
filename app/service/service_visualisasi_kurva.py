# app/service/service_visualisasi_kurva.py

from app.models.models_database import (
    GempaReferenceCurve,
    TsunamiReferenceCurve,
    BanjirReferenceCurve,
)

def get_all_disaster_curves():
    # Peta nama ke Model SQLAlchemy
    # banjir digunakan untuk banjir_r dan banjir_rc (sama-sama pakai BanjirReferenceCurve)
    mapping = {
        "gempa":     GempaReferenceCurve,
        "tsunami":   TsunamiReferenceCurve,
        "banjir":    BanjirReferenceCurve,
    }

    all_curves = {}
    for disaster, Model in mapping.items():
        rows = Model.query.order_by(Model.tipe_kurva, Model.x).all()

        grouped = {}
        for row in rows:
            t = row.tipe_kurva
            if t not in grouped:
                grouped[t] = {"x": [], "y": []}
            grouped[t]["x"].append(row.x)
            grouped[t]["y"].append(row.y)

        all_curves[disaster] = grouped

    return all_curves
