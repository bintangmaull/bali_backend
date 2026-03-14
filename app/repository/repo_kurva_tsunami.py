# app/repository/repo_kurva_tsunami.py

import logging
from app.models.models_database import TsunamiReferenceCurve
from app.extensions import db

logger = logging.getLogger(__name__)

def get_reference_curves_tsunami():
    """Mengambil referensi kurva Tsunami dari database (tipe_kurva: cr, mcf, mur, w)."""
    try:
        logger.info("📥 Mengambil referensi kurva Tsunami dari database...")
        with db.session.no_autoflush:
            curves = db.session.query(TsunamiReferenceCurve).all()
        db.session.expunge_all()
        db.session.close()

        reference_curves = {}
        for curve in curves:
            reference_curves.setdefault(curve.tipe_kurva, {"x": [], "y": []})
            reference_curves[curve.tipe_kurva]["x"].append(curve.x)
            reference_curves[curve.tipe_kurva]["y"].append(curve.y)

        logger.info(f"✅ Berhasil mengambil {len(curves)} referensi kurva Tsunami.")
        return reference_curves

    except Exception as e:
        db.session.rollback()
        db.session.close()
        logger.error(f"❌ ERROR mengambil kurva Tsunami: {e}")
        return {}
