"""
GST Inward HSN/SAC Fetcher — desktop app entry point
Developed by Sunayana

Run: python main.py
Build to .exe (on Windows): pyinstaller build.spec
"""
import os
import sys
import webview

import backend


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class Api:
    def __init__(self):
        self.window = None

    def upload_json(self, gstin):
        """Bulk-capable: user can select one or many JSON files at once.
        Period is taken from each file's name where possible; falls back to
        invoice-date derivation (with a note) when the filename doesn't match
        the portal's naming pattern."""
        result = window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=("JSON files (*.json)", "All files (*.*)"),
        )
        if not result:
            return {"cancelled": True}

        files_summary = []
        total_ingested, total_failed = 0, 0
        for path in result:
            fname_gstin, fname_period = backend.parse_filename(path)
            used_gstin = gstin or fname_gstin
            try:
                s = backend.ingest_json_file(path, gstin_tag=used_gstin, period_override=fname_period)
                files_summary.append({
                    "filename": os.path.basename(path),
                    "detected_period": fname_period,
                    "period_source": "filename" if fname_period else "invoice date (filename pattern not recognized)",
                    "ingested": s["ingested"],
                    "failed": s["failed"],
                    "periods": s["periods"],
                })
                total_ingested += s["ingested"]
                total_failed += s["failed"]
            except Exception as e:
                files_summary.append({"filename": os.path.basename(path), "error": str(e)})

        return {
            "files": files_summary,
            "total_ingested": total_ingested,
            "total_failed": total_failed,
        }

    def get_periods(self, gstin):
        try:
            return backend.get_available_periods(gstin or None)
        except Exception:
            return []

    def generate_range(self, period_from, period_to, gstin):
        try:
            return backend.generate_report(period_from, period_to, gstin or None)
        except Exception as e:
            return {"error": str(e)}

    def generate_selected(self, periods, gstin):
        try:
            if not periods:
                return {"error": "Select at least one month."}
            return backend.generate_report_for_periods(periods, gstin or None)
        except Exception as e:
            return {"error": str(e)}

    def list_exports(self):
        try:
            return backend.list_exports()
        except Exception:
            return []

    def list_gstins(self):
        try:
            return backend.list_gstins()
        except Exception:
            return []

    def add_gstin(self, gstin, entity_name):
        try:
            return backend.add_gstin(gstin, entity_name)
        except Exception as e:
            return {"error": str(e)}

    def remove_gstin(self, gstin):
        backend.remove_gstin(gstin)
        return {"ok": True}

    def clear_all_data(self):
        try:
            backend.clear_all_data()
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def get_save_folder(self):
        return backend.get_save_folder()

    def browse_folder(self):
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            folder = result[0]
            backend.set_setting("save_folder", folder)
            return folder
        return None


if __name__ == "__main__":
    import threading

    backend.init_db()
    api = Api()
    window = webview.create_window(
        "GST Inward HSN/SAC Fetcher",
        resource_path("ui.html"),
        js_api=api,
        width=1200,
        height=900,
        resizable=True,
        background_color="#f8f9fa",
    )
    api.window = window
    webview.start(debug=False)
