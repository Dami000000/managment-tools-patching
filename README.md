# CPU Patching Runbook

This repository contains Ansible playbooks for patching Oracle Identity & Access Management products and infrastructure components.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Directory Structure](#directory-structure)
- [Pre-patching Checklist](#pre-patching-checklist)
  - [1. Verify and configure group_vars/vars.yml](#1-verify-and-configure-group_varsvarsyml)
  - [2. Verify inventory for the target environment](#2-verify-inventory-for-the-target-environment)
  - [3. Verify the hosts file for the target environment](#3-verify-the-hosts-file-for-the-target-environment)
  - [4. Place patch archives on the Ansible host](#4-place-patch-archives-on-the-ansible-host)
- [OIG — Oracle Identity Governance](#oig--oracle-identity-governance)
- [OAM — Oracle Access Manager](#oam--oracle-access-manager)
- [OUD — Oracle Unified Directory](#oud--oracle-unified-directory)
- [OHS — Oracle HTTP Server](#ohs--oracle-http-server)
- [OSB — Oracle Service Bus](#osb--oracle-service-bus)
- [AAG — Axway API Gateway](#aag--axway-api-gateway)
- [Running Selected Steps (Tags)](#running-selected-steps-tags)
- [Variables Reference](#variables-reference)

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
│   └── vars.yml                        # Global variables for all environments
├── inventory/
│   ├── fat/
│   │   ├── hosts                       # FAT hosts file
│   │   └── group_vars/
│   │       ├── all/vars                # FAT-wide variables (env: fat)
│   │       ├── oig_mh/vars             # ap: mh
│   │       ├── oam_ap1/vars            # ap: ap1
│   │       ├── oud_mh/vars             # ap: mh
│   │       └── ...
│   ├── dev/
│   │   ├── hosts                       # DEV hosts file
│   │   └── group_vars/
│   │       ├── all/vars                # DEV-wide variables (env: dev)
│   │       └── ...
│   ├── sat/
│   ├── tring/
│   ├── supp/
│   └── prod/
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

## Pre-patching Checklist

### 1. Verify and configure `group_vars/vars.yml`

> **This is the most critical step.** All product-specific parameters are defined here.  
> Review every section relevant to the product(s) being patched before execution.

#### Domain paths — set per environment

OIG and OAM domain names differ between environments. Set the correct values before running:

```yaml
# OIG domain paths
oig_managed_server_domain: /app/config/mserver/domains/IAMGovernanceDomain     # FAT / PROD
# oig_managed_server_domain: /app/config/mserver/domains/IAMGovernanceDomain12c  # DEV

oig_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMGovernanceDomain   # FAT / PROD
# oig_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMGovernanceDomain12c  # DEV

# OAM domain paths
oam_managed_server_domain: /app/config/mserver/domains/IAMAccessDomain
oam_admin_server_domain: /mnt/nfs/config/aserver/domains/IAMAccessDomain
```

#### WebLogic passwords

Passwords for OIG, OAM and OSB Admin Servers must be set correctly.  
**Always encrypt passwords using Ansible Vault — never store them in plain text.**

```yaml
# In group_vars/vars.yml — encrypt with ansible-vault:
oig_wls_password: "CHANGE_ME_USE_VAULT"
oam_wls_password: "CHANGE_ME_USE_VAULT"
osb_wls_password: "CHANGE_ME_USE_VAULT"
```

To encrypt a password:
```bash
ansible-vault encrypt_string 'actual_password' --name 'oig_wls_password'
ansible-vault encrypt_string 'actual_password' --name 'oam_wls_password'
ansible-vault encrypt_string 'actual_password' --name 'osb_wls_password'
```

Paste the encrypted output directly into `group_vars/vars.yml`.

#### Admin Server URLs and ports

Verify that the Admin Server URLs and ports match the target environment:

```yaml
# OIG
oig_admin_server_url: "t3://oim-mh-intvip.bck.{{ env }}.ccn2.taxud"
oig_admin_server_port: 7101
oig_managed_server_port: 14000
oig_soa_port: 8001

# OAM
oam_admin_url: "t3://oam-{{ ap }}-intvip.bck.{{ env }}.ccn2.taxud:7001"
oam_admin_server_port: 7001
oam_managed_server_port: 14100
oam_ama_server_port: 14150

# OSB
osb_admin_server_url: "t3://osb1.{{ ap }}.{{ env }}.ccn2.taxud"
osb_admin_server_port: 7001
osb_managed_server_port: 7010
```

#### Managed server names

Verify that the managed server names match the WebLogic domain configuration:

```yaml
# OIG managed servers
oig_managed_servers_node1:
  - managed_server_node1: wls_oig1
  - managed_server_node1: wls_soa1

oig_managed_servers_node2:
  - managed_server_node2: wls_oig2
  - managed_server_node2: wls_soa2

# OAM managed servers
oam_managed_servers_node1:
  - managed_server_node1: wls_oam1
  - managed_server_node1: wls_ama1

oam_managed_servers_node2:
  - managed_server_node2: wls_oam2
  - managed_server_node2: wls_ama2
```

#### Patch archive names

Verify that the patch archive filenames defined in `vars.yml` match the actual files placed in `/app/patches/`:

```yaml
# OIG
oig_bundle_archive: p34986147_122140_Linux-x86-64.zip
oig_patches_to_apply:
  - patch_archive: p36946553_122140_Generic.zip

# OAM
oam_bundle_archive: p37478538_122140_Linux-x86-64.zip
oam_patches_to_apply:
  - patch_archive: p36946553_122140_Generic.zip
  - patch_archive: p36739303_12214221222_Generic.zip

# JDK
jdk_archive: jdk-8u491-linux-x64.tar.gz

# OPatch
opatch_archive: p28186730_1394218_Generic.zip
```

#### OUD and AAG paths

```yaml
# OUD
oud_ldap_instance: /app/ldap_instance

# AAG
aag_install_dir: /app/Axway-7.7.0
aag_patch_archive: APIGateway_7.7.20240228_Core_linux-x86-64_BN01.tar.gz
```

---

### 2. Verify inventory for the target environment

Each environment has its own inventory directory under `inventory/`. The `group_vars` subdirectory inside each environment contains per-group variables — primarily the `ap` (access point / location) variable.

**Check that the correct `ap` value is set for the group being patched:**

```
inventory/<env>/group_vars/
├── all/vars              → env: <environment_name>   (e.g. env: fat)
├── oig_mh/vars           → ap: mh
├── oam_ap1/vars          → ap: ap1
├── oam_ap2/vars          → ap: ap2
├── oam_ap3/vars          → ap: ap3
├── oam_ap4/vars          → ap: ap4
├── oud_mh/vars           → ap: mh
├── oud_ap1/vars          → ap: ap1
├── oud_ap2/vars          → ap: ap2
├── oud_ap3/vars          → ap: ap3
├── ohs_ap1/vars          → ap: ap1
├── ohs_ap2/vars          → ap: ap2
├── osb_ap1/vars          → ap: ap1
...
```

Verify the `all/vars` file sets the correct environment name:

```yaml
# inventory/fat/group_vars/all/vars
env: fat
```

```yaml
# inventory/dev/group_vars/all/vars
env: dev
```

To verify the inventory is parsed correctly before running a playbook:

```bash
# List all hosts in the target group
ansible -i inventory/fat/hosts oig_mh --list-hosts

# Check what variables are resolved for a specific host
ansible -i inventory/fat/hosts oim1.mh.fat.ccn2.taxud -m debug -a "var=hostvars[inventory_hostname]"
```

---

### 3. Verify the hosts file for the target environment

The `hosts` file defines all server groups and hostnames for the environment.  
**Before running any playbook, verify that:**

- All expected servers are listed under the correct group
- Hostnames match the actual DNS names of the target servers
- Groups are correctly nested under parent groups (`:children`)

Example structure in `inventory/fat/hosts`:

```ini
[all:vars]
ansible_user=oracle
ansible_connection=ssh

[oig_mh]
oim1.mh.fat.ccn2.taxud
oim2.mh.fat.ccn2.taxud

[oig:children]
oig_mh

[oam_ap1]
oam1.ap1.fat.ccn2.taxud
oam2.ap1.fat.ccn2.taxud

[oam:children]
oam_ap1
oam_ap2
oam_ap3
oam_ap4
...
```

Verify SSH connectivity to all hosts in the target group before running the playbook:

```bash
# Test SSH connectivity
ansible -i inventory/fat/hosts oig_mh -m ping

# Test for a specific location
ansible -i inventory/fat/hosts oam_ap1 -m ping

# Test for all hosts
ansible -i inventory/fat/hosts all -m ping
```

---

### 4. Place patch archives on the Ansible host

```
/app/patches/
├── JAVA/    → jdk-8u491-linux-x64.tar.gz
│            → p28186730_1394218_Generic.zip   (OPatch)
├── OIG/     → p34986147_122140_Linux-x86-64.zip   (SPBAT bundle)
│            → p36946553_122140_Generic.zip
├── OAM/     → p37478538_122140_Linux-x86-64.zip   (SPBAT bundle)
│            → p36946553_122140_Generic.zip
│            → p36739303_12214221222_Generic.zip
├── OUD/     → OUD patch archives
├── OHS/     → OHS patch archives
├── OSB/     → p34980707_122140_Generic.zip    (SPBAT bundle)
│            → additional OSB patch archives
└── AAG/     → APIGateway_7.7.20240228_Core_linux-x86-64_BN01.tar.gz
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
- NFS `/mnt/nfs` mounted and accessible — verify: `df -h | grep mnt`
- `oig_managed_server_domain` and `oig_admin_server_domain` set correctly in `group_vars/vars.yml`
- `oig_wls_password` encrypted in `group_vars/vars.yml`

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
- `oam_managed_server_domain` and `oam_admin_server_domain` set correctly in `group_vars/vars.yml`
- `oam_wls_password` encrypted in `group_vars/vars.yml`

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
- `osb_wls_password` encrypted in `group_vars/vars.yml`

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

## Variables Reference

### Variables that must be set manually per environment (`group_vars/vars.yml`)

| Variable | Description | Example value |
|----------|-------------|---------------|
| `oig_managed_server_domain` | Path to OIG managed server domain | `/app/config/mserver/domains/IAMGovernanceDomain` |
| `oig_admin_server_domain` | Path to OIG admin server domain (NFS) | `/mnt/nfs/config/aserver/domains/IAMGovernanceDomain` |
| `oam_managed_server_domain` | Path to OAM managed server domain | `/app/config/mserver/domains/IAMAccessDomain` |
| `oam_admin_server_domain` | Path to OAM admin server domain (NFS) | `/mnt/nfs/config/aserver/domains/IAMAccessDomain` |
| `oig_wls_password` | WebLogic password for OIG Admin Server | encrypt with ansible-vault |
| `oam_wls_password` | WebLogic password for OAM Admin Server | encrypt with ansible-vault |
| `osb_wls_password` | WebLogic password for OSB Admin Server | encrypt with ansible-vault |
| `jdk_archive` | JDK archive filename | `jdk-8u491-linux-x64.tar.gz` |
| `opatch_archive` | OPatch archive filename | `p28186730_1394218_Generic.zip` |
| `oig_bundle_archive` | OIG SPBAT bundle archive filename | `p34986147_122140_Linux-x86-64.zip` |
| `oam_bundle_archive` | OAM SPBAT bundle archive filename | `p37478538_122140_Linux-x86-64.zip` |
| `osb_bundle_archive` | OSB SPBAT bundle archive filename | `p34980707_122140_Generic.zip` |
| `aag_patch_archive` | AAG patch archive filename | `APIGateway_7.7.20240228_Core_linux-x86-64_BN01.tar.gz` |

### Variables set automatically per inventory group

| Variable | File | Description |
|----------|------|-------------|
| `ap` | `inventory/<env>/group_vars/<group>/vars` | Location identifier (e.g. `mh`, `ap1`, `ap2`) |
| `env` | `inventory/<env>/group_vars/all/vars` | Environment name (e.g. `fat`, `dev`, `prod`) |

### Variables that are static (defined in `group_vars/vars.yml`, change only with product upgrade)

| Variable | Description |
|----------|-------------|
| `oracle_user` | OS user running Oracle processes (`oracle`) |
| `oracle_home_oig` | Oracle Home path for OIG binaries |
| `oracle_home_oam` | Oracle Home path for OAM binaries |
| `oig_admin_server_port` | OIG Admin Server port (`7101`) |
| `oig_managed_server_port` | OIG managed server port (`14000`) |
| `oig_soa_port` | SOA managed server port (`8001`) |
| `oam_admin_server_port` | OAM Admin Server port (`7001`) |
| `oam_managed_server_port` | OAM managed server port (`14100`) |
| `oig_managed_servers_node1` | List of OIG managed server names on node1 |
| `oig_managed_servers_node2` | List of OIG managed server names on node2 |
| `oam_managed_servers_node1` | List of OAM managed server names on node1 |
| `oam_managed_servers_node2` | List of OAM managed server names on node2 |
