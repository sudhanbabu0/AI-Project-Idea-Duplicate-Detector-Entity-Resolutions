# AI Project Idea Duplicate Detector & Entity Resolution System (SRM-AIDRS)

**SRM Institute of Science and Technology**  
*Department of Artificial Intelligence & Computer Science (3rd Year) • Academic Year 2026–2027*  

### **Project Guide:** Dr. S.P. Ramya  
### **Project Team Members:**
1. **Sudhan Babu** — `RA2411047050032` (Lead)
2. **Keerthi Vasaa** — `RA2411047050041`
3. **Dayanandan** — `RA2411047050029`

---

## 🌟 Executive Summary

Every semester, hundreds of students submit project proposals independently (e.g., *"Smart Attendance System using Face Recognition"* vs. *"AI Based Face Recognition Attendance System"*). Traditional relational database keyword queries (`WHERE title LIKE '%attendance%'`) fail because students use different phrasing, synonyms, or structural formatting. 

**SRM-AIDRS** is an intelligent DBMS extension combining a **relational SQL database** with **dense AI vector embeddings** to automatically track, compare, and flag duplicate project proposals in real-time, providing faculty coordinators with automated entity resolution and student team collaboration tools.

---

## 🏗️ System Architecture & Workflow (Slide 7)

```
[ INPUT ]                   [ AI PROCESS ]                   [ SQL DATABASE ]                  [ OUTPUT / RESOLUTION ]
Student Submits       ───>  Dense Vector Generation   ───>  Vector Table Indexing        ───>  Duplicate Alert (>80%)
Title, Domain &             (512-D Embeddings) &            (Cosine Distance Query)            Side-by-Side Review &
Abstract                    Entity Extraction                                                  Team Merge Actions
```

---

## 📦 System Modules (Slide 8)

### 🔹 Module 1: User Authentication & Submission Portal
- Allows students to log in, submit project proposals (Title, Domain, Abstract, Methodology, Tech Stack, Team details), and track review status.
- **Live Real-Time Duplicate Pre-Check**: Calculates similarity against the database as the student types, displaying an instant similarity gauge meter (0–100%) and warning if a similar idea already exists before final submission.

### 🔹 Module 2: AI Embedding & Processing Engine
- Extracts technical features, domain keywords, acronyms, and character/word n-grams.
- Generates 512-dimensional $L_2$-normalized vector representations capturing semantic meaning beyond simple keyword matching.
- Highlights overlapping phrases and technical entities across proposals.

### 🔹 Module 3: DBMS Vector Index & Similarity Matcher
- Pure SQL relational database storing projects, users, similarity matrices, and vector embeddings in the `project_vectors` table.
- Executes cosine distance queries:
  $$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
- Classifies similarity into risk levels:
  - **$\ge 80\%$ (High Duplicate Alert)**: Critical overlap; flagged for coordinator review.
  - **$50\% - 79\%$ (Moderate Overlap)**: Conceptual overlap; student team collaboration recommended.
  - **$< 50\%$ (Original Proposal)**: Verified original project idea.

### 🔹 Module 4: Admin Resolution Dashboard
- Displays executive metrics (Total Submissions, Duplicate Flags, Merged Teams, Original Rate).
- **Side-by-Side Diff Inspector**: Highlights common text phrases in yellow and displays identical technical entities.
- **Academic Resolution Actions**:
  - **Merge Teams**: Merges both student groups into a single joint capstone team under Dr. S.P. Ramya.
  - **Approve Both**: Approves both if sufficient technical divergence exists.
  - **Reject Duplicate**: Rejects proposal with feedback.
  - **Request Revision**: Instructs student to alter methodology or scope.

---

## 🗄️ Relational SQL Database Schema

The database (`projects.db`) is structured with relational tables:

1. **`users`**: `id`, `username`, `password_hash`, `name`, `role` ('student'/'faculty'), `reg_no`, `department`.
2. **`projects`**: `id`, `student_id`, `title`, `domain`, `abstract`, `methodology`, `tech_stack`, `team_members`, `submitted_by_name`, `reg_no`, `status`, `max_similarity_score`, `matched_project_id`.
3. **`project_vectors`**: `id`, `project_id` (FK), `vector_json` (512-D float array), `dimension`, `entity_tags_json`, `updated_at`.
4. **`similarity_matches`**: `id`, `source_project_id` (FK), `target_project_id` (FK), `similarity_score`, `title_similarity`, `abstract_similarity`, `entity_similarity`, `common_entities`, `risk_level`.
5. **`entity_resolutions`**: `id`, `project_a_id`, `project_b_id`, `action`, `faculty_name`, `resolution_notes`, `merged_team_name`, `resolved_at`.

---

## 🚀 How to Run the Website

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Seed Academic Repository Data
```powershell
python seed_data.py
```

### Step 3: Launch Server (Broadcasting on 0.0.0.0)
```powershell
python run.py
```

The terminal will display:
```
[+] SERVER READY AND BROADCASTING ON NETWORK INTERFACES:
    - On this Laptop (Localhost):     http://localhost:5000
    - On College Wi-Fi / Mobile LAN:  http://10.172.241.68:5000
    - Network Hosting:                BIND 0.0.0.0:5000 (Public LAN Enabled)
```

---

## 🌐 Running Beyond Localhost (Multi-Device & Cloud Access)

1. **Local Area Network (Wi-Fi) Access**:
   - The application binds to `0.0.0.0:5000`.
   - Any smartphone or laptop connected to the same college Wi-Fi or mobile hotspot can open:
     `http://<YOUR_IP>:5000` (e.g. `http://10.172.241.68:5000`).
   - Open `/network` in the portal to view the **scannable QR code** for your evaluators!

2. **1-Click Free Cloud Deployment (Render / Railway)**:
   - Configured with `Procfile` and `render.yaml`.
   - Push to GitHub and deploy on [Render.com](https://render.com) for a free 24/7 public URL (`https://srm-duplicate-detector.onrender.com`).

3. **Instant Zero-Config Cloudflare Tunnel**:
   - Run: `cloudflared tunnel --url http://localhost:5000`
   - Gives an instant public HTTPS address accessible from anywhere.

---

## 🔑 Demo Login Accounts

| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| **Faculty Guide** | `ramya.guide` | `password123` | Dr. S.P. Ramya (Review Dashboard & Entity Resolution) |
| **Lead Student** | `sudhan` | `password123` | Sudhan Babu (RA2411047050032 - Submission & Tracking) |
| **Student** | `keerthi` | `password123` | Keerthi Vasaa (RA2411047050041) |
| **Student** | `dayanandan` | `password123` | Dayanandan (RA2411047050029) |
