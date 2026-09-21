
import threading
from datetime import datetime

from config import HOSTS_FILE_PATH, BLOCK_REDIRECT_IP


FOXFLOW_MARKER_START = "# === FOXFLOW BLOCK START ==="
FOXFLOW_MARKER_END = "# === FOXFLOW BLOCK END ==="


class SiteBlocker:
    
    def __init__(self):
        self._lock = threading.Lock()
        self.is_enabled = False

    def get_blocked_sites(self):
        """Get all blocked sites from DB."""
        try:
            from db.database import SessionLocal
            from db.models import BlockedSite

            db = SessionLocal()
            try:
                sites = db.query(BlockedSite).all()
                return [
                    {"id": s.id, "domain": s.domain, "active": s.active,
                     "created_at": s.created_at.isoformat() if s.created_at else None}
                    for s in sites
                ]
            finally:
                db.close()
        except Exception as e:
            print(f"[Blocker] Error: {e}")
            return []

    def add_site(self, domain):
        """Add a domain to the block list."""
        domain = domain.strip().lower()
        if domain.startswith("http"):
            from urllib.parse import urlparse
            domain = urlparse(domain).netloc
        if domain.startswith("www."):
            domain = domain[4:]

        try:
            from db.database import SessionLocal
            from db.models import BlockedSite

            db = SessionLocal()
            try:
                existing = db.query(BlockedSite).filter_by(domain=domain).first()
                if existing:
                    return {"error": f"{domain} is already in the block list"}

                site = BlockedSite(domain=domain, active=True, created_at=datetime.utcnow())
                db.add(site)
                db.commit()

                if self.is_enabled:
                    self._update_hosts_file()

                return {"success": True, "domain": domain}
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def remove_site(self, domain):
      
        try:
            from db.database import SessionLocal
            from db.models import BlockedSite

            db = SessionLocal()
            try:
                site = db.query(BlockedSite).filter_by(domain=domain).first()
                if not site:
                    return {"error": f"{domain} not found"}
                db.delete(site)
                db.commit()

                if self.is_enabled:
                    self._update_hosts_file()

                return {"success": True}
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def toggle_site(self, domain):
       
        try:
            from db.database import SessionLocal
            from db.models import BlockedSite

            db = SessionLocal()
            try:
                site = db.query(BlockedSite).filter_by(domain=domain).first()
                if not site:
                    return {"error": f"{domain} not found"}
                site.active = not site.active
                db.commit()

                if self.is_enabled:
                    self._update_hosts_file()

                return {"success": True, "active": site.active}
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def enable(self):
      
        with self._lock:
            self.is_enabled = True
            self._update_hosts_file()

    def disable(self):
     
        with self._lock:
            self.is_enabled = False
            self._remove_foxflow_entries()

    def get_status(self):
        return {
            "enabled": self.is_enabled,
            "sites": self.get_blocked_sites(),
        }

    def _update_hosts_file(self):
       
        try:
            from db.database import SessionLocal
            from db.models import BlockedSite

            db = SessionLocal()
            try:
                active_sites = db.query(BlockedSite).filter_by(active=True).all()
                domains = [s.domain for s in active_sites]
            finally:
                db.close()

            self._remove_foxflow_entries()

            if not domains:
                return

            block_lines = [FOXFLOW_MARKER_START]
            for domain in domains:
                block_lines.append(f"{BLOCK_REDIRECT_IP} {domain}")
                block_lines.append(f"{BLOCK_REDIRECT_IP} www.{domain}")
            block_lines.append(FOXFLOW_MARKER_END)

            with open(HOSTS_FILE_PATH, "a") as f:
                f.write("\n" + "\n".join(block_lines) + "\n")

            # Flush DNS cache
            import subprocess
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, shell=True)

        except PermissionError:
            print("[Blocker] ERROR: Need admin privileges to modify hosts file.")
        except Exception as e:
            print(f"[Blocker] Error updating hosts: {e}")

    def _remove_foxflow_entries(self):
        """Remove FoxFlow entries from the hosts file."""
        try:
            with open(HOSTS_FILE_PATH, "r") as f:
                lines = f.readlines()

            new_lines = []
            skip = False
            for line in lines:
                if FOXFLOW_MARKER_START in line:
                    skip = True
                    continue
                if FOXFLOW_MARKER_END in line:
                    skip = False
                    continue
                if not skip:
                    new_lines.append(line)

            with open(HOSTS_FILE_PATH, "w") as f:
                f.writelines(new_lines)

        except PermissionError:
            print("[Blocker] ERROR: Need admin privileges to modify hosts file.")
        except Exception as e:
            print(f"[Blocker] Error cleaning hosts: {e}")



site_blocker = SiteBlocker()
