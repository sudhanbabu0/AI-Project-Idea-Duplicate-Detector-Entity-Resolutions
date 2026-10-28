"""
Seed Data Script for SRMIST AI Project Duplicate Detector & Entity Resolution System.
Populates realistic student projects, faculty accounts, vector embeddings, and similarity matrices.
"""
import os
import json
import sqlite3
from database import (
    DB_PATH, init_db, create_user, add_project, store_project_vector,
    update_project_status, record_similarity_match, record_resolution,
    get_all_projects
)
from nlp_engine import engine, extract_entities

def seed_database():
    print("[*] Reinitializing SQL Database...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("[+] Removed previous database to ensure clean seed.")
        except Exception as e:
            print(f"[!] Note: Could not remove DB file ({e}), continuing with table initialization...")

    init_db()

    print("[*] Creating Users (Faculty & Students)...")
    # Faculty Coordinator / Guide (Dr. S.P. Ramya)
    faculty_id = create_user(
        username='ramya.guide',
        password='password123',
        name='Dr. S.P. Ramya',
        role='faculty',
        reg_no='FAC-AI-2024',
        department='Artificial Intelligence'
    )

    # Lead Student Team (Sudhan Babu, Keerthi Vasaa, Dayanandan)
    sudhan_id = create_user(
        username='sudhan',
        password='password123',
        name='Sudhan Babu',
        role='student',
        reg_no='RA2411047050032',
        department='Artificial Intelligence'
    )
    keerthi_id = create_user(
        username='keerthi',
        password='password123',
        name='Keerthi Vasaa',
        role='student',
        reg_no='RA2411047050041',
        department='Artificial Intelligence'
    )
    daya_id = create_user(
        username='dayanandan',
        password='password123',
        name='Dayanandan',
        role='student',
        reg_no='RA2411047050029',
        department='Artificial Intelligence'
    )

    # Other SRMIST Students
    rahul_id = create_user(
        username='rahul.k',
        password='password123',
        name='Rahul Kumar',
        role='student',
        reg_no='RA2411047050055',
        department='Artificial Intelligence'
    )
    priya_id = create_user(
        username='priya.s',
        password='password123',
        name='Priya Sharma',
        role='student',
        reg_no='RA2411047050012',
        department='Computer Science'
    )
    vikram_id = create_user(
        username='vikram.r',
        password='password123',
        name='Vikram Raman',
        role='student',
        reg_no='RA2411047050088',
        department='Computer Science'
    )
    ananya_id = create_user(
        username='ananya.m',
        password='password123',
        name='Ananya Mukherjee',
        role='student',
        reg_no='RA2411047050064',
        department='Information Technology'
    )

    # Project definitions
    projects_data = [
        {
            'student_id': sudhan_id,
            'title': 'Smart Attendance System using Face Recognition and Deep Learning',
            'domain': 'Artificial Intelligence',
            'abstract': 'An automated student attendance monitoring system that uses OpenCV and deep learning to identify student faces from classroom CCTV camera feeds and records attendance in real-time into the college database.',
            'methodology': 'Haar Cascade face detection, FaceNet CNN feature embeddings, Cosine distance matching, SQLite attendance logging backend, and web dashboard.',
            'tech_stack': 'Python, OpenCV, PyTorch, FaceNet, SQLite, Flask',
            'team_members': 'Sudhan Babu (RA2411047050032), Keerthi Vasaa (RA2411047050041), Dayanandan (RA2411047050029)',
            'submitted_by_name': 'Sudhan Babu',
            'reg_no': 'RA2411047050032'
        },
        {
            'student_id': rahul_id,
            'title': 'AI Based Face Recognition Attendance System for Classroom Monitoring',
            'domain': 'Artificial Intelligence',
            'abstract': 'Classroom attendance tracking application using computer vision and deep learning to recognize student faces automatically from webcams and update academic logs in database with duplicate prevention.',
            'methodology': 'MTCNN face detection, ResNet embeddings, Cosine distance similarity, MySQL relational database, Flask web interface.',
            'tech_stack': 'Python, OpenCV, TensorFlow, ResNet, MySQL, Flask',
            'team_members': 'Rahul Kumar (RA2411047050055), Sneha Reddy (RA2411047050071)',
            'submitted_by_name': 'Rahul Kumar',
            'reg_no': 'RA2411047050055'
        },
        {
            'student_id': priya_id,
            'title': 'Early Detection of Melanoma Skin Cancer using Convolutional Neural Networks',
            'domain': 'Artificial Intelligence',
            'abstract': 'An automated computer-aided diagnostic tool designed to classify dermoscopic skin lesion images into benign or malignant melanoma using custom CNNs and transfer learning.',
            'methodology': 'Image preprocessing, hair artifact removal, EfficientNet-B4 fine-tuning on ISIC dataset, Grad-CAM visual heatmaps for clinical interpretability.',
            'tech_stack': 'Python, PyTorch, EfficientNet, OpenCV, Scikit-learn, FastAPI',
            'team_members': 'Priya Sharma (RA2411047050012), Rohan Verma (RA2411047050019)',
            'submitted_by_name': 'Priya Sharma',
            'reg_no': 'RA2411047050012'
        },
        {
            'student_id': vikram_id,
            'title': 'Deep Learning Framework for Skin Lesion and Melanoma Classification',
            'domain': 'Artificial Intelligence',
            'abstract': 'Automated classification of skin lesions and melanoma detection from clinical dermoscopy photographs utilizing deep convolutional neural networks with high diagnostic sensitivity.',
            'methodology': 'Data augmentation, transfer learning using ResNet-50 and EfficientNet on ISIC dermoscopic database, Grad-CAM visualization, Streamlit UI.',
            'tech_stack': 'Python, TensorFlow, Keras, ResNet-50, Streamlit, Pandas',
            'team_members': 'Vikram Raman (RA2411047050088), Karthik S (RA2411047050090)',
            'submitted_by_name': 'Vikram Raman',
            'reg_no': 'RA2411047050088'
        },
        {
            'student_id': ananya_id,
            'title': 'Decentralized Land Registry and Title Transfer using Ethereum Smart Contracts',
            'domain': 'Blockchain',
            'abstract': 'A tamper-proof real estate title management system built on Ethereum blockchain to eliminate fraudulent property disputes and automate escrow transfers through smart contracts.',
            'methodology': 'Solidity smart contracts adhering to ERC-721 token standards for unique property parcel NFTs, IPFS for deed document storage, Web3.js client.',
            'tech_stack': 'Solidity, Ethereum, IPFS, Web3.js, React, Node.js',
            'team_members': 'Ananya Mukherjee (RA2411047050064), Aditya Iyer (RA2411047050069)',
            'submitted_by_name': 'Ananya Mukherjee',
            'reg_no': 'RA2411047050064'
        },
        {
            'student_id': sudhan_id,
            'title': 'IoT-Driven Precision Agriculture and Automated Soil Moisture Irrigation',
            'domain': 'IoT & Embedded Systems',
            'abstract': 'An automated smart irrigation framework using ESP32 microcontrollers and soil moisture sensors with solar powering and cloud telemetry to conserve water in dryland farms.',
            'methodology': 'ESP32 Wi-Fi telemetry via MQTT protocol, capacitive soil sensors, threshold-based solenoid valve control, mobile dashboard.',
            'tech_stack': 'C++, ESP32, MQTT, Node-RED, InfluxDB, Grafana',
            'team_members': 'Sudhan Babu (RA2411047050032), Harish N (RA2411047050039)',
            'submitted_by_name': 'Sudhan Babu',
            'reg_no': 'RA2411047050032'
        },
        {
            'student_id': rahul_id,
            'title': 'Cloud Intrusion Detection System using Ensemble Tree Classifiers',
            'domain': 'Cybersecurity',
            'abstract': 'An active network security intrusion detection system monitoring AWS VPC flow logs to classify malicious DDoS, port scan, and brute-force attacks.',
            'methodology': 'Feature engineering on NSL-KDD dataset, XGBoost and Random Forest ensemble models, real-time alert dispatch to Slack.',
            'tech_stack': 'Python, Scikit-learn, XGBoost, Pandas, AWS Lambda, Docker',
            'team_members': 'Rahul Kumar (RA2411047050055), Varun B (RA2411047050058)',
            'submitted_by_name': 'Rahul Kumar',
            'reg_no': 'RA2411047050055'
        },
        {
            'student_id': priya_id,
            'title': 'Autonomous Drone Visual Navigation in GPS-Denied Indoor Environments',
            'domain': 'Robotics & AI',
            'abstract': 'Visual inertial odometry navigation algorithm for micro aerial vehicles operating inside tunnels and GPS-denied buildings without external satellite signals.',
            'methodology': 'Stereo camera feature tracking, ORB-SLAM3 visual odometry, Extended Kalman Filter sensor fusion, ROS2 navigation stack.',
            'tech_stack': 'C++, Python, ROS2, OpenCV, Gazebo, PX4 Autopilot',
            'team_members': 'Priya Sharma (RA2411047050012), Deepa T (RA2411047050015)',
            'submitted_by_name': 'Priya Sharma',
            'reg_no': 'RA2411047050012'
        }
    ]

    print("[*] Training baseline corpus for Semantic Vector Engine...")
    engine.fit_baseline_corpus(projects_data)

    print("[*] Inserting Projects and Computing Mathematical Vector Embeddings...")
    created_projects = []
    for p in projects_data:
        pid = add_project(
            student_id=p['student_id'],
            title=p['title'],
            domain=p['domain'],
            abstract=p['abstract'],
            methodology=p['methodology'],
            tech_stack=p['tech_stack'],
            team_members=p['team_members'],
            submitted_by_name=p['submitted_by_name'],
            reg_no=p['reg_no']
        )
        vector = engine.generate_embedding(
            title=p['title'],
            domain=p['domain'],
            abstract=p['abstract'],
            methodology=p['methodology'],
            tech_stack=p['tech_stack']
        )
        entities = extract_entities(p['abstract'] + ' ' + p['title'], p['tech_stack'])
        store_project_vector(pid, vector, entities)
        
        p['id'] = pid
        created_projects.append(p)

    print("[*] Computing Cross-Project Pairwise Semantic Similarity & Flagging Duplicates...")
    for i in range(len(created_projects)):
        p1 = created_projects[i]
        max_score = 0.0
        best_match_id = None

        for j in range(len(created_projects)):
            if i == j:
                continue
            p2 = created_projects[j]
            comp = engine.compare_proposals(p1, p2)
            score = comp['similarity_percentage']

            if score > max_score:
                max_score = score
                best_match_id = p2['id']

            # Record similarity match in SQL table
            if i < j and score >= 20.0:
                record_similarity_match(
                    source_id=p1['id'],
                    target_id=p2['id'],
                    score=score,
                    title_sim=comp['title_similarity'],
                    abs_sim=comp['abstract_similarity'],
                    entity_sim=comp['entity_similarity'],
                    common_entities=comp['common_entities'],
                    risk_level=comp['risk_level']
                )

        if max_score >= 80.0:
            status = 'DUPLICATE_FLAGGED'
        elif max_score >= 50.0:
            status = 'PENDING'
        else:
            status = 'APPROVED'

        update_project_status(p1['id'], status, max_score=max_score, matched_id=best_match_id)

    # Record sample Faculty Entity Resolution to show resolution history in review
    print("[*] Recording sample Entity Resolution (Skin Lesion Projects merged into collaborative team)...")
    record_resolution(
        project_a_id=created_projects[3]['id'], # Skin lesion proposal 2
        project_b_id=created_projects[2]['id'], # Skin lesion proposal 1
        action='MERGED_COLLABORATION',
        faculty_id=faculty_id,
        faculty_name='Dr. S.P. Ramya',
        notes='High conceptual overlap (85.2% semantic match) detected on melanoma classification. Both student groups have agreed to merge into a single joint capstone team under Dr. S.P. Ramya with split responsibilities (EfficientNet frontend + Grad-CAM clinical validation).',
        merged_name='Joint ISIC Melanoma Diagnostic Group'
    )

    print("[+] Database seeding complete! All tables and vector indices populated successfully.")

if __name__ == '__main__':
    seed_database()
