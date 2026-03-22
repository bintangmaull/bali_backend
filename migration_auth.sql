-- SQL Migration: Buat tabel users dan activity_log di Supabase
-- Jalankan skrip ini di Supabase SQL Editor (Database > SQL Editor)

-- Tabel users
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    nama          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabel activity_log
CREATE TABLE IF NOT EXISTS activity_log (
    id          SERIAL PRIMARY KEY,
    user_nama   VARCHAR(255) NOT NULL,
    user_email  VARCHAR(255) NOT NULL,
    action      VARCHAR(50)  NOT NULL, -- 'tambah' | 'edit' | 'hapus' | 'upload_csv'
    target      VARCHAR(50)  NOT NULL, -- 'bangunan' | 'hsbgn'
    target_id   VARCHAR(255),
    detail      TEXT,
    timestamp   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- (Opsional) RLS: Aktifkan Row Level Security jika diperlukan
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
