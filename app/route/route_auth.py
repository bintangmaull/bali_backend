from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import json
from app.extensions import db
from app.models.models_database import User

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Mendaftarkan pengguna baru dengan status 'pending'."""
    data = request.get_json() or {}
    nama = data.get('nama', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not nama or not email or not password:
        return jsonify({'msg': 'Nama, email, dan password wajib diisi.'}), 400

    if len(password) < 6:
        return jsonify({'msg': 'Password minimal 6 karakter.'}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({'msg': 'Email sudah terdaftar.'}), 409

    new_user = User(
        nama=nama,
        email=email,
        password_hash=generate_password_hash(password),
        status='pending'
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'msg': 'Pendaftaran berhasil. Akun Anda sedang menunggu persetujuan admin.',
        'user': new_user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login dengan email dan password. Hanya akun 'approved' yang bisa masuk."""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'msg': 'Email dan password wajib diisi.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'msg': 'Email atau password salah.'}), 401

    if user.status == 'pending':
        return jsonify({'msg': 'Akun Anda belum disetujui oleh admin. Silakan tunggu.'}), 403

    if user.status == 'rejected':
        return jsonify({'msg': 'Akun Anda telah ditolak oleh admin.'}), 403

    # Flask-JWT-Extended 4.x: identity MUST be a string, not a dict
    identity_str = json.dumps({'id': user.id, 'email': user.email, 'nama': user.nama})
    token = create_access_token(identity=identity_str)

    return jsonify({
        'access_token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Mengembalikan info user yang sedang login."""
    current_user = get_jwt_identity()
    return jsonify({'user': current_user}), 200
