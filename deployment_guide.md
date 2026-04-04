# Panduan Deploy Backend ke Hostinger VPS via Dokploy

Dokploy adalah alternatif open-source (seperti Vercel/Coolify) yang sangat ringan untuk mengelola deployment di VPS sendiri. Berikut adalah langkah-langkah untuk mendeploy project **backend-capstone-aal** Anda.

## 1. Persiapan VPS di Hostinger
*   **Pilih Paket**: Gunakan VPS KVM (minimal 2GB RAM, disarankan 4GB).
*   **Sistem Operasi**: Pilih **Ubuntu 22.04 LTS** atau **Ubuntu 24.04 LTS** (Clean Install).
*   **Firewall**: Pastikan port `80`, `443`, dan `3000` (untuk setup awal) terbuka.

## 2. Instalasi Dokploy
Masuk ke VPS Anda via SSH (misal: `ssh root@ip-vps-anda`) dan jalankan command satu baris ini:

```bash
curl -sSL https://dokploy.com/install.sh | sh
```

Tunggu hingga selesai. Dokploy akan menginstal Docker dan komponen lainnya secara otomatis.

## 3. Setup Awal Dokploy
1.  Buka browser dan akses `http://ip-vps-anda:3000`.
2.  Buat akun admin pertama Anda.
3.  (Disarankan) Masuk ke **Settings** > **Domain** untuk mengatur domain/subdomain ke IP VPS agar bisa menggunakan HTTPS (SSL otomatis via Let's Encrypt).

## 4. Deploy Project
### A. Hubungkan ke GitHub
1.  Di dashboard Dokploy, pergi ke menu **Git Providers**.
2.  Hubungkan akun GitHub Anda.

### B. Buat Project & Application
1.  Klik **Create Project**, beri nama (misal: `backend-aal`).
2.  Klik project tersebut, lalu pilih **Add Service** > **Application**.
3.  Pilih repository: `bintangmaull/backend-capstone-aal`.
4.  Pilih branch: `main` (atau branch pilihan Anda).

### C. Konfigurasi Build & Environment
Dokploy akan mendeteksi `Dockerfile` di root project secara otomatis.

1.  **Build Method**: Pastikan terpilih **Docker** (karena sudah ada Dockerfile).
2.  **Environment Variables**: Masukkan variabel berikut di tab **Environment**:
    *   `DB_USER`: [User Database Anda]
    *   `DB_PASSWORD`: [Password Database Anda]
    *   `DB_HOST`: [Host Database Anda]
    *   `DB_PORT`: `5432`
    *   `DB_NAME`: [Nama Database Anda]
    *   `JWT_SECRET_KEY`: [String Random untuk JWT]
    *   `FRONTEND_URL`: [URL Frontend Anda, misal https://my-dashboard.vercel.app]

### D. Deploy Backend
1.  Klik tombol **Deploy**.
2.  Cek tab **Logs** untuk melihat progres build docker.
3.  Setelah selesai (status "Running"), aplikasi akan bisa diakses sesuai domain/port yang dikonfigurasi di Dokploy.

---

## 5. Deploy Frontend (Next.js)
### A. Buat Application Baru
1.  Di project yang sama (`backend-aal`), klik **Add Service** > **Application**.
2.  Pilih repository: `bintangmaull/frontend-capstone-aal`.
3.  Pilih branch: `main`.

### B. Konfigurasi Build & Environment
Saya telah membuatkan `Dockerfile` di root frontend agar build lebih stabil.

1.  **Build Method**: Pilih **Docker**.
2.  **Environment Variables**: Masukkan variabel berikut di tab **Environment**:
    *   `NEXT_PUBLIC_API_URL`: [URL Backend Anda, misal https://api-aal.com]
    *   `NEXT_PUBLIC_SUPABASE_KEY`: [Key Supabase Anda]

### C. Deploy Frontend
1.  Klik tombol **Deploy**.
2.  Setelah status "Running", frontend Anda akan aktif.

> [!TIP]
> Di bagian **Networking**, petakan domain utama Anda (misal `dashboard-aal.com`) ke container port `3000` (port standar Next.js).

---

## 6. Tips & Maintenance
