Siap! Ini dia versi penuh (full version) dari file `DESIGN.md`-nya. Formatnya sudah disesuaikan persis seperti standar *System Prompt* agar AI *coding assistant* kamu (seperti Cursor, GitHub Copilot, atau ChatGPT) bisa langsung memahaminya dan membuat kode yang sesuai dengan visi "ramah untuk orang awam" di semua sistem operasi.

Tinggal klik tombol **Copy** di sudut blok kode di bawah ini, lalu *paste* ke file `DESIGN.md` kamu:

```markdown
# 🤖 SYSTEM BLUEPRINT & AI PROMPT: AutoBiz Engine TUI
> **Target Audience:** Non-Technical Users (Laypeople / Aspiring CEOs).
> **Platform Requirement:** Cross-Platform (Windows, macOS, Linux).
> **Tech Stack:** Go (Bubbletea) for TUI Front-End, Python (FastAPI) for Backend.

## 🎯 1. DIRECTIVE FOR AI DEVELOPER
Anda adalah *Expert Go Developer & UI/UX Designer*. Tugas Anda adalah membangun Terminal User Interface (TUI) untuk **AutoBiz Engine**, sebuah platform orkestrasi AI otonom untuk bisnis.

**KRITERIA WAJIB (STRICT RULES):**
1. **Zero-Friction UX:** Pengguna aplikasi ini adalah orang awam (bukan programmer). TUI tidak boleh terlihat seperti *hacker tool*. Jangan pernah tampilkan *raw JSON* atau *stack trace error* ke layar pengguna. Terjemahkan semua *response* sistem ke bahasa manusia yang ramah dan mudah dimengerti.
2. **Cross-Platform Compatibility:** Gunakan library (`charmbracelet/bubbletea`) yang menjamin TUI berjalan mulus di Windows (CMD/PowerShell), macOS (Terminal/iTerm), dan Linux tanpa *dependency* atau pengaturan tambahan bagi *user*.
3. **Responsive Design:** Gunakan *flexbox/grid layout* (dengan `charmbracelet/lipgloss`) agar UI menyesuaikan ukuran jendela terminal secara otomatis tanpa merusak tata letak teks.
4. **Visual Feedback:** Selalu gunakan *loading spinner* (`charmbracelet/bubbles/spinner`), *progress bar*, atau notifikasi warna saat menunggu *response* dari Backend API agar pengguna tahu sistem sedang bekerja.

---

## 🏗️ 2. SYSTEM ARCHITECTURE

```text
┌─────────────────────────────────────────────────────────────┐
│  🖥️ TUI FRONTEND (Go / Bubbletea) - Cross-Platform Exec     │
│  [Tab 1: ⌘ Dashboard] [Tab 2: 🏢 Biz] [Tab 3: ⚖️ Approvals] │
│  UX: Layar harus terasa seperti dasbor game yang simpel.    │
└────────────────────────────┬────────────────────────────────┘
                             │ ⚡ Asynchronous HTTP REST
┌────────────────────────────▼────────────────────────────────┐
│  ⚙️ BACKEND ENGINE (Python / FastAPI)                       │
│  [🔑 Auth] [🚀 Biz Logic] [🤖 Agent Orchestrator]           │
└─────────────────────────────────────────────────────────────┘

```

---

## 🗺️ 3. NON-TECHNICAL USER FLOW

Terapkan alur ini dengan navigasi keyboard yang sangat mudah ditebak. Jika pengguna menekan tombol yang salah, jangan *crash*, berikan petunjuk *hint* di layar bawah.

```text
[Buka App] ──> [Layar Login Ramah] ──> [⌘ Dashboard: Ringkasan Bisnis]
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
            [🏢 Ide Bisnis Baru]      [⚖️ Kotak Keputusan]      [📈 Laporan Uang]
            (Input form sederhana)    (Pilih: Setuju/Tolak)     (Grafik & Angka Jelas)

```

---

## 🔌 4. BACKEND API INTEGRATION MAP

*AI Instruction: Petakan endpoint ini ke state management di Bubbletea. Gunakan `tea.Cmd` untuk fetching data secara asynchronous agar UI tidak freeze.*

**Base URL:** `http://localhost:8000/api/v1`

### A. Auth (Onboarding)

* `POST /auth/login` | Body: `{email, password}`
* *UI Rule:* Saat mengetik password, sembunyikan karakter dengan `***`.

### B. Businesses (Core Engine)

* `GET /businesses/`
* *UI Rule:* Tampilkan sebagai *list* atau *card* dengan status yang jelas menggunakan ikon (Misal: 🟡 Merancang, 🟢 Aktif).


* `POST /businesses/create` | Body: `{idea}`
* *UI Rule:* Berikan *text box* (textarea) yang luas agar user bebas menulis ide layaknya sedang *chatting* dengan asisten.


* `POST /businesses/{id}/launch`
* *UI Rule:* Buat animasi sukses yang memuaskan (misal: perubahan warna seketika atau teks "LILIS SUKSES!") saat tombol ini ditekan.



### C. Approvals (CEO Control)

* `GET /approvals/pending`
* `POST /approvals/{id}/decide` | Body: `{decision: "approve"|"reject"}`
* *UI Rule:* Ini adalah fitur utama interaksi. Buat layar ini terasa seperti kotak masuk (inbox) surel yang penting. Beri instruksi sangat jelas di layar: `[A] Setuju` atau `[R] Tolak`.

### D. Metrics (Performance)

* `GET /metrics/{id}/realtime`
* *UI Rule:* Ubah data mentah (angka) menjadi indikator visual yang mudah dimengerti (Contoh: "⬆️ Naik 20%", "🚨 Sedang sepi pengunjung").

---

## 🖥️ 5. COMPONENT TREE & STATE MANAGEMENT

Bangun struktur komponen Go (Model) seperti berikut untuk memastikan skalabilitas dan kerapian kode:

```go
AppModel (Memegang Global State & Auth Token)
├── ScreenAuth
│   └── InputForm (Email, Password via bubbles/textinput)
└── ScreenMain (Tampil setelah login berhasil)
    ├── HeaderComponent (Tampilkan Nama User & Status Koneksi Backend)
    ├── TabNavigator (Fokus kontrol navigasi horizontal: tombol 1, 2, 3, 4)
    ├── ContentRouter (Switch case berdasarkan tab aktif)
    │   ├── ViewDashboard (Statistik Global / Summary)
    │   ├── ViewBusinesses (List model & Form Create)
    │   ├── ViewApprovals (Inbox Keputusan model)
    │   └── ViewMetrics (Tabel & Mini-Charts model)
    └── FooterHelp (Selalu tampil di bawah: "Tekan 'q' untuk keluar, 'esc' kembali")

```

---

## 🎨 6. UI/UX DESIGN TOKENS (Bubbletea Lipgloss)

Gunakan palet warna ini menggunakan library `lipgloss`. Warna dipilih berdasarkan psikologi desain agar orang awam langsung paham konteksnya.

| State/Fungsi | Warna Hex | Penerapan TUI |
| --- | --- | --- |
| **Border / Pasif** | `#5C6370` | Garis kotak yang tidak aktif, teks petunjuk bantuan di footer. |
| **Active / Focus** | `#C678DD` | (Ungu Terang) Tab yang sedang dibuka, input text yang sedang aktif, baris list yang disorot. |
| **Success / Action** | `#98C379` | (Hijau) Tanda uang/profit masuk, tombol "Approve", status bisnis "Aktif". |
| **Warning / Danger** | `#E06C75` | (Merah) Error koneksi, penolakan (tombol "Reject"), notifikasi krisis atau *churn rate* tinggi. |
| **Info / Reading** | `#61AFEF` | (Biru) Teks isi penjelasan dari AI, indikator angka metrik netral. |

---

## ⌨️ 7. UNIVERSAL KEY BINDINGS

*AI Instruction: Daftarkan key bindings ini secara konsisten di seluruh layar menggunakan `bubbles/key`. Tampilkan panduan tombol ini di bagian bawah layar (Footer) secara dinamis sesuai menu yang sedang dibuka.*

| Key | Action | UX Note untuk Laypeople |
| --- | --- | --- |
| `Tab` / `Shift+Tab` | Pindah kolom input | Standar universal form di komputer. |
| `1`, `2`, `3`, `4` | Pindah Menu Utama | Sangat intuitif untuk navigasi cepat antar menu (Dashboard, Biz, Approvals, Metrics). |
| `Panah Atas/Bawah` | Scroll / Pilih *list* | Menggantikan *mouse scroll*. |
| `Enter` | Konfirmasi / Buka | Menggantikan *klik kiri mouse* untuk memilih item atau submit form. |
| `Esc` | Kembali / Batal | *Safety button* jika user salah masuk menu atau ingin batal mengisi form. |
| `a` | Approve (Setuju) | *Shortcut* khusus saat berada di dalam menu *Approvals*. |
| `r` | Reject (Tolak) | *Shortcut* khusus saat berada di dalam menu *Approvals*. |
| `q` | Keluar Aplikasi | Tombol aman untuk keluar (mencegah user panik menekan `Ctrl+C`). |

---

**END OF SYSTEM INSTRUCTION.**
*Execute the Go/Bubbletea implementation based strictly on the user-centric guidelines above. Prioritize clean, idiomatic Go code.*

```

```