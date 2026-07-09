# CPU Patching Runbook

This repository contains Ansible playbooks for patching Oracle Identity & Access Management products and infrastructure components.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Directory Structure](#directory-structure)
- [Pre-patching Configuration](#pre-patching-configuration)
- [OIG — Oracle Identity Governance](#oig--oracle-identity-governance)
- [OAM — Oracle Access Manager](#oam--oracle-access-manager)
- [OUD — Oracle Unified Directory](#oud--oracle-unified-directory)
- [OHS — Oracle HTTP Server](#ohs--oracle-http-server)
- [OSB — Oracle Service Bus](#osb--oracle-service-bus)
- [AAG — Axway API Gateway](#aag--axway-api-gateway)
- [Running Selected Steps (Tags)](#running-selected-steps-tags)
- [Variables — Where to Set Them](#variables--where-to-set-them)

---

## Prerequisites

- Ansible >= 2.9
- SSH access to target servers as `oracle` user
- Patch archives placed in `/app/patches/` on the Ansible host
- Oracle Database **must be running** before starting OIG/OAM/OSB
- For OIG and OAM: NFS `/mnt/nfs` mounted on both nodes

---

## Directory Structure

```
.
├── group_vars/
│   └── vars.yml                   # Global variables for all environments
├── inventory/
│   ├── fat/
│   │   ├── hosts                  # FAT inventory
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

## Pre-patching Configuration

### 1. Set environment variables in `group_vars/vars.yml`

Before running any patching playbook, ensure the following variables are set correctly for the target environment:

```yaml
# OIG
oig_managed_server_domain: /app/config/mserver/domains/IAMGovernanceDomain      # FAT
# oig_managed_server_domain: /app/config/mserver/domains/IAMGovernanceDomain12c  # DEV
oig_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMGovernanceDomain    # FAT
# oig_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMGovernanceDomain12c  # DEV

# OAM
oam_managed_server_domain: /app/config/mserver/domains/IAMAccessDomain
oam_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMAccessDomain
```

### 2. Set passwords (Ansible Vault)

```bash
ansible-vault encrypt_string 'password' --name 'oig_wls_password'
ansible-vault encrypt_string 'password' --name 'oam_wls_password'
```

### 3. Place patch archives on the Ansible host

```
/app/patches/
├── JAVA/    → jdk-8u491-linux-x64.tar.gz
├── OIG/     → OIG patch archives
├── OAM/     → OAM patch archives
├── OUD/     → OUD patch archives
├── OHS/     → OHS patch archives
├── OSB/     → OSB patch archives
└── AAG/     → AAG patch archive
```

---

## OIG — Oracle Identity Governance

### ⚠️ NFS Warning

The Admin Server and its configuration reside on NFS (`/mnt/nfs/config/aserver`).  
**Before performing an NFS backup, the Node Manager on node2 must be stopped**, because Node Manager holds open file handles on the NFS resource and causes the backup to hang.

The correct order of operations is handled automatically by the playbook:
1. Stop OIG managed servers (node1 + node2) — via WLST with `force=true`
2. Stop Admin Server (node1)
3. Stop Node Manager (both nodes)
4. Backup
5. Patching
6. Start Node Manager → Admin Server → SOA → OIG

### Usage

```bash
# FAT environment — mh location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh"

# DEV environment
ansible-playbook -i inventory/dev/hosts playbooks/patch_oig.yml -e "target=oig_mh"

# Single server
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oim1.mh.fat.ccn2.taxud"

# One node at a time (default: 2)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" -e "serial=1"
```

### Playbook Steps

| Step | Tag | Description |
|------|-----|-------------|
| Stop OIG services | `stop`, `cots` | Stops SOA+OIG managed servers (force), Admin Server, Node Manager |
| Backup OIG | `backup` | Backup of Oracle Home and domain configuration |
| Install/Update JDK | `jdk` | JDK upgrade |
| Install/Update OPatch | `opatch` | OPatch tool upgrade |
| Apply SPBAT Bundle Patch | `spbat` | OIG Bundle Patch installation |
| Apply OIG patches | `patch` | Additional OIG patches installation |
| Start OIG services | `start`, `cots` | Starts Node Manager → Admin Server → SOA → OIG |

### Requirements Before Running

- Oracle Database **must be running**
- NFS `/mnt/nfs` mounted and accessible
- Verify: `df -h | grep mnt`

---

## OAM — Oracle Access Manager

### ⚠️ NFS Warning

Same as OIG — the OAM Admin Server resides on NFS (`/mnt/nfs/config/aserver/domains/IAMAccessDomain`).  
**Before an NFS backup, the Node Manager on node2 must be stopped.**  
The playbook handles this automatically in the correct order.

### Usage

```bash
# FAT — ap1 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap1"

# FAT — ap2 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap2"

# FAT — ap3 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap3"

# FAT — ap4 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam_ap4"

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_oam.yml -e "target=oam_ap1"

# All locations at once
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml

# Single server
ansible-playbook -i inventory/fat/hosts playbooks/patch_oam.yml -e "target=oam1.ap1.fat.ccn2.taxud"
```

### Playbook Steps

| Step | Tag | Description |
|------|-----|-------------|
| Stop OAM services | `stop`, `cots` | Stops OAM/AMA managed servers, Admin Server, Node Manager |
| Backup OAM | `backup` | Backup of Oracle Home and domain configuration |
| Install/Update JDK | `jdk` | JDK upgrade |
| Install/Update OPatch | `opatch` | OPatch tool upgrade |
| Apply SPBAT Bundle Patch | `spbat` | OAM Bundle Patch installation |
| Apply OAM patches | `patch` | Additional OAM patches installation |
| Start OAM services | `start`, `cots` | Starts Node Manager → Admin Server → OAM → AMA |

### Requirements Before Running

- Oracle Database **must be running**
- NFS `/mnt/nfs` mounted and accessible

---

## OUD — Oracle Unified Directory

### Notes

- OUD does not have Admin Server / Node Manager on NFS — no NFS restrictions apply
- Patched **1 node at a time** by default (`serial=1`) to maintain LDAP service availability
- LDAP instance path: `/app/ldap_instance`

### Usage

```bash
# FAT — mh location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_mh"

# FAT — ap1 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap1"

# FAT — ap2 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap2"

# FAT — ap3 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap3"

# FAT — all locations
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_oud.yml -e "target=oud_ap1"

# Single server
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud1.ap1.fat.ccn2.taxud"

# Two nodes in parallel (risk — LDAP service unavailability)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oud.yml -e "target=oud_ap1" -e "serial=2"
```

### Playbook Steps

| Step | Tag | Description |
|------|-----|-------------|
| Stop OUD services | `stop`, `cots` | Stops the OUD LDAP instance |
| Backup OUD | `backup` | Backup of Oracle Home and LDAP instance |
| Install/Update JDK | `jdk` | JDK upgrade |
| Install/Update OPatch | `opatch` | OPatch tool upgrade |
| Apply OUD patches | `patch` | OUD patches installation |
| Start OUD services | `start`, `cots` | Starts the OUD LDAP instance |

---

## OHS — Oracle HTTP Server

### Notes

- OHS is the HTTP frontend — patched **1 node at a time** (`serial=1`)
- Playbook includes an additional DB Client installation step (`db_client`)
- No Node Manager / NFS — no NFS restrictions apply

### Usage

```bash
# FAT — ap1 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml -e "target=ohs_ap1"

# FAT — ap2 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml -e "target=ohs_ap2"

# FAT — all locations
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_ohs.yml -e "target=ohs_ap1"

# Single server
ansible-playbook -i inventory/fat/hosts playbooks/patch_ohs.yml -e "target=ohs1.ap1.fat.ccn2.taxud"
```

### Playbook Steps

| Step | Tag | Description |
|------|-----|-------------|
| Stop OHS services | `stop`, `cots` | Stops Oracle HTTP Server |
| Backup OHS | `backup` | Backup of Oracle Home and configuration |
| Install/Update JDK | `jdk` | JDK upgrade |
| Install/Update OPatch | `opatch` | OPatch tool upgrade |
| Install DB Client | `db_client` | Oracle DB Client installation/upgrade |
| Apply OHS patches | `patch` | OHS patches installation |
| Start OHS services | `start`, `cots` | Starts Oracle HTTP Server |

---

## OSB — Oracle Service Bus

### Notes

- OSB Admin Server and Managed Servers reside on local filesystem (no NFS)
- Patched **1 node at a time** by default (`serial=1`)

### Usage

```bash
# FAT — ap1 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap1"

# FAT — ap2 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap2"

# FAT — ap3 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap3"

# FAT — ap4 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb_ap4"

# FAT — all locations
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_osb.yml -e "target=osb_ap1"

# Single server
ansible-playbook -i inventory/fat/hosts playbooks/patch_osb.yml -e "target=osb1.ap1.fat.ccn2.taxud"
```

### Playbook Steps

| Step | Tag | Description |
|------|-----|-------------|
| Stop OSB services | `stop`, `cots` | Stops OSB managed servers and Admin Server |
| Backup OSB | `backup` | Backup of Oracle Home and domain configuration |
| Install/Update JDK | `jdk` | JDK upgrade |
| Install/Update OPatch | `opatch` | OPatch tool upgrade |
| Apply SPBAT Bundle Patch | `spbat` | SOA/OSB Bundle Patch installation |
| Apply OSB patches | `patch` | Additional OSB patches installation |
| Start OSB services | `start`, `cots` | Starts Admin Server and OSB managed servers |

### Requirements Before Running

- Oracle Database **must be running**

---

## AAG — Axway API Gateway

### Notes

- AAG **does not use OPatch** (no Oracle Home) — no jdk/opatch/spbat steps
- Patched **1 node at a time** by default (`serial=1`)
- Patch archive: single `.tar.gz` file

### Usage

```bash
# FAT — ap1 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap1"

# FAT — ap2 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap2"

# FAT — ap3 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap3"

# FAT — ap4 location
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag_ap4"

# FAT — all locations
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml

# DEV
ansible-playbook -i inventory/dev/hosts playbooks/patch_aag.yml -e "target=aag_ap1"

# Single server
ansible-playbook -i inventory/fat/hosts playbooks/patch_aag.yml -e "target=aag1.ap1.fat.ccn2.taxud"
```

### Playbook Steps

| Step | Tag | Description |
|------|-----|-------------|
| Stop AAG services | `stop`, `cots` | Stops Axway API Gateway |
| Backup AAG | `backup` | Backup of AAG installation directory |
| Apply AAG patch | `patch` | AAG new version installation |
| Start AAG services | `start`, `cots` | Starts Axway API Gateway |

---

## Running Selected Steps (Tags)

Each playbook supports tags to run only selected steps:

```bash
# Stop only
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags stop

# Backup only
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags backup

# Patch only (without stop/start)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags patch

# Start only
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags start

# Stop + patch (without backup and start)
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --tags "stop,patch"

# Skip backup
ansible-playbook -i inventory/fat/hosts playbooks/patch_oig.yml -e "target=oig_mh" --skip-tags backup
```

| Tag | Available in |
|-----|-------------|
| `stop`, `cots` | all products |
| `backup` | all products |
| `jdk` | OIG, OAM, OUD, OHS, OSB |
| `opatch` | OIG, OAM, OUD, OHS, OSB |
| `spbat` | OIG, OAM, OSB |
| `db_client` | OHS |
| `patch` | all products |
| `start`, `cots` | all products |

---

## Variables — Where to Set Them

| Variable | File | Notes |
|----------|------|-------|
| `oig_managed_server_domain` | `group_vars/vars.yml` | Set manually per environment |
| `oig_admin_server_domain` | `group_vars/vars.yml` | Set manually per environment |
| `oam_managed_server_domain` | `group_vars/vars.yml` | Set manually per environment |
| `oam_admin_server_domain` | `group_vars/vars.yml` | Set manually per environment |
| `ap` | `inventory/<env>/group_vars/<group>/vars` | Set automatically per location |
| `env` | `inventory/<env>/hosts` `[all:vars]` | Set per environment |
| `oig_wls_password` | `group_vars/vars.yml` | Encrypt with ansible-vault |
| `oam_wls_password` | `group_vars/vars.yml` | Encrypt with ansible-vault |
| `osb_wls_password` | `group_vars/vars.yml` | Encrypt with ansible-vault |
