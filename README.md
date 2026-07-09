# CPU Patching Runbook

Repozytorium zawiera playbooki Ansible do patchowania produktów Oracle Identity & Access Management oraz komponentów infrastrukturalnych.

---

## Spis treści

- [Wymagania wstępne](#wymagania-wstępne)
- [Struktura katalogów](#struktura-katalogów)
- [Konfiguracja przed patchowaniem](#konfiguracja-przed-patchowaniem)
- [OIG — Oracle Identity Governance](#oig--oracle-identity-governance)
- [OAM — Oracle Access Manager](#oam--oracle-access-manager)
- [OUD — Oracle Unified Directory](#oud--oracle-unified-directory)
- [OHS — Oracle HTTP Server](#ohs--oracle-http-server)
- [OSB — Oracle Service Bus](#osb--oracle-service-bus)
- [AAG — Axway API Gateway](#aag--axway-api-gateway)
- [Uruchamianie wybranych kroków (tagi)](#uruchamianie-wybranych-kroków-tagi)
- [Zmienne — gdzie je ustawić](#zmienne--gdzie-je-ustawić)

---

## Wymagania wstępne

- Ansible >= 2.9
- Dostęp SSH do serwerów docelowych jako użytkownik `oracle`
- Paczki patchy umieszczone w katalogu `/app/patches/` na serwerze Ansible
- Baza danych Oracle **uruchomiona** przed startem OIG/OAM/OSB
- Dla OIG i OAM: NFS `/mnt/nfs` zamontowany na obu nodach

---

## Struktura katalogów

```
.
├── group_vars/
│   └── vars.yml                   # Globalne zmienne dla wszystkich środowisk
├── inventory/
│   ├── fat/
│   │   ├── hosts                  # Inwentarz FAT
│   │   └── group_vars/
│   │       ├── oig_mh/vars        # ap: mh
│   │       ├── oam_ap1/vars       # ap: ap1
│   │       ├── oud_mh/vars        # ap: mh
│   │       └── ...
│   └── dev/
│       └── ...
├── playbooks/
│   ├── patch_oig.yml
│   ├── patch_oam.yml
│   ├── patch_oud.yml
│   ├── patch_ohs.yml
│   ├── patch_osb.yml
│   └── patch_aag.yml
└── roles/
    ├── stop_cots/
    ├── start_cots/
    ├── backup/
    ├── jdk/
    ├── opatch_install/
    ├── spbat/
    └── patch/
```

---

## Konfiguracja przed patchowaniem

### 1. Ustaw zmienne środowiskowe w `group_vars/vars.yml`

Przed uruchomieniem patchowania upewnij się że poniższe zmienne są poprawne dla docelowego środowiska:

```yaml
# OIG
oig_managed_server_domain: /app/config/mserver/domains/IAMGovernanceDomain   # FAT
# oig_managed_server_domain: /app/config/mserver/domains/IAMGovernanceDomain12c  # DEV
oig_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMGovernanceDomain   # FAT
# oig_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMGovernanceDomain12c  # DEV

# OAM
oam_managed_server_domain: /app/config/mserver/domains/IAMAccessDomain
oam_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMAccessDomain
```

### 2. Ustaw hasła (Ansible Vault)

```bash
ansible-vault encrypt_string 'haslo' --name 'oig_wls_password'
ansible-vault encrypt_string 'haslo' --name 'oam_wls_password'
```

### 3. Umieść paczki patchy na serwerze Ansible

```
/app/patches/
├── JAVA/    → jdk-8u491-linux-x64.tar.gz
├── OIG/     → paczki OIG
├── OAM/     → paczki OAM
├── OUD/     → paczki OUD
├── OHS/     → paczki OHS
├── OSB/     → paczki OSB
└── AAG/     → paczka AAG
```

---

## OIG — Oracle Identity Governance

### ⚠️ Uwaga NFS

Admin Server i jego konfiguracja znajdują się na NFS (`/mnt/nfs/config/aserver`).  
**Przed wykonaniem backupu NFS należy zatrzymać Node Manager na node2**, ponieważ Node Manager trzyma otwarte pliki na zasobie NFS i backup się zawiesza.

Kolejność operacji jest obsługiwana automatycznie przez playbook:
1. Stop OIG managed servers (node1 + node2) — przez WLST z `force=true`
2. Stop Admin Server (node1)
3. Stop Node Manager (oba nody)
4. Backup
5. Patching
6. Start Node Manager → Admin Server → SOA → OIG

### Uruchomienie

```bash
# Środowisko FAT — lokalizacja mh
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh"

# Środowisko DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_oig.yml -e "target=oig_mh"

# Pojedynczy serwer
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oim1.mh.fat.ccn2.taxud"

# Jeden node na raz (domyślnie 2)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" -e "serial=1"
```

### Kroki playbooka

| Krok | Tag | Opis |
|------|-----|------|
| Stop OIG services | `stop`, `cots` | Zatrzymuje SOA+OIG managed servers (force), Admin Server, Node Manager |
| Backup OIG | `backup` | Backup Oracle Home i konfiguracji |
| Install/Update JDK | `jdk` | Aktualizacja JDK |
| Install/Update OPatch | `opatch` | Aktualizacja narzędzia OPatch |
| Apply SPBAT Bundle Patch | `spbat` | Instalacja Bundle Patcha OIG |
| Apply OIG patches | `patch` | Instalacja dodatkowych patchy OIG |
| Start OIG services | `start`, `cots` | Uruchomienie Node Manager → Admin → SOA → OIG |

### Wymagania przed uruchomieniem

- Baza danych Oracle **musi być uruchomiona**
- NFS `/mnt/nfs` zamontowany i dostępny
- Weryfikacja: `df -h | grep mnt`

---

## OAM — Oracle Access Manager

### ⚠️ Uwaga NFS

Analogicznie jak OIG — Admin Server OAM jest na NFS (`/mnt/nfs/config/aserver/domains/IAMAccessDomain`).  
**Przed backupem NFS Node Manager na node2 musi być zatrzymany.**  
Playbook obsługuje to automatycznie w odpowiedniej kolejności.

### Uruchomienie

```bash
# FAT — lokalizacja ap1
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap1"

# FAT — lokalizacja ap2
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap2"

# FAT — lokalizacja ap3
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap3"

# FAT — lokalizacja ap4
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap4"

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_oam.yml -e "target=oam_ap1"

# Wszystkie lokalizacje naraz
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml

# Pojedynczy serwer
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam1.ap1.fat.ccn2.taxud"
```

### Kroki playbooka

| Krok | Tag | Opis |
|------|-----|------|
| Stop OAM services | `stop`, `cots` | Zatrzymuje OAM/AMA managed servers, Admin Server, Node Manager |
| Backup OAM | `backup` | Backup Oracle Home i konfiguracji |
| Install/Update JDK | `jdk` | Aktualizacja JDK |
| Install/Update OPatch | `opatch` | Aktualizacja narzędzia OPatch |
| Apply SPBAT Bundle Patch | `spbat` | Instalacja Bundle Patcha OAM |
| Apply OAM patches | `patch` | Instalacja dodatkowych patchy OAM |
| Start OAM services | `start`, `cots` | Uruchomienie Node Manager → Admin → OAM → AMA |

### Wymagania przed uruchomieniem

- Baza danych Oracle **musi być uruchomiona**
- NFS `/mnt/nfs` zamontowany i dostępny

---

## OUD — Oracle Unified Directory

### Uwagi

- OUD nie posiada Admin/Node Manager na NFS — brak ograniczeń NFS
- Domyślnie patchowany **1 node na raz** (`serial=1`) aby zachować dostępność usługi LDAP
- Instancja LDAP: `/app/ldap_instance`

### Uruchomienie

```bash
# FAT — lokalizacja mh
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_mh"

# FAT — lokalizacja ap1
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap1"

# FAT — lokalizacja ap2
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap2"

# FAT — lokalizacja ap3
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap3"

# FAT — wszystkie lokalizacje
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_oud.yml -e "target=oud_ap1"

# Pojedynczy serwer
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud1.ap1.fat.ccn2.taxud"

# Dwa nody równolegle (ryzyko — utrata dostępności LDAP)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap1" -e "serial=2"
```

### Kroki playbooka

| Krok | Tag | Opis |
|------|-----|------|
| Stop OUD services | `stop`, `cots` | Zatrzymuje instancję OUD LDAP |
| Backup OUD | `backup` | Backup Oracle Home i instancji LDAP |
| Install/Update JDK | `jdk` | Aktualizacja JDK |
| Install/Update OPatch | `opatch` | Aktualizacja narzędzia OPatch |
| Apply OUD patches | `patch` | Instalacja patchy OUD |
| Start OUD services | `start`, `cots` | Uruchomienie instancji OUD LDAP |

---

## OHS — Oracle HTTP Server

### Uwagi

- OHS jest frontendem HTTP — patchowany **1 node na raz** (`serial=1`)
- Playbook zawiera dodatkowy krok instalacji DB Client (`db_client`)
- Brak Node Manager / NFS — brak ograniczeń NFS

### Uruchomienie

```bash
# FAT — lokalizacja ap1
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml -e "target=ohs_ap1"

# FAT — lokalizacja ap2
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml -e "target=ohs_ap2"

# FAT — wszystkie lokalizacje
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_ohs.yml -e "target=ohs_ap1"

# Pojedynczy serwer
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml -e "target=ohs1.ap1.fat.ccn2.taxud"
```

### Kroki playbooka

| Krok | Tag | Opis |
|------|-----|------|
| Stop OHS services | `stop`, `cots` | Zatrzymuje Oracle HTTP Server |
| Backup OHS | `backup` | Backup Oracle Home i konfiguracji |
| Install/Update JDK | `jdk` | Aktualizacja JDK |
| Install/Update OPatch | `opatch` | Aktualizacja narzędzia OPatch |
| Install DB Client | `db_client` | Instalacja/aktualizacja Oracle DB Client |
| Apply OHS patches | `patch` | Instalacja patchy OHS |
| Start OHS services | `start`, `cots` | Uruchomienie Oracle HTTP Server |

---

## OSB — Oracle Service Bus

### Uwagi

- OSB posiada Admin Server i Managed Servers na lokalnym filesystemie (brak NFS)
- Domyślnie patchowany **1 node na raz** (`serial=1`)

### Uruchomienie

```bash
# FAT — lokalizacja ap1
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap1"

# FAT — lokalizacja ap2
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap2"

# FAT — lokalizacja ap3
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap3"

# FAT — lokalizacja ap4
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap4"

# FAT — wszystkie lokalizacje
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_osb.yml -e "target=osb_ap1"

# Pojedynczy serwer
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb1.ap1.fat.ccn2.taxud"
```

### Kroki playbooka

| Krok | Tag | Opis |
|------|-----|------|
| Stop OSB services | `stop`, `cots` | Zatrzymuje OSB managed servers i Admin Server |
| Backup OSB | `backup` | Backup Oracle Home i konfiguracji |
| Install/Update JDK | `jdk` | Aktualizacja JDK |
| Install/Update OPatch | `opatch` | Aktualizacja narzędzia OPatch |
| Apply SPBAT Bundle Patch | `spbat` | Instalacja Bundle Patcha SOA/OSB |
| Apply OSB patches | `patch` | Instalacja dodatkowych patchy OSB |
| Start OSB services | `start`, `cots` | Uruchomienie Admin Server i managed servers OSB |

### Wymagania przed uruchomieniem

- Baza danych Oracle **musi być uruchomiona**

---

## AAG — Axway API Gateway

### Uwagi

- AAG **nie używa OPatch** (brak Oracle Home) — brak kroków jdk/opatch/spbat
- Domyślnie patchowany **1 node na raz** (`serial=1`)
- Paczka patcha: pojedynczy plik `.tar.gz`

### Uruchomienie

```bash
# FAT — lokalizacja ap1
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap1"

# FAT — lokalizacja ap2
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap2"

# FAT — lokalizacja ap3
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap3"

# FAT — lokalizacja ap4
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap4"

# FAT — wszystkie lokalizacje
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_aag.yml -e "target=aag_ap1"

# Pojedynczy serwer
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag1.ap1.fat.ccn2.taxud"
```

### Kroki playbooka

| Krok | Tag | Opis |
|------|-----|------|
| Stop AAG services | `stop`, `cots` | Zatrzymuje Axway API Gateway |
| Backup AAG | `backup` | Backup katalogu instalacji AAG |
| Apply AAG patch | `patch` | Instalacja nowej wersji AAG |
| Start AAG services | `start`, `cots` | Uruchomienie Axway API Gateway |

---

## Uruchamianie wybranych kroków (tagi)

Każdy playbook obsługuje tagi umożliwiające uruchomienie tylko wybranych kroków:

```bash
# Tylko stop
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags stop

# Tylko backup
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags backup

# Tylko patching (bez stop/start)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags patch

# Tylko start
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags start

# Stop + patch (bez backup i start)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags "stop,patch"

# Pomiń backup
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --skip-tags backup
```

| Tag | Dostępny w |
|-----|-----------|
| `stop`, `cots` | wszystkie produkty |
| `backup` | wszystkie produkty |
| `jdk` | OIG, OAM, OUD, OHS, OSB |
| `opatch` | OIG, OAM, OUD, OHS, OSB |
| `spbat` | OIG, OAM, OSB |
| `db_client` | OHS |
| `patch` | wszystkie produkty |
| `start`, `cots` | wszystkie produkty |

---

## Zmienne — gdzie je ustawić

| Zmienna | Plik | Uwaga |
|---------|------|-------|
| `oig_managed_server_domain` | `group_vars/vars.yml` | Ustaw ręcznie per środowisko |
| `oig_admin_server_domain` | `group_vars/vars.yml` | Ustaw ręcznie per środowisko |
| `oam_managed_server_domain` | `group_vars/vars.yml` | Ustaw ręcznie per środowisko |
| `oam_admin_server_domain` | `group_vars/vars.yml` | Ustaw ręcznie per środowisko |
| `ap` | `inventory/<env>/group_vars/<group>/vars` | Ustawiane automatycznie per lokalizacja |
| `env` | `inventory/<env>/hosts` `[all:vars]` | Ustawiane per środowisko |
| `oig_wls_password` | `group_vars/vars.yml` | Szyfrować przez ansible-vault |
| `oam_wls_password` | `group_vars/vars.yml` | Szyfrować przez ansible-vault |
| `osb_wls_password` | `group_vars/vars.yml` | Szyfrować przez ansible-vault |
