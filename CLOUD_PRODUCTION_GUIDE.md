# Cloud Production Launch Guide

> **Purpose:** Run the 4-model P2-alt production solve (6,009,159 hands × 4 opponent models × N=1000) on a rented cloud machine. Mac Mini takes ~10 days; cloud can cut that to ~2 days.
>
> **Audience:** First-time cloud renter. Click-by-click, written for a non-technical user.
>
> **Research process:** Top 3 options below were chosen after a Socratic pressure-test with Gemini 3 Pro on 2026-04-18 and re-verified against current live pricing on 2026-04-19. Rejected alternatives are documented at the bottom.

---

## ⚠️ READ THIS FIRST — None of these are monthly commitments

If you saw the prices below and thought "that's a monthly subscription" — it isn't. All three providers bill **only while your virtual machine is running**. The moment you click **Destroy** / **Terminate** / **Delete**, the meter stops and you stop paying. There is no contract, no minimum term, no auto-renewal. You can use it for 4 hours and pay 4 hours.

When you see "$1.78/hour" on a cloud provider page, that is the **metered rate**, not a subscription. Think of it like a taxi meter: it ticks up while the engine is running, and when you stop the engine, the meter stops.

The three options below are ranked by how strongly they **protect you from accidentally overspending**:

- **RunPod** is **structurally impossible to overspend.** You deposit $30 (or $50, or whatever you pick); the system physically cannot charge you more than that. When your deposit runs out, the pod terminates. No surprise bills.
- **Google Cloud (GCP)** gives you a **$300 Welcome credit** valid for 90 days. Until you explicitly click "Upgrade to Paid" (which you never have to click), your bill cannot exceed $300 — the credit IS your hard cap.
- **DigitalOcean** gives you a **$200 credit** valid for 60 days, and Droplets have a **monthly price cap** — even if you forget to destroy a 48-vCPU Droplet and leave it running for an entire calendar month, the bill for that Droplet is capped at its advertised monthly rate. It cannot run away.

All three charge **per-second** (with a 60-second minimum on DO and GCP). Destroy = meter stops within the second.

---

## TL;DR — Pick one of these 3

| | **#1 RunPod** ⭐ | **#2 Google Cloud (GCP)** | **#3 DigitalOcean** |
|---|---|---|---|
| Why you'd pick it | **Cannot overspend** — deposit is your hard ceiling | $300 credit covers the whole job + **fastest** wall-clock | $200 credit covers the whole job + simplest UI |
| Billing model | Strictly prepaid, per-second, **no credit card auto-charge** | Per-second, 1-min min; $300 credit acts as hard cap until you upgrade | Per-second, 60-sec min; monthly price cap safety net |
| Machine | 32 vCPU CPU pod | `c2d-highcpu-112` (112 vCPU AMD EPYC) | 48 vCPU CPU-Optimized Premium AMD Droplet |
| Wall-clock (all 4 models) | ~4.9 days | ~1.3–1.7 days | ~3 days |
| Signup credit | None | **$300** for 90 days | **$200** for 60 days |
| Out-of-pocket cost | ~$110 (from your prepaid deposit) | **$0** (within credit) | **$0** (within credit) |
| Setup friction | ~10 min — no quota tickets | 4-24 hr quota review + account upgrade | 2-6 hr support ticket to unlock 48 vCPU |
| Overspend-risk score | **Zero** — hard-capped by deposit | Very low — hard-capped by credit | Low — hard-capped by monthly cap on the Droplet |
| First-time friendliness | ★★★★★ | ★★★ | ★★★★★ |
| Jump to section | [RunPod →](#runpod--ranked-1) | [GCP →](#google-cloud-gcp--ranked-2) | [DigitalOcean →](#digitalocean--ranked-3) |

**Single recommendation if overspend anxiety is your #1 concern: RunPod.** You deposit what you can afford to lose, full stop. Worst case: pod dies with data you can re-run. No credit card surprises.

**Single recommendation if $0-out-of-pocket is your #1 concern: Google Cloud.** The $300 trial credit covers the fastest machine and the fastest wall-clock, and the trial itself cannot become a paid subscription without you explicitly clicking an "Upgrade" button. Per-usage billing model explained in full below.

---

## Prerequisites (all options)

Before starting, the following must already be true (Claude Code handled these in the session-end commit):

1. The Bug 1 + Bug 3 fixes are committed + pushed to `github.com/mcoski8/tw` on branch `main`.
2. This guide is committed to the repo so you can pull it up on the cloud VM if needed.

Verify at <https://github.com/mcoski8/tw> that you see a recent commit mentioning Bug 1 / Bug 3 / Sprint 2b.

**Universal rule:** After the job finishes and you've downloaded the output files, **destroy the VM immediately** to stop the meter. This is flagged in each guide but worth saying up front.

---

# RunPod — ranked #1

**Why RunPod is #1**: It's the only option where overspending is **physically impossible**. You deposit $30 (or any amount you pick); RunPod cannot charge you more than your deposit. Billing is strictly **prepaid, per-second**, with no credit card kept on file for auto-charging. Deploy takes 10 minutes. No quota tickets, no fraud reviews.

**The trade-off**: RunPod's CPU pods cap at 32 vCPUs (not a pricing choice — that's just their CPU ceiling), so wall-clock is ~5 days vs. ~3 on DO or ~1.7 on GCP. You also pay real money (~$110) out of pocket since RunPod has no signup credit. But you pay it **up front** from a prepaid balance, not after the fact from a charged card.

**Estimated wall-clock**: ~4.9 days (32 vCPU pod).
**Estimated out-of-pocket**: ~$110 total (pay from prepaid deposit).
**Recommended deposit**: $140 (30% safety margin over the ~$110 estimate so you don't run out mid-job and lose the pod).

## Step 1 — Sign up

1. Go to <https://www.runpod.io/> → **Sign up**.
2. Create with email + password (or Google SSO).
3. Verify your email.

## Step 2 — Add billing credit (this IS your spending cap)

**Critical**: if your balance hits $0 during the run, RunPod **terminates the pod and deletes all data**. Over-provision.

1. Top-right avatar → **Billing**.
2. **Add Credits** → **$140**.
3. Enter credit card. Charge goes through Stripe. Credit appears immediately.

Note: once that $140 is deposited, **that is the absolute maximum the job can cost you**. If your estimate was wrong or the job runs twice as long as expected, RunPod terminates the pod when the $140 is consumed. It cannot keep charging.

## Step 3 — Launch a CPU pod (not a GPU pod)

1. Left sidebar: **Pods** → **Deploy**.
2. **CRITICAL**: at the top of the Deploy page there are tabs. Click the **CPU** tab. If you stay on the GPU tab you'll see expensive machines (H100, A100, B200, L40, MI300X — all GPU names) at $3-15/hr. Those are wrong for our job. Our solver is pure CPU code.
3. Sanity check: on the CPU tab, prices should be well under $1.50/hr. If you're seeing $3+/hr, you're still on GPU.
4. Select the **32 vCPU / 64 GB RAM** pod. Price: verify in console, expected around **$0.96/hr** as of April 2026. This is RunPod's CPU ceiling — no 64+ vCPU CPU pods exist. (There's also a "5 GHz" high-clock tier at a premium, but it gives you *fewer cores*, which hurts this workload. Stick with the standard 32 vCPU.)
5. Template: select **RunPod Base** (Ubuntu 22.04). Don't pick a Docker image from the list — you don't need one.
6. Container Disk: **50 GB** (default).
7. Volume Disk: **0 GB** — the 216 MB of output is small; container disk is fine.
8. Name: `tw-solver`.
9. Click **Deploy On-Demand**.

> ⚠️ **Do NOT click "Savings Plan" or "Reserved"** — those are 3-month or 6-month prepaid commitments. You want **On-Demand**, which is pure per-second billing drawn from your deposit with no commitment term.

10. Wait ~30 seconds. The pod row turns green ("Running").

## Step 4 — Open the web terminal

1. Click the pod row → **Connect** button (top-right of the pod detail pane).
2. **Start Web Terminal** → opens a browser terminal. No SSH keys, no password.

## Step 5 — Install Rust and build

Paste into the terminal:

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

Note: `/workspace` is RunPod's convention for the persistent working directory. Output goes here.

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

Also glance at your **Billing** page occasionally — watch the remaining balance tick down. If you notice it burning too fast, you can terminate early.

## Step 8 — Download results

RunPod's web UI has a file browser via Jupyter Lab:

1. In the pod detail pane → **Connect** → **Start Jupyter Lab**.
2. Navigate to `/workspace/tw/data/best_response/` → right-click each file → **Download**.

Or from your Mac's Terminal, use `scp` with the runpodctl CLI (see <https://docs.runpod.io/cli/install-runpodctl>).

## Step 9 — **TERMINATE** the pod

Do not merely **Stop** — stopping preserves volume disk and some charges continue. **Terminate** deletes everything.

1. Pod detail → top-right menu → **Terminate Pod**.
2. Confirm. Pod row disappears.

Whatever balance is left on your RunPod account stays there for next time, or you can contact support for a refund.

---

# Google Cloud (GCP) — ranked #2

**Why GCP**: The **$300 free-trial Welcome credit** covers the entire job with room to spare, and the `c2d-highcpu-112` machine (112 vCPU AMD EPYC, 56 physical cores) finishes the 4-model solve in ~1.3-1.7 days — the fastest of the three options. Billing is **per-second with a 1-minute minimum**.

**The hurdle**: GCP hard-caps new trial accounts at ~8-24 vCPUs per region. To get the 112-vCPU machine you must (a) upgrade from free trial to paid account (you still keep the $300 credit), and (b) submit a CPU quota increase. Manual fraud review takes same-day to 24 hours.

**Estimated wall-clock**: ~1.3-1.7 days total.
**Estimated out-of-pocket**: $0 (covered by $300 signup credit; `c2d-highcpu-112` × ~40 hours ≈ $169).

## Understanding GCP's per-usage pricing model (read before signing up)

This section exists because first-time GCP users sometimes think the free trial is a trap. It isn't — but you should understand why.

### What "per-usage" actually means on GCP

- **Every resource you create is billed by the second it exists**, with a 1-minute minimum. You create a VM, it starts running, the meter starts. You delete the VM, meter stops within seconds. There is **no monthly commitment, no minimum term, no contract**. You delete, you stop paying for that resource.

- **The $300 Welcome credit is your hard cap during the trial.** Until you click the explicit "Upgrade to Paid" / "Activate" button, your account cannot be charged beyond what the credit can absorb. When the $300 runs out (or 90 days pass, whichever comes first), the trial ends and GCP stops all resources unless you've upgraded. No surprise credit-card charge.

- **Free trial ends automatically, not by subscription renewal.** Trial end = either $300 consumed OR 90 days elapsed. There is no "month 2" that starts billing.

- **Sustained Use Discounts (SUDs)** apply automatically with no commitment. If a VM runs more than 25% of the month, GCP auto-reduces the price. Zero commitment needed.

- **⚠️ AVOID "Committed Use Discounts" (CUDs).** These are the one GCP pricing feature that IS a commitment — you commit to 1 or 3 years of usage in exchange for 20-55% off. Do **not** click anything labeled "CUD," "Committed Use Discount," "Reservations," or "Savings Plan." For a one-time job, stick with pure on-demand pricing (the default).

### What you need to avoid clicking

During setup you want to **stay on the free trial** as long as possible. Two specific steps in this guide ask you to upgrade — those are required because GCP blocks large VMs on trial-only accounts, not because upgrading makes you pay monthly.

After upgrading: any spending past the $300 credit will be billed to your card. So until this job is done, **treat the $300 as your budget, and set a billing alert at $250** (Step 5b below) to be safe.

### Will GCP auto-bill me after my trial ends?

Not unless you explicitly upgrade. If you stay on the free trial and the 90 days lapse, GCP stops your services and doesn't charge your card. If you **do** upgrade mid-trial to unlock a bigger VM (required for this job), then yes, once the $300 credit is exhausted you start paying usage fees — but only for resources you actively have running. Destroying the VM after the job stops all further charges.

---

## Step 1 — Create a Google Cloud account

1. Go to <https://cloud.google.com/> → **Get started for free**.
2. Sign in with Google account.
3. Enter credit card details (required for identity verification — card is NOT charged during the free trial).
4. Click **Start my free trial**.

Confirm in the Billing section that you see "$300 credit, expires in 90 days."

## Step 2 — Create a project

1. Top-left project dropdown → **New Project**.
2. Name: `tw-poker-solver`.
3. Click **Create**. Wait 15 seconds, then select the new project from the dropdown.

## Step 3 — Enable Compute Engine

1. Hamburger menu (≡) → **Compute Engine → VM instances**.
2. If you see "Enable billing" or "Enable Compute Engine API" banners, click each.
3. Wait 1-2 minutes.

## Step 4 — Upgrade past free trial (required for big VM, but you keep the $300)

This is the step that sounds scary but isn't.

1. Top-right → **Activate** (or "Upgrade to paid account").
2. Accept. **You keep the full unused $300 credit** — the upgrade just unlocks the ability to provision larger VMs. You won't actually be billed to your card until the $300 is consumed.

## Step 5a — Request a quota increase

1. Hamburger → **IAM & Admin → Quotas & System Limits**.
2. Filter: type `CPUs` in the filter box.
3. Look for **"CPUs"** in region `us-central1`. The current limit is likely 24.
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

## Step 5b — Set a billing alert (strongly recommended)

Before you launch a VM, cap the blast radius.

1. Hamburger → **Billing → Budgets & alerts**.
2. **Create Budget**.
3. Name: `tw-solver-safety-net`.
4. Projects: `tw-poker-solver`.
5. Target amount: `$250`.
6. Alerts at: `50%`, `90%`, `100%`.
7. Email: your email address.
8. Save.

Now if spend gets anywhere near your credit cap, you'll get emails. (This doesn't auto-kill the VM — GCP doesn't support that out of the box — but it gives you time to react.)

## Step 6 — Launch the VM

Once quota is approved:

1. Compute Engine → **VM instances → CREATE INSTANCE**.
2. Fill:
   - **Name**: `tw-solver`
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - Machine configuration tab: **Compute-optimized** → **C2D** series → `c2d-highcpu-112`
   - Boot disk: **Change** → OS: **Debian 12**, Size: 50 GB → **Select**

> ⚠️ **Do NOT click anything under "VM provisioning model" that says "Spot" unless you accept the risk.** Spot is ~60% cheaper but GCP can pre-empt (kill) your VM at any time. Our solver has crash-safe resume so it's technically fine, but for a non-technical first-timer, stick with **Standard** (the default) — it's covered by your credit anyway.

3. Expand **Advanced options → Management → Startup script**:

```bash
#!/bin/bash
apt-get update
apt-get install -y git build-essential pkg-config libssl-dev curl time
su -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y' $(logname 2>/dev/null || echo root)
```

4. Check the estimated cost panel on the right — should read around **$4.22/hr** as of April 2026. A 40-hour run = ~$169 → fits well under the $300 credit.
5. Click **Create**.

## Step 7 — SSH via browser

1. VM list → `tw-solver` row → **SSH** button.
2. A new browser tab opens with a shell. If it says "startup script still running," wait 2-3 min and reopen.

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

**Critical:** `nohup ... &` lets the job survive when you close the browser tab. Without it, closing the tab kills the job.

## Step 9 — Monitor

Re-open SSH any time. Paste:

```bash
cd ~/tw
tail -10 data/session06/production_launch.log
for f in data/session06/prod_*.log; do echo "=== $f ==="; tail -3 "$f"; done
pgrep -af "tw-engine solve" || echo "Job stopped."
```

Also check **Billing → Overview** in the console periodically — you'll see real-time credit consumption.

## Step 10 — Download

Back on your Mac:

```bash
# Install gcloud CLI if you haven't: https://cloud.google.com/sdk/docs/install
cd /Users/michaelchang/Documents/claudecode/taiwanese/data
mkdir -p best_response_cloud
gcloud compute scp --recurse --zone us-central1-a tw-solver:~/tw/data/best_response/ best_response_cloud/
```

Or use the in-browser SSH's gear icon → **Download file** per file.

## Step 11 — **DELETE** the VM (critical)

**This is the step that stops the meter.** Without deletion, the VM keeps billing against your credit even after your job finishes.

1. Compute Engine → VM instances → check `tw-solver` → **Delete**.
2. Confirm.

Row disappears. You are no longer being billed.

### Optional: close the GCP account entirely after the job

If you want belt-and-suspenders assurance of zero future billing:

1. Hamburger → **Billing** → **Close billing account**.
2. Confirm.

This terminates billing permanently. You can always re-enable later if you want to use GCP again.

---

# DigitalOcean — ranked #3

**Why DigitalOcean**: Cleanest UI of any major cloud provider, one-click Droplet launch, in-browser terminal. $200 signup credit covers the entire job. Since January 2026, billing is **per-second with a 60-second minimum**, and every Droplet has a **monthly price cap** — even if you forget to destroy a 48-vCPU Droplet and leave it running for a full calendar month, the bill for that Droplet cannot exceed its advertised monthly price. This is a safety net specific to DO.

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

## Step 3 — Set a billing alert (recommended)

1. Avatar → **Settings** → **Billing**.
2. **Billing Alerts** → set at $150 (i.e. 75% of the $200 credit).
3. Enter your email.

## Step 4 — Wait for approval, then launch the Droplet

Once you get the approval email:

1. Back on the DO dashboard, top-right: **Create → Droplets**.
2. Choose an image: **Ubuntu 22.04 (LTS) x64**.
3. Choose a Droplet type: click **CPU-Optimized** → select **Premium AMD**.
4. Size: find the 48 vCPU / 96 GB RAM option. Hourly rate shown: ~$1.78/hr. (Confirm on the page — prices occasionally tick.)
5. Choose a datacenter region: **New York 3** (any region works; NY is a good default for US users).
6. Authentication: choose **Password**. Enter a strong password you can copy-paste. **Uncheck any SSH-key-only option** — password gets you in-browser access faster.
7. Hostname: `tw-solver`.
8. Click **Create Droplet**. Wait ~30 seconds for the IP to appear.

## Step 5 — Connect via in-browser console

1. On the Droplet detail page, click **Access** in the left sidebar.
2. Click **Launch Droplet Console**. A browser terminal opens.
3. Username: `root`. Password: what you set in Step 4.

## Step 6 — Install Rust and build

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

## Step 7 — Generate canonical hands and launch the solve

```bash
mkdir -p data
./engine/target/release/tw-engine enumerate-canonical --out data/canonical_hands.bin

chmod +x scripts/production_all_models.sh
nohup scripts/production_all_models.sh > data/session06/production_launch.log 2>&1 &
echo "Launched. PID: $!  Safe to close this browser tab — nohup keeps it running."
```

## Step 8 — Monitor (any time in the next few days)

Re-open the Droplet console and paste:

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

## Step 9 — Download results

1. On your Mac, open Terminal.app and run:

```bash
cd /Users/michaelchang/Documents/claudecode/taiwanese/data
mkdir -p best_response_cloud
# Replace <DROPLET_IP> with the IP shown in the DO dashboard.
# When prompted for password, paste the root password from Step 4.
scp -r root@<DROPLET_IP>:~/tw/data/best_response/ best_response_cloud/
```

## Step 10 — DESTROY the Droplet (critical)

1. Back on DO dashboard → your Droplet → **Destroy** in the left sidebar.
2. **Destroy entire Droplet**. Type the droplet name to confirm.

Row disappears. You are no longer being billed.

---

# What I rejected (and why)

Briefly, so you don't wonder "should I have considered X":

| Provider | Rejected because |
|---|---|
| **AWS (EC2 / Lightsail)** | EC2 is genuinely hostile to first-time users: VPCs, security groups, IAM, key pairs — the click-by-click guide would be 15 pages. Lightsail is simpler but capped at 8 vCPUs, slower than your Mac Mini. |
| **Hetzner Cloud** | Cheapest per core, but the KYC process requires passport + selfie and can be flaky for first-time US customers (reviews report face-match failures and arbitrary account closures). Saves ~$35 vs DO, but DO has a $200 signup credit so Hetzner is *more* expensive out of pocket. Not worth the account-creation anxiety. |
| **Azure** | $200 signup credit is fine but the console is even denser than AWS for a non-technical user. Not worth it vs GCP. |
| **Oracle Cloud** | "Always Free" ARM VMs sound appealing but (a) notoriously capacity-constrained — you often can't actually provision them, and (b) the paid tiers offer no UX advantage over DO. |
| **Fly.io / Railway / Render** | Designed for long-running web services. Fly.io caps at 8 dedicated vCPUs; Render caps at 32 and is priced like an enterprise tool. Wrong fit for a one-time batch job. |
| **Lambda Labs, Vast.ai** | GPU-first; CPU offerings are afterthoughts. RunPod is the exception — it has real CPU pods. |
| **Latitude.sh / Equinix Metal** | Bare-metal hourly is great in principle but signup requires SSH key management (not beginner-friendly) and pricing starts higher than RunPod. |
| **Spot / preemptible pricing** on any provider | The solver has crash-safe resume, so technically spot is safe. But every preemption = another SSH session, another "did it break?" moment for a non-technical user. Savings of ~$20-60 aren't worth the anxiety. Use on-demand. |
| **GCP Committed Use Discounts (CUDs)** | These ARE multi-year commitments — the one GCP pricing feature that doesn't fit "no monthly commitment." Do not click anything labeled "CUD" or "Reservations." |
| **RunPod Savings Plans** | 3- or 6-month prepaid commitments. The On-Demand tier is pure per-second with no commitment — use that. |

---

# Sub-24-hour variant (if you want results faster)

The default guide targets ~1.7-3 days wall-clock. If you want sub-24-hour completion, the workload is embarrassingly parallel across 4 models AND across the 6M hands, so either a **bigger machine** or **multiple machines in parallel** works. A GPU does NOT help — the solver is branchy integer code and lookup-table-memory-bound, exactly the pattern GPUs are worst at. Commercial poker solvers (PioSolver etc.) are CPU-only for the same reason.

## Sub-24-hour approach — GCP bigger VM

**Wall-clock: ~15-19 hours. Cost: $0 out of pocket if the $300 trial credit is still untouched.**

Follow the GCP section exactly, but in Step 5a request quota for `200` CPUs instead of `128`, and in Step 6 pick one of these machine types:

- `c3-highcpu-176` — 176 vCPU Intel Sapphire Rapids, ~$7.50/hr — 15-hour job ≈ $113 → fits under $300 credit.
- `c3d-highcpu-180` — 180 vCPU AMD EPYC, similar price — confirm on pricing calculator.

These are the largest single-VM CPU options on GCP that don't require a partner quota review. Still billed per-second, still covered by the $300 credit, still no monthly commitment.

## If sub-24-hour matters less than simplicity

The default GCP `c2d-highcpu-112` path (~1.7 days, $0 out of pocket) is already 5-6× faster than your Mac Mini and the fastest within the $300 credit. For almost every user this is the sweet spot.

---

# Common gotchas (all options)

1. **"Hourly pricing" is NOT a subscription.** You can run a VM for 4 hours and pay 4 hours. Destroy = meter stops. None of these three options require you to commit to any time period.
2. **Closing the browser tab kills the job — unless you used `nohup`.** The scripts already use it, so you're fine, but if you copy-paste any other long-running command, remember `nohup cmd > log 2>&1 &`.
3. **Data deletion when the VM is destroyed**. ALWAYS download `data/best_response/*.bin` before destroying.
4. **Billing alerts on DO and GCP** (Steps 3 / 5b above) are the cheapest insurance policy you can buy. Set them.
5. **RunPod hits $0 → pod dies → data lost.** Over-provision your prepaid deposit (the guide recommends $140 for a ~$110 job).
6. **Don't click anything labeled "Reserved," "Savings Plan," "Committed Use," or "CUD"** on any provider. Those are the only features that create multi-month commitments. The default is always pure on-demand per-second billing.
7. **The 4 output files are idempotent-by-header.** If you destroy and re-create the VM later, you can continue the job from where it left off if you re-upload the partial `.bin` files to the same path. But the easy path is: let all 4 complete on one machine, then destroy.
8. **Expected total data transfer out**: ~220 MB. Well under the 1 GB/month free tier of any provider. No bandwidth cost to worry about.
9. **Close the account afterward if you want** — on GCP and DO both, closing the billing account prevents any future charges. RunPod is prepaid so the question doesn't arise.

---

# Session-end action from Claude Code

To make this guide usable, Claude Code:
1. Committed the bug fixes + scripts + this guide to the local repo.
2. Pushed to `github.com/mcoski8/tw` on `main`.
3. Verified push succeeded so the cloud `git clone` will work.

You can verify: go to <https://github.com/mcoski8/tw>, check the latest commit message mentions Bug 1 + Bug 3 + Sprint 2b + the cloud guide rewrite.

---

*Last updated: 2026-04-19 (ranked by overspend safety; RunPod #1, GCP #2 with expanded per-usage pricing section, DO #3).*
