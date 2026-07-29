# GitHub Issues & CI/CD Deployment Workflow Guide

This document outlines the standard process for creating GitHub issues, using the Antigravity CLI (`agy`) to resolve them in isolated branches, and running automated tests before merging and deploying to Firebase Hosting.

---

## Part 1: GitHub Secrets Setup (One-time Setup)
To allow GitHub Actions to deploy to Firebase Hosting on your behalf, you need to add your Firebase Service Account key as a GitHub Repository Secret:

1. **Generate the Service Account Key:**
   - Run this command in your local project terminal:
     ```bash
     npx firebase login:ci
     ```
     *(Or, generate a service account JSON file from the [Google Cloud Console for your project](https://console.cloud.google.com/iam-admin/serviceaccounts) under **Firebase Hosting** and download it).*
   - Alternatively, run `npx firebase init hosting:github` which will automatically create the service account and upload it to GitHub for you!

2. **Add to GitHub Secrets:**
   - Go to your GitHub repository: `https://github.com/grahamsw/starsandstripes`.
   - Click **Settings** -> **Secrets and variables** -> **Actions**.
   - Click **New repository secret**.
   - **Name:** `FIREBASE_SERVICE_ACCOUNT_STARS_AND_STRIPES_FLAG_2026`
   - **Value:** Paste the entire contents of your service account JSON file.

---

## Part 2: The Issue-to-Deploy Lifecycle

### Step 1: Create a GitHub Issue
Create an issue on GitHub to document what needs to be changed (e.g. *"Issue #14: Add manual cycle button to WebGL canvas sidebar"*).

### Step 2: Checkout a Clean branch and tell `agy` to tackle it
On your laptop, checkout a new branch corresponding to the issue and launch the `agy` CLI to solve it:

```bash
# 1. Fetch remote changes and checkout a clean branch
git checkout main
git pull origin main
git checkout -b fix/issue-14

# 2. Run agy with a direct prompt to resolve the issue
agy -p "Tackle issue #14: Add a manual cycle button to the WebGL flag emulator sidebar so users can manually advance to the next theme."
```
*Note: The `agy` agent will read the workspace, make the necessary file changes, compile, and save the files on your branch.*

### Step 3: Local Verification & Tests
Always verify the changes compile and run correctly locally before pushing:

```bash
# Verify the Vite/Vue build compiles without syntax or bundler errors
npm run build

# If all is well, stage and commit the changes
git add .
git commit -m "Fix issue #14: Add manual cycle button to sidebar"
```

### Step 4: Push Branch & Create a Pull Request
Push your branch to GitHub and create a Pull Request to merge into `main`:

```bash
# Push branch to remote
git push origin fix/issue-14

# Create a Pull Request (using GitHub CLI or the GitHub Web UI)
gh pr create --title "Fix issue #14: Add manual cycle button" --body "Resolves #14"
```

### Step 5: PR Build Gate (Automated Tests)
Once the Pull Request is opened:
- The **PR Build & Compiler Gate** workflow (`.github/workflows/pr-checks.yml`) will automatically trigger.
- It spins up a clean container, installs your Node.js dependencies, and runs `npm run build`.
- If the build succeeds, a green checkmark will appear on the PR. If it fails, the merge button is blocked to protect the `main` branch.

### Step 6: Merge & Automatic Deploy
- Once you approve and merge the Pull Request:
  - The **Deploy to Firebase Hosting on Merge** workflow (`.github/workflows/deploy.yml`) is triggered on the `main` branch.
  - It compiles the final production assets and deploys them live to [https://stars-and-stripes-flag-2026.web.app](https://stars-and-stripes-flag-2026.web.app) in under a minute!
