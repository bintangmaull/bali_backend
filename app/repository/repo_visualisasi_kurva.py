from app.models.models_database import (
    GempaReferenceCurve,
    TsunamiReferenceCurve,
    BanjirReferenceCurve,
)

def get_disaster_data(disaster_type):
    model_map = {
        "gempa":     GempaReferenceCurve,
        "tsunami":   TsunamiReferenceCurve,
        "banjir":    BanjirReferenceCurve,      # dipakai untuk banjir_r dan banjir_rc
        "banjir_r":  BanjirReferenceCurve,
        "banjir_rc": BanjirReferenceCurve,
    }

    model = model_map.get(disaster_type)
    if not model:
        raise ValueError(f"Unknown disaster type: {disaster_type}")

    rows = model.query.order_by(model.x.asc()).all()
    return [(row.x, row.y) for row in rows]
