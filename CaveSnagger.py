import sys
import os
import requests
from bs4 import BeautifulSoup

# --- PYSIDE6 IMPORTS ---
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextEdit, QSlider, QFileDialog, QLineEdit)
from PySide6.QtCore import Qt, QThread, Signal, QRectF
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen

# --- BRANDING: CAVEMAN AI (SafeCoffee Palette) ---
COLORS = {
    "bg_main": "#121826",
    "bg_console": "#0D1117",
    "accent_purple": "#8A2BE2",
    "accent_teal": "#008080",
    "text_main": "#E0E0E0"
}

STYLE_SHEET = f"""
    QMainWindow {{ background-color: {COLORS['bg_main']}; }}
    QLabel {{ color: {COLORS['text_main']}; font-family: 'Segoe UI'; }}
    QLineEdit {{ 
        background-color: {COLORS['bg_console']}; color: white; 
        border: 1px solid {COLORS['accent_teal']}; border-radius: 3px; padding: 5px;
    }}
    QTextEdit {{ 
        background-color: {COLORS['bg_console']}; color: {COLORS['accent_teal']}; 
        border: 1px solid {COLORS['accent_purple']}; border-radius: 5px; 
        font-family: 'Consolas', monospace; font-size: 10px;
    }}
    QPushButton {{
        background-color: {COLORS['accent_purple']}; color: white; 
        border-radius: 5px; padding: 10px; font-weight: bold;
    }}
    QPushButton:disabled {{ background-color: #444; color: #888; }}
"""

class AcquisitionRing(QWidget):
    """Custom OrbWeaver Silk Ring (Pure PySide6)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.value = 0
        self.total = 1

    def update_progress(self, current, total):
        self.value = current
        self.total = total if total > 0 else 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(15, 15, self.width()-30, self.height()-30)
        
        # Void Ring
        painter.setPen(QPen(QColor(COLORS['bg_console']), 18))
        painter.drawEllipse(rect)

        # Silk Arc
        angle = (self.value / self.total) * 360
        pen = QPen(QColor(COLORS['accent_teal']), 18)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, -angle * 16)

        # Stats
        painter.setPen(QColor(COLORS['text_main']))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{self.value} / {self.total}\nSNAGGED")

class SnagWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal()

    def __init__(self, topic, target_dir, limit):
        super().__init__()
        self.topic = topic
        self.target_dir = target_dir
        self.limit = limit
        self.base_url = "https://export.arxiv.org/api/query"

    def run(self):
        try:
            if not os.path.exists(self.target_dir):
                os.makedirs(self.target_dir)

            self.log.emit(f">> Scouring Silk for: {self.topic}...")
            params = {'search_query': f'all:{self.topic}', 'max_results': self.limit}
            
            response = requests.get(self.base_url, params=params, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser') 
            
            entries = soup.find_all('entry')
            if not entries:
                self.log.emit("<font color='orange'>[!] No research found.</font>")
                return

            for i, entry in enumerate(entries):
                pdf_link = entry.find('link', title='pdf')
                if not pdf_link: continue
                
                url = pdf_link['href']
                clean_title = "".join([c for c in entry.find('title').text.strip() if c.isalnum() or c==' '])[:40]
                filename = clean_title.replace(" ", "_") + ".pdf"
                save_path = os.path.join(self.target_dir, filename)

                self.log.emit(f"<font color='#008080'>> Capturing: {filename}</font>")
                
                with requests.get(url, stream=True) as r:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                self.progress.emit(i + 1)
            
            self.log.emit(f"<font color='#8A2BE2'>[SUCCESS] Document stack secured.</font>")
        except Exception as e:
            self.log.emit(f"<font color='red'>[ERROR] {str(e)}</font>")
        finally:
            self.finished.emit()

class CaveSnagger(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CavemanAI | CaveSnagger")
        self.setFixedSize(480, 870)
        self.setStyleSheet(STYLE_SHEET)
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.target_dir = os.path.join(self.script_dir, "Acquisitions")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # --- HEADER SECTION (90x90 Logo) ---
        header_row = QHBoxLayout()
        logo = QLabel()
        pix = QPixmap(os.path.join(self.script_dir, "Snagger.jpeg"))
        if not pix.isNull():
            logo.setPixmap(pix.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        title = QLabel("CaveSnagger")
        title.setFont(QFont("Impact", 36))
        title.setStyleSheet(f"color: {COLORS['accent_purple']};")
        
        header_row.addWidget(logo)
        header_row.addWidget(title)
        header_row.addStretch()
        main_layout.addLayout(header_row)
        main_layout.addSpacing(15)

        # --- ORB WEAVER SUBTITLE (Updated to 9pt Font Size) ---
        sub = QLabel("ORB WEAVER ACQUISITION UNIT")
        sub.setStyleSheet(f"color: {COLORS['accent_teal']}; font-size: 9pt; letter-spacing: 2px;")
        main_layout.addWidget(sub)

        # Topic Search
        main_layout.addWidget(QLabel("TOPIC OF INTEREST:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. Theoretical Physics, Machine Learning...")
        main_layout.addWidget(self.topic_input)

        # Slider & Limits
        self.label_limit = QLabel("DOCUMENTS TO SNAG: 10")
        main_layout.addWidget(self.label_limit)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(lambda v: self.label_limit.setText(f"DOCUMENTS TO SNAG: {v}"))
        main_layout.addWidget(self.slider)

        self.btn_dest = QPushButton("ASSIGN STORAGE FOLDER")
        self.btn_dest.clicked.connect(self.select_folder)
        main_layout.addWidget(self.btn_dest)

        self.btn_snag = QPushButton("START ACQUISITION")
        self.btn_snag.clicked.connect(self.start_snag)
        main_layout.addWidget(self.btn_snag)

        # Progress Ring
        self.progress_ring = AcquisitionRing()
        main_layout.addWidget(self.progress_ring, alignment=Qt.AlignCenter)

        # Console
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path: self.target_dir = path

    def start_snag(self):
        topic = self.topic_input.text().strip()
        if not topic: return
        self.btn_snag.setEnabled(False)
        limit = self.slider.value()
        self.progress_ring.update_progress(0, limit)
        
        self.worker = SnagWorker(topic, self.target_dir, limit)
        self.worker.progress.connect(lambda v: self.progress_ring.update_progress(v, limit))
        self.worker.log.connect(self.update_log)
        self.worker.finished.connect(lambda: self.btn_snag.setEnabled(True))
        self.worker.start()

    def update_log(self, text):
        self.log_output.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CaveSnagger()
    window.show()
    sys.exit(app.exec())
