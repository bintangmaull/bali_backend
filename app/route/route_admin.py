import os
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models_database import User, ActivityLog

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/api/admin')

# Developer-only password (simpan di environment variable ADMIN_SECRET)
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'cardinaladmin2024')


def admin_required(fn):
    """Decorator: validasi X-Admin-Secret header sebelum mengeksekusi route admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        secret = request.headers.get('X-Admin-Secret', '')
        if secret != ADMIN_SECRET:
            return jsonify({'msg': 'Akses ditolak: bukan administrator.'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ─── Manajemen User ──────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Daftar semua pengguna terdaftar."""
    status_filter = request.args.get('status')  # optional: 'pending', 'approved', 'rejected'
    query = User.query.order_by(User.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    users = query.all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Menyetujui pendaftaran pengguna."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan.'}), 404
    user.status = 'approved'
    db.session.commit()
    return jsonify({'msg': f'Akun {user.email} berhasil disetujui.', 'user': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Menolak pendaftaran pengguna."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan.'}), 404
    user.status = 'rejected'
    db.session.commit()
    return jsonify({'msg': f'Akun {user.email} telah ditolak.', 'user': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Menghapus pengguna dari sistem."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Pengguna tidak ditemukan.'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'msg': f'Akun {user.email} berhasil dihapus.'}), 200


# ─── Activity Log ─────────────────────────────────────────────────

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    """Daftar semua activity log, terbaru di atas."""
    target_filter = request.args.get('target')  # optional: 'bangunan' atau 'hsbgn'
    query = ActivityLog.query.order_by(ActivityLog.timestamp.desc())
    if target_filter:
        query = query.filter_by(target=target_filter)
    logs = query.limit(500).all()
    return jsonify([log.to_dict() for log in logs]), 200
