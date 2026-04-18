# Cloud Production Launch Guide

> **Purpose:** Run the 4-model P2-alt production solve (6,009,159 hands × 4 opponent models × N=1000) on a rented cloud machine. Mac Mini takes ~10 days; cloud can cut that to ~2 days.
>
> **Audience:** First-time cloud renter. Click-by-click, written for a non-technical user.
>
> **Research process:** Top 3 options below were chosen by Claude Code after a Socratic pressure-test with Gemini 3 Pro on 2026-04-18. Rejected alternatives are documented at the bottom with the reason for rejection, so you can see the reasoning.

---

## TL;DR — Pick one of these 3

| | **#1 DigitalOcean** | **#2 RunPod** | **#3 Google Cloud (GCP)** |
|---|---|---|---|
| Best for | Non-technical user who wants the simplest UI and a major-brand reputation | User who wants to start *tonight* with zero waiting for quota approval, at the lowest cost | User who wants $0 out-of-pocket (if quota approved) and the fastest machine available |
| Machine | 48 vCPU CPU-Optimized Premium AMD Droplet | 64 vCPU CPU pod ("Community Cloud") | `c2d-highcpu-112` (112 vCPU on AMD EPYC) |
| Wall-clock (all 4 models) | ~3 days | ~2.5 days | ~1.7 days |
| Signup credit | $200 for new accounts (covers job) | None — prepaid (add ~$25 via credit card) | $300 for new accounts (covers job) |
| Out-of-pocket cost (with credit) | **$0** | **~$17** | **$0** |
| Quota hassle on signup | Must open a support ticket to unlock 48 vCPU (same-day approval with the copy-paste ticket below) | **None** — prepaid model skips enterprise fraud filters | New accounts hard-capped at 8–12 vCPU; **must upgrade past free trial and request a quota increase**; manual fraud review is likely |
| First-time friendliness | ★★★★★ (cleanest UI of any cloud provider) | ★★★★ (prepaid is boring; browser terminal works out-of-the-box) | ★★★ (polished but dense; account creation can hit friction) |
| How to start | Option 1 steps below | Option 2 steps below | Option 3 steps below |

**My single recommendation**, if you don't want to read further: start with **RunPod (Option 2)**. You'll be running in 10 minutes, no bureaucracy, total bill under $20. The only reason to pick DO or GCP is if you already have a relationship/habit with them.

**If you'd rather pay $0 and have a big-brand UI**, go DigitalOcean (#1). You'll burn a couple hours on the quota ticket, but it's free after the signup credit.

**If you want the absolute fastest wall-clock and don't mind jumping through GCP's fraud-review hoop**, go GCP (#3). Note: realistically this option can take a day just to get approved.

---

## Prerequisites (all options)

Before starting, the following must be done on the Mac (Claude Code will do these automatically as the session-end commit):

1. The Bug 1 + Bug 3 fixes from this session are committed + pushed to `github.com/mcoski8/tw` on branch `main`.
2. This guide is committed to the repo so you can pull it up on the cloud VM if needed.

Verify at <https://github.com/mcoski8/tw> that you see a recent commit from today mentioning Bug 1 / Bug 3 / Sprint 2b.

**Important for all 3:** After the job finishes and you've downloaded the output files, **destroy the VM immediately** to stop the meter. This is flagged in each guide but worth saying up front.

---

# Option 1: DigitalOcean (★ Simplest UI)

**Why DigitalOcean**: Of every major cloud provider, DO has the cleanest, most developer-friendly UI. Their "Droplets" are simple VMs with one-click launch and in-browser terminal access. No VPC, no security groups, no IAM — you click CREATE and you're in a shell.

**The catch**: New DO accounts are limited to ~10 vCPUs total. To rent a 48-vCPU Droplet, you need to open a support ticket. Usually approved same day with the right wording (template below).

**Estimated wall-clock**: ~3 days total for all 4 models.
**Estimated out-of-pocket**: $0 (covered by the $200 new-user signup credit).

## Step 1 — Sign up

1. Go to <https://www.digitalocean.com/> → click **Sign up**.
2. Create an account with email + password (or use Google/GitHub SSO).
3. Enter a credit card for identity verification. You get **$200 in credit, valid for 60 days**.
4. On your DO dashboard, click your avatar (top-right) → **Settings** → **Billing**. Confirm you see "$200.00 in free credits."

## Step 2 — Open the quota support ticket FIRST

Do this before trying to create the 48-vCPU droplet — the support ticket unlocks it.

1. Click your avatar → **Support** → **Create a new ticket**.
2. Category: **Billing** → **Account verification or limit increase**.
3. Paste the following as the ticket body:

```
Subject: Temporary limit increase request: 48 vCPU CPU-Optimized Premium AMD Droplet for 3 days

Hello,

I'd like to request a temporary Droplet limit increase so I can create a
single CPU-Optimized Premium AMD Droplet with 48 vCPUs (the "c-48" plan).

Use case: I am running a one-time personal data-processing job — a Rust-based
Monte Carlo probability solver for a card-game research project. This is a
batch compute job, NOT a web service and definitely NOT cryptocurrency mining.

Expected duration: approximately 60 hours of compute (about 3 days).

Action plan: once the job finishes and I download the output files
(about 220 MB total), I will destroy the Droplet the same day. I don't need
the quota increase to be permanent.

I've already verified my credit card on the account. Please let me know if
any additional verification is needed. Thanks!
```

4. Submit. Response typically arrives within 2-6 hours during US business hours.

## Step 3 — Wait for approval, then launch the Droplet

Once you get the approval email:

1. Back on the DO dashboard, top-right: **Create → Droplets**.
2. Choose an image: **Ubuntu 22.04 (LTS) x64**.
3. Choose a Droplet type: click **CPU-Optimized** → select **Premium AMD**.
4. Size: find the 48 vCPU / 96 GB RAM option. Hourly rate shown: ~$1.78/hr.
5. Choose a datacenter region: **New York 3** (any region works; NY is a good default for US users).
6. Authentication: choose **Password**. Enter a strong password you can copy-paste. **Uncheck any SSH-key-only option** — password gets you in-browser access faster.
7. Hostname: `tw-solver` (or anything).
8. Click **Create Droplet**. Wait ~30 seconds for the IP to appear.

## Step 4 — Connect via in-browser console

1. On the Droplet detail page, click **Access** in the left sidebar.
2. Click **Launch Droplet Console**. A browser terminal opens.
3. Username: `root`. Password: what you set in Step 3.

## Step 5 — Install Rust and build

Paste into the terminal:

```bash
apt-get update
apt-get install -y git build-essential pkg-config libssl-dev curl time
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustc --version
```

You'll see `rustc 1.xx.y` when it's done (~2 min).

```bash
cd ~
git clone https://github.com/mcoski8/tw.git
cd tw
cd engine && cargo build --release && cd ..
```

Another ~3 min. You're ready.

## Step 6 — Generate canonical hands and launch the solve

```bash
mkdir -p data
./engine/target/release/tw-engine enumerate-canonical --out data/canonical_hands.bin

chmod +x scripts/production_all_models.sh
nohup scripts/production_all_models.sh > data/session06/production_launch.log 2>&1 &
echo "Launched. PID: $!  Safe to close this browser tab — nohup keeps it running."
```

## Step 7 — Monitor (any time in the next few days)

Re-open the Droplet console (Step 4) and paste:

```bash
cd ~/tw

# Overall progress
tail -10 data/session06/production_launch.log

# Per-model ETA
for f in data/session06/prod_*.log; do
    echo "=== $f ==="
    tail -3 "$f"
done

# Is the process still alive?
pgrep -af "tw-engine solve" || echo "Job stopped (check if it's complete or crashed)."
```

If you see "Job stopped" but not all 4 files are present in `data/best_response/`, just re-run the script:

```bash
cd ~/tw && chmod +x scripts/production_all_models.sh && nohup scripts/production_all_models.sh > data/session06/production_launch.log 2>&1 &
```

The `solve` binary's append-only writer resumes automatically — no data loss.

## Step 8 — Download results (when all 4 files present in `~/tw/data/best_response/`)

Easiest approach for a non-technical user:

1. In the DO dashboard, navigate to your Droplet.
2. Use the **"Files"** tab (if available) or download via SCP on your Mac:

```bash
# On your Mac (not the DO console), open Terminal.app
cd /Users/michaelchang/Documents/claudecode/taiwanese/data
mkdir -p best_response_cloud
# Replace <DROPLET_IP> with the IP shown in the DO dashboard.
# When prompted for password, paste the root password from Step 3.
scp -r root@<DROPLET_IP>:~/tw/data/best_response/ best_response_cloud/
```

## Step 9 — DESTROY the Droplet (critical)

1. Back on DO dashboard → your Droplet → **Destroy** in the left sidebar.
2. **Destroy entire Droplet**. Type the droplet name to confirm.

Row disappears. You are no longer being billed.

---

# Option 2: RunPod (★ Cheapest, Fastest to Start)

> ⚠️ **DO NOT PICK A GPU POD.** RunPod's homepage and deploy flow default to showing **GPU** pods (H100, H200, A100, RTX, B200, L40, MI300X — any of these names = GPU). Those cost $3-15/hour and **we don't need a GPU** — our solver is pure CPU. Click the **CPU tab** on the deploy page. If the price tag shows a GPU model name, it's the wrong pod. CPU pods cost $0.05-0.70/hour depending on vCPU count.

**Why RunPod**: RunPod is designed for ML workloads (mostly GPU) but they have "Community Cloud" CPU pods that are the cheapest credible option for this job. Their billing model is **prepaid** — you load $25, run your pod, and it stops when the balance is depleted. This prepaid model means RunPod doesn't have the enterprise fraud filters that gate big VMs at GCP/DO, so **there's no quota ticket and no multi-hour wait**. You can be running within 10 minutes of account creation.

**Estimated wall-clock**: ~2.5 days (64 vCPU pod).
**Estimated out-of-pocket**: ~$17-20 total.

## Step 1 — Sign up

1. Go to <https://www.runpod.io/> → **Sign up**.
2. Create with email + password (or Google SSO).
3. Verify your email.

## Step 2 — Add billing credit

**Critical**: if your balance hits $0 during the run, RunPod **terminates the pod and deletes all data**. Over-provision: for a $17 job, load $30.

1. Top-right avatar → **Billing**.
2. **Add Credits** → $30.
3. Enter credit card. Charge goes through Stripe. Credit appears immediately.

## Step 3 — Launch a CPU pod

1. Left sidebar: **Pods** → **Deploy**.
2. **CRITICAL**: at the top of the Deploy page you'll see tabs. Click the **CPU** tab. If you stay on the GPU tab you'll see expensive 360+ GB VRAM machines — those are all wrong for our job and cost $3-15/hr.
3. Sanity check you're on CPU: prices should be well under $1/hr. If prices are above $3/hr, you're still on GPU tab.
4. Filter for a pod with **64 vCPUs**. Select it. Price will show ~$0.25-0.35/hr. (A 128-vCPU pod for ~$0.60/hr is even better — grab that if offered — this is the "sub-24-hour" path.)
5. Template: select **RunPod Base** (Ubuntu 22.04, no extras). This is the default; don't pick a Docker image from the list — you don't need one.
6. Container Disk: **50 GB** (default).
7. Volume Disk: **0 GB** — the 216 MB of output is small; container disk is fine.
8. Name: `tw-solver`.
9. Click **Deploy On-Demand**.
10. Wait ~30 seconds. The pod row turns green ("Running").

## Step 4 — Open the web terminal

1. Click the pod row → **Connect** button (top-right of the pod detail pane).
2. **Start Web Terminal** → opens a browser terminal. No SSH keys, no password.

## Step 5 — Install Rust and build

Same as DO, paste:

```bash
apt-get update
apt-get install -y git build-essential pkg-config libssl-dev curl time
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustc --version

cd /workspace
git clone https://github.com/mcoski8/tw.git
cd tw
cd engine && cargo build --release && cd ..
```

Note: `/workspace` is RunPod's convention for the working directory. Output should go here.

## Step 6 — Generate canonical hands and launch

```bash
mkdir -p data
./engine/target/release/tw-engine enumerate-canonical --out data/canonical_hands.bin

chmod +x scripts/production_all_models.sh
nohup scripts/production_all_models.sh > data/session06/production_launch.log 2>&1 &
echo "Launched. PID: $!"
```

## Step 7 — Monitor

Reconnect via Web Terminal any time (pod stays running). Paste:

```bash
cd /workspace/tw
tail -10 data/session06/production_launch.log
for f in data/session06/prod_*.log; do echo "=== $f ==="; tail -3 "$f"; done
pgrep -af "tw-engine solve" || echo "Job stopped."
```

## Step 8 — Download results

RunPod's web UI has a file browser:

1. In the pod detail pane → **Connect** → **Start Jupyter Lab** (even though we're not using Jupyter for compute, its file browser is convenient).
2. Navigate to `/workspace/tw/data/best_response/` → right-click each file → **Download**.

Or from your Mac's Terminal, use `scp` with the runpodctl CLI (see <https://docs.runpod.io/cli/install-runpodctl>).

## Step 9 — **TERMINATE** the pod

Do not merely **Stop** — stopping preserves the volume disk but doesn't stop all charges on RunPod. **Terminate** deletes everything.

1. Pod detail → top-right menu → **Terminate Pod**.
2. Confirm. Pod row disappears.

Whatever balance is left on your RunPod account stays there (or refund via support).

---

# Option 3: Google Cloud (GCP) — Biggest Machine, $0 if Quota Approved

**Why GCP**: $300 free credit for new accounts covers the entire job; the `c2d-highcpu-112` machine (56 physical AMD EPYC cores) finishes the job in ~1.7 days, the fastest of the three options.

**The hurdle**: GCP hard-caps new trial accounts at 8-12 vCPUs per region. To get the 112-vCPU machine you must:
1. Upgrade from free trial to paid account (still get the $300 credit).
2. Submit a quota increase for 128 CPUs.
3. Wait for GCP's manual fraud review (same-day to 24 hours).

If that's too much bureaucracy, skip to Option 1 or 2.

**Estimated wall-clock**: ~1.7 days total.
**Estimated out-of-pocket**: $0 (covered by $300 signup credit).

## Step 1 — Create a Google Cloud account

1. Go to <https://cloud.google.com/> → **Get started for free**.
2. Sign in with Google account.
3. Enter credit card details (required even for the $300 trial).
4. Click **Start my free trial**.

## Step 2 — Create a project

1. Top-left project dropdown → **New Project**.
2. Name: `tw-poker-solver`.
3. Click **Create**. Wait 15 seconds, then select the new project from the dropdown.

## Step 3 — Enable Compute Engine

1. Hamburger menu (≡) → **Compute Engine → VM instances**.
2. If you see "Enable billing" or "Enable Compute Engine API" banners, click each.
3. Wait 1-2 minutes.

## Step 4 — Upgrade past free trial (required for big VM)

1. Top-right → **Activate** (or "Upgrade to paid account").
2. Accept. You still keep the $300 credit.

## Step 5 — Request a quota increase

1. Hamburger → **IAM & Admin → Quotas & System Limits**.
2. Filter: type `CPUs` in the filter box.
3. Look for **"CPUs"** in region `us-central1`. The current limit is probably 24.
4. Check the row → **Edit Quotas** (top).
5. New limit: **128**.
6. Description box — paste this:

```
One-time personal batch compute job. Rust-based Monte Carlo probability
solver for a card-game research project (non-commercial). Plan to provision
a single c2d-highcpu-112 instance for approximately 40 hours and then
destroy it. Not a web service, not cryptocurrency mining. Will stay within
the $300 free trial credit.
```

7. Submit. Response: usually within hours. You'll get an email.

## Step 6 — Launch the VM

Once quota is approved:

1. Compute Engine → **VM instances → CREATE INSTANCE**.
2. Fill:
   - **Name**: `tw-solver`
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - Machine configuration tab: **Compute-optimized** → **C2D** series → `c2d-highcpu-112`
   - Boot disk: **Change** → OS: **Debian 12**, Size: 50 GB → **Select**
3. Expand **Advanced options → Management → Startup script**:

```bash
#!/bin/bash
apt-get update
apt-get install -y git build-essential pkg-config libssl-dev curl time
su -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y' $(logname 2>/dev/null || echo root)
```

4. Verify the estimated cost shows ~$3.40/hr. Click **Create**.

## Step 7 — SSH via browser

1. VM list → `tw-solver` row → **SSH** button.
2. New browser tab opens with a shell. If it says "startup script still running," wait 2-3 min and reopen.

## Step 8 — Build + run

```bash
# Verify Rust installed (startup script does this)
if ! command -v cargo &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

cd ~
git clone https://github.com/mcoski8/tw.git
cd tw
cd engine && ~/.cargo/bin/cargo build --release && cd ..

mkdir -p data
./engine/target/release/tw-engine enumerate-canonical --out data/canonical_hands.bin

chmod +x scripts/production_all_models.sh
nohup scripts/production_all_models.sh > data/session06/production_launch.log 2>&1 &
echo "Launched. PID: $!"
```

**Critical:** using `nohup` + `&` lets the job survive when you close the browser tab. If you just run the command without `nohup`, closing the tab kills the job and you'll have to restart.

## Step 9 — Monitor

Re-open SSH any time. Paste:

```bash
cd ~/tw
tail -10 data/session06/production_launch.log
for f in data/session06/prod_*.log; do echo "=== $f ==="; tail -3 "$f"; done
pgrep -af "tw-engine solve" || echo "Job stopped."
```

## Step 10 — Download

Back on your Mac:

```bash
# Install gcloud CLI if you haven't: https://cloud.google.com/sdk/docs/install
cd /Users/michaelchang/Documents/claudecode/taiwanese/data
mkdir -p best_response_cloud
gcloud compute scp --recurse --zone us-central1-a tw-solver:~/tw/data/best_response/ best_response_cloud/
```

Or use the in-browser SSH's gear icon → **Download file** per file.

## Step 11 — DELETE the VM

1. Compute Engine → VM instances → check `tw-solver` → **Delete**.
2. Confirm.

---

# What I rejected (and why)

Briefly, so you don't wonder "should I have considered X":

| Provider | Rejected because |
|---|---|
| **AWS (EC2 / Lightsail)** | EC2 is genuinely hostile to first-time users: VPCs, security groups, IAM, key pairs — the click-by-click guide would be 15 pages. Lightsail is simpler but capped at 8 vCPUs, which is slower than your Mac Mini. |
| **Hetzner Cloud** | Cheapest per core, but for US-based first-time users the KYC process (passport photo verification) is slow and can reject non-EU applicants. Saves ~$35 vs DO, but DO has $200 signup credit so Hetzner is *more* expensive out of pocket. |
| **Azure** | $200 signup credit is fine but the console is even denser than AWS for a non-technical user. Not worth it vs GCP. |
| **Oracle Cloud** | "Always Free" ARM VMs sound appealing but (a) notoriously capacity-constrained — you often can't actually provision them, and (b) the paid tiers offer no UX advantage over DO. |
| **Fly.io / Railway / Render** | Designed for long-running web services. Fly.io caps at 8 dedicated vCPUs; Render caps at 32 and is priced like an enterprise tool. Wrong fit for a one-time batch job. |
| **Lambda Labs, Vast.ai** | GPU-first; CPU offerings are afterthoughts. RunPod is the exception — it has real CPU pods. |
| **Latitude.sh / Equinix Metal** | Bare-metal hourly is great in principle but signup requires SSH key management (not beginner-friendly) and pricing starts higher than RunPod. |
| **Spot / preemptible pricing** on any provider | The solver has crash-safe resume, so technically spot is safe. But every preemption = another SSH session, another "did it break?" moment for a non-technical user. Savings of ~$20-60 aren't worth the anxiety. Use on-demand. |

---

# Sub-24-hour variant (if you want results faster)

The default guide targets ~2.5-3 days wall-clock. If you want sub-24-hour completion, the workload is embarrassingly parallel across 4 models AND across the 6M hands, so either a **bigger machine** or **multiple machines in parallel** works. A GPU does NOT help — the solver is branchy integer code and lookup-table-memory-bound, exactly the pattern GPUs are worst at. Commercial poker solvers (PioSolver etc.) are CPU-only for the same reason.

## Sub-24-hour approach A — RunPod with a bigger CPU pod (RECOMMENDED)

**Wall-clock: ~17-19 hours. Cost: ~$15-25. Complexity: same as the single-pod guide.**

RunPod's Community Cloud rotates through available CPU pods based on which GPU host machines aren't currently rented for ML work. **Pods with 128-192 vCPUs show up regularly at $0.60-1.20/hr.** When you reach the pod selection screen (Option 2, Step 3), filter for CPU pods and pick the largest one you see under $1.50/hr.

If a 128-vCPU pod is available: follow Option 2 exactly as written. Wall-clock becomes ~19 hours instead of 2.5 days. Total bill ~$15.

If a 192-vCPU pod is available: ~15-17 hours. Total bill ~$20-25.

## Sub-24-hour approach B — RunPod with 4 pods in parallel (EXPERIENCED USER)

**Wall-clock: ~17 hours. Cost: ~$20. Complexity: HIGH — only try this if you're OK with managing 4 browser tabs.**

> ⚠️ **Gemini 3 Pro explicitly pushed back on this approach for non-technical users.** Managing 4 separate web terminals, 4 separate progress logs, 4 separate downloads, and 4 separate teardowns multiplies the surface area for human error. Forgetting to terminate even one pod drains your prepaid balance. **If you forget you have 4 pods and close your laptop, one may keep running for days.** Use this only if you're comfortable with command-line process management.

If you accept that risk:

1. Launch 4 separate RunPod CPU pods, each with 64 vCPU, following Option 2 Steps 1-4 four times (you can name them `tw-1`, `tw-2`, `tw-3`, `tw-4`).
2. On each pod, do the same Rust install + git clone + build from Option 2 Step 5.
3. On each pod, run ONE model instead of all four. Inside each pod's terminal, paste ONE of these (different on each pod):

   **Pod 1 (`tw-1`):**
   ```bash
   mkdir -p data/best_response
   nohup /workspace/tw/engine/target/release/tw-engine solve \
       --canonical /workspace/tw/data/canonical_hands.bin \
       --lookup /workspace/tw/data/lookup_table.bin \
       --out /workspace/tw/data/best_response/mfsuitaware_mixed90.bin \
       --samples 1000 --seed 12648430 --block-size 2000 \
       --opponent mixed --mix-base mfsuitaware --mix-p 0.9 \
       > /workspace/tw/data/prod_mfsuitaware.log 2>&1 &
   echo "Launched PID: $!"
   ```

   **Pod 2 (`tw-2`):** same command but `--mix-base omaha` and `--out /workspace/tw/data/best_response/omahafirst_mixed90.bin`, log `prod_omahafirst.log`.

   **Pod 3 (`tw-3`):** `--mix-base topdef` → `topdefensive_mixed90.bin`, log `prod_topdefensive.log`.

   **Pod 4 (`tw-4`):** `--opponent weighted` (no mix flags) → `randomweighted.bin`, log `prod_randomweighted.log`.

4. Monitor each pod independently. When all 4 are done, download each pod's single `.bin` file, then **terminate all 4 pods**.

## Sub-24-hour approach C — GCP bigger VM

**Wall-clock: ~15-19 hours. Cost: $0 out of pocket if you already cleared the quota review.**

Follow Option 3 (GCP) exactly, but in Step 5 request quota for `200` CPUs instead of `128`, and in Step 6 pick machine type `c2d-highcpu-224` (224 vCPU = 112 physical AMD EPYC cores) or `c3-highcpu-176` (176 vCPU Intel Sapphire Rapids). Cost on-demand: ~$6.80-9.50/hr; $120-180 on-demand, $0 after the $300 free trial credit. Wall-clock all 4 models sequentially: ~15-19 hours.

This is the absolute fastest option, but only viable if you've already sunk the time into GCP's account upgrade + quota review (typically 4-24 hours of bureaucracy).

## Which sub-24 approach should YOU pick?

- **First-time cloud user, want simplicity**: Approach A. Same simplicity as default RunPod guide, just pick a bigger pod at deployment time.
- **Willing to juggle 4 tabs + comfortable with the terminate-everything discipline**: Approach B. Cheapest at $20 total.
- **Already have GCP account + already cleared quota**: Approach C. Fastest absolute.
- **Want to maximize simplicity and don't mind 2.5 days**: just use the default Option 2 guide (64-vCPU, sequential). Still 4× faster than your Mac Mini.

---

# Common gotchas (all options)

1. **Closing the browser tab kills the job — unless you used `nohup`.** The scripts already use it, so you're fine, but if you copy-paste any other long-running command, remember `nohup cmd > log 2>&1 &`.
2. **Data deletion when the VM is destroyed**. ALWAYS download `data/best_response/*.bin` before destroying.
3. **Billing alerts.** On DO, GCP, Azure you can set a billing alert at, say, $50 to email you — recommended. RunPod doesn't need this (prepaid).
4. **The 4 output files are idempotent-by-header.** If you destroy and re-create the VM later, you can continue the job from where it left off if you re-upload the partial `.bin` files to the same path. But the easy path is: let all 4 complete on one machine, then destroy.
5. **Expected total data transfer out**: ~220 MB. Well under the 1 GB/month free tier of any provider. No bandwidth cost to worry about.
6. **Time zones**: all of these providers bill in their local time (DO = NY, RunPod = US various, GCP = PST). Don't worry about it — hourly billing with minute granularity.

---

# Session-end action from Claude Code

To make this guide usable, Claude Code will:
1. Commit the bug fixes + scripts + this guide to the local repo.
2. Push to `github.com/mcoski8/tw` on `main`.
3. Verify push succeeded so the cloud `git clone` will work.

You can verify after waking up: go to <https://github.com/mcoski8/tw>, check the latest commit message mentions Bug 1 + Bug 3 + Sprint 2b.
