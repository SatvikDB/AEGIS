# 📤 GitHub Upload Guide

**Upload AEGIS to: https://github.com/SatvikDB/AEGIS**

---

## 🚀 Quick Upload (5 Steps)

### Step 1: Initialize Git Repository

```bash
# Navigate to project directory (if not already there)
cd /Users/satvikdb/Downloads/Claude

# Initialize git
git init

# Add remote repository
git remote add origin https://github.com/SatvikDB/AEGIS.git
```

### Step 2: Add Files

```bash
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status
```

### Step 3: Create First Commit

```bash
# Commit with descriptive message
git commit -m "Initial commit: AEGIS v2.0 - Complete AI Intelligence System

- YOLO11 object detection (80 classes)
- AI Tactical Analyst with Gemini
- GPS Geo-Intelligence with 3D globe
- Custom model training pipeline (71% mAP@50)
- Analytics dashboard with charts
- Multi-model support (COCO/Military/DOTA)
- Complete documentation (1,600+ lines)
- Production-ready code"
```

### Step 4: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

### Step 5: Verify Upload

Open: https://github.com/SatvikDB/AEGIS

---

## 📋 Pre-Upload Checklist

### ✅ Files to Include

- [x] Source code (`.py`, `.js`, `.css`, `.html`)
- [x] Configuration files (`config.py`, `requirements.txt`)
- [x] Documentation (`.md` files)
- [x] Scripts (`scripts/`)
- [x] Templates (`templates/`)
- [x] Static assets (`static/`)
- [x] `.gitignore` file
- [x] `README.md`

### ❌ Files to Exclude (via .gitignore)

- [x] `.env` (contains API keys!)
- [x] `venv/` (virtual environment)
- [x] `__pycache__/` (Python cache)
- [x] `static/uploads/*` (uploaded images)
- [x] `logs/*.csv` (detection logs)
- [x] `models/*.pt` (large model files)
- [x] `datasets/*/images/` (training data)
- [x] `.DS_Store` (macOS files)

---

## 🔐 Security Check

### CRITICAL: Remove Sensitive Data

**Before uploading, verify `.env` is NOT included:**

```bash
# Check if .env will be committed
git status | grep .env

# If .env appears, it's a problem!
# Make sure .gitignore includes .env
```

**Your `.env` contains:**
- Gemini API key
- Should NEVER be uploaded to GitHub

**Already in .gitignore:** ✅

---

## 📝 Detailed Steps

### Option A: Command Line (Recommended)

```bash
# 1. Initialize repository
git init

# 2. Add remote
git remote add origin https://github.com/SatvikDB/AEGIS.git

# 3. Stage all files
git add .

# 4. Check what's staged
git status

# 5. Commit
git commit -m "Initial commit: AEGIS v2.0"

# 6. Set main branch
git branch -M main

# 7. Push
git push -u origin main
```

### Option B: GitHub Desktop

1. Open GitHub Desktop
2. File → Add Local Repository
3. Choose project folder
4. Create repository on GitHub.com
5. Publish repository
6. Push to origin

---

## 🎯 What Gets Uploaded

### ✅ Included Files (~50MB)

**Source Code:**
- `app.py` - Main Flask application
- `config.py` - Configuration
- `services/*.py` - All service modules
- `scripts/*.py` - Training and utility scripts

**Frontend:**
- `templates/*.html` - Web pages
- `static/css/*.css` - Stylesheets
- `static/js/*.js` - JavaScript

**Documentation:**
- `README.md` - Project overview
- `AEGIS_COMPLETE_DOCUMENTATION.md` - Complete docs
- `PRESENTATION_SCRIPT.md` - Presentation guide
- All other `.md` files

**Configuration:**
- `requirements.txt` - Dependencies
- `.gitignore` - Git ignore rules
- `datasets/military/military.yaml` - Training config

**Placeholders:**
- `static/uploads/.gitkeep`
- `logs/.gitkeep`
- `models/README.md`

### ❌ Excluded Files (~2GB+)

**Large Files:**
- Model weights (`.pt` files) - 5-50MB each
- Training datasets - 1-2GB
- Uploaded images - varies
- Training outputs - 100MB+

**Sensitive:**
- `.env` file with API keys
- Personal data

**Temporary:**
- Python cache
- Virtual environment
- Log files
- Backup files

---

## 🔄 After Upload

### Update README on GitHub

1. Go to https://github.com/SatvikDB/AEGIS
2. Edit `README.md` if needed
3. Add badges (optional):
   ```markdown
   ![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
   ![YOLO](https://img.shields.io/badge/YOLO-11-green.svg)
   ![License](https://img.shields.io/badge/license-MIT-blue.svg)
   ```

### Add Topics/Tags

Add these topics to your repository:
- `artificial-intelligence`
- `computer-vision`
- `object-detection`
- `yolo`
- `machine-learning`
- `military-intelligence`
- `flask`
- `python`
- `deep-learning`
- `geospatial-analysis`

### Create Releases

1. Go to Releases
2. Create new release
3. Tag: `v2.0`
4. Title: "AEGIS v2.0 - Complete AI Intelligence System"
5. Description: Copy from README

---

## 📊 Repository Structure

After upload, your repo will look like:

```
AEGIS/
├── .gitignore
├── README.md
├── AEGIS_COMPLETE_DOCUMENTATION.md
├── PRESENTATION_SCRIPT.md
├── QUICK_COMMANDS.md
├── app.py
├── config.py
├── requirements.txt
│
├── services/
│   ├── detection.py
│   ├── alert.py
│   ├── logger.py
│   ├── analyst.py
│   ├── llm_client.py
│   ├── geo_service.py
│   └── analytics.py
│
├── scripts/
│   ├── train_dota_model.py
│   ├── evaluate_dota_model.py
│   └── ...
│
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   └── globe.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/.gitkeep
│
├── logs/.gitkeep
├── models/README.md
└── datasets/military/military.yaml
```

---

## 🐛 Troubleshooting

### Problem: "Repository already exists"

```bash
# Remove existing remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/SatvikDB/AEGIS.git
```

### Problem: "Permission denied"

```bash
# Check if you're logged in
git config --global user.name "SatvikDB"
git config --global user.email "your-email@example.com"

# Use personal access token instead of password
# Generate at: https://github.com/settings/tokens
```

### Problem: "File too large"

```bash
# Check file sizes
find . -type f -size +50M

# Add large files to .gitignore
echo "path/to/large/file" >> .gitignore

# Remove from staging
git rm --cached path/to/large/file
```

### Problem: ".env file was committed"

```bash
# Remove from git history
git rm --cached .env

# Add to .gitignore
echo ".env" >> .gitignore

# Commit
git commit -m "Remove .env from tracking"

# Force push (if already pushed)
git push -f origin main
```

---

## 📝 Commit Message Template

```bash
git commit -m "Title: Brief description

- Feature 1
- Feature 2
- Bug fix
- Documentation update"
```

**Good Examples:**

```bash
git commit -m "Add DOTA aerial detection support

- Implement DOTA model training pipeline
- Add model switching functionality
- Create training scripts
- Update documentation"
```

```bash
git commit -m "Fix GPS panel rendering issue

- Add browser cache-busting
- Update geo.js with debug logs
- Improve error handling"
```

---

## 🎯 Post-Upload Tasks

### 1. Add Repository Description

On GitHub, add description:
> "AEGIS - AI-powered military intelligence system with YOLO11 object detection, Gemini AI analysis, and GPS geo-intelligence. Complete production-ready platform."

### 2. Add Website (Optional)

If you deploy it, add the URL

### 3. Enable GitHub Pages (Optional)

For documentation hosting

### 4. Add License

Choose a license (MIT, Apache, etc.)

### 5. Create Issues/Projects

For future development tracking

---

## ✅ Verification Checklist

After upload, verify:

- [ ] Repository is public/private as intended
- [ ] README displays correctly
- [ ] All source files are present
- [ ] .env is NOT visible
- [ ] Documentation is readable
- [ ] File structure is correct
- [ ] .gitignore is working
- [ ] No sensitive data exposed

---

## 🎉 Success!

Your AEGIS project is now on GitHub!

**Repository URL:** https://github.com/SatvikDB/AEGIS

**Share it:**
- Add to your resume/portfolio
- Share on LinkedIn
- Include in project presentations
- Use for job applications

---

## 📚 Additional Git Commands

### Update Repository

```bash
# After making changes
git add .
git commit -m "Update: description of changes"
git push
```

### Create Branch

```bash
# For new features
git checkout -b feature/video-detection
git push -u origin feature/video-detection
```

### View History

```bash
git log --oneline
git log --graph --all
```

### Undo Changes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- filename
```

---

**Ready to upload!** 🚀

Run the commands in Step 1-4 and your project will be on GitHub!
