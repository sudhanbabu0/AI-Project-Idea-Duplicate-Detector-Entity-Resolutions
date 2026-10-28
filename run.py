"""
Server Launcher for SRMIST AI Project Duplicate Detector & Entity Resolution System.
Binds to 0.0.0.0 for LAN/Wi-Fi multi-device access and generates QR code.
"""
import os
import sys
import socket
import qrcode
import qrcode.image.svg
from database import init_db, get_dashboard_statistics
from seed_data import seed_database
from app import app, get_host_ip

def setup_server():
    print("\n" + "=" * 70)
    print("   SRM INSTITUTE OF SCIENCE AND TECHNOLOGY - DEPARTMENT OF AI")
    print("   AI Project Idea Duplicate Detector & Entity Resolution System")
    print("=" * 70)

    # 1. Initialize DB and seed if empty
    init_db()
    stats = get_dashboard_statistics()
    if stats['total_projects'] == 0:
        print("[*] No existing proposals detected. Seeding baseline academic data...")
        seed_database()
    else:
        print(f"[+] SQL Database verified: {stats['total_projects']} projects, {stats['flagged_projects']} duplicate flags.")

    # 2. Network IP & QR Code Generation
    lan_ip = get_host_ip()
    port = int(os.environ.get('PORT', 5000))
    lan_url = f"http://{lan_ip}:{port}"
    local_url = f"http://localhost:{port}"

    os.makedirs(os.path.join('static', 'img'), exist_ok=True)
    qr_path = os.path.join('static', 'img', 'qr_lan.svg')
    try:
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(lan_url, image_factory=factory)
        img.save(qr_path)
        print(f"[+] Generated Network QR Code SVG at: {qr_path}")
    except Exception as e:
        print(f"[!] Note: QR code generation skipped: {e}")

    # 3. Print access banner
    print("\n[+] SERVER READY AND BROADCASTING ON NETWORK INTERFACES:")
    print("    - LIVE PUBLIC INTERNET WEBSITE:    https://supplemental-combinations-hollow-competing.trycloudflare.com")
    print(f"    - On College Wi-Fi / Mobile LAN:   {lan_url}")
    print(f"    - Local Machine Fallback:          {local_url}")
    print(f"    - Network Hosting:                 BIND 0.0.0.0:{port} (Worldwide Access Enabled)")
    print("\n[+] ACADEMIC EVALUATION CREDENTIALS:")
    print("    - Faculty Guide (Dr. S.P. Ramya):  username: ramya.guide   | password: password123")
    print("    - Lead Student (Sudhan Babu):      username: sudhan        | password: password123")
    print("    - Team Members: Keerthi Vasaa (RA2411047050041), Dayanandan (RA2411047050029)")
    print("=" * 70 + "\n")

    return port

if __name__ == '__main__':
    port = setup_server()
    app.run(host='0.0.0.0', port=port, debug=False)
