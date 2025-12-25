# v21.py
# CROSSWORD PUZZLE — v21
# Save as V21.py and run. Requires PyQt6, pandas, openpyxl, pillow.
#the necessary modules you need to run this code are
#py -3.14 -m pip install PyQt6 PyQt6-Qt6 PyQt6-sip pandas openpyxl pillow

import sys
import os
import json
import random
import time
import traceback
import uuid
from datetime import datetime

from PyQt6 import QtCore, QtGui, QtWidgets
import pandas as pd

APP_TITLE = "CROSSWORD PUZZLE — V21"
CONFIG_FILE = "config.json"
LEADERBOARD_FILE = "leaderboard.csv"
GRID_SIZE = 16
WORDS_TO_PICK = 7
ADMIN_PASSWORD = "0"

# small sample pool — replace with your real dataset if needed
DUMMY_QUESTIONS = [
    {"id": 1, "clue": "Capital of France", "answer": "PARIS"},
    {"id": 2, "clue": "Largest planet", "answer": "JUPITER"},
    {"id": 3, "clue": "Opposite of hot", "answer": "COLD"},
    {"id": 4, "clue": "Feline pet", "answer": "CAT"},
    {"id": 5, "clue": "Sound unit", "answer": "DECIBEL"},
    {"id": 6, "clue": "A small stream", "answer": "BROOK"},
    {"id": 7, "clue": "Not heavy", "answer": "LIGHT"},
    {"id": 8, "clue": "To freeze water", "answer": "ICE"},
    {"id": 9, "clue": "Used for cutting", "answer": "SCISSORS"},
    {"id": 10, "clue": "Opposite of night", "answer": "DAY"},
    {"id": 11, "clue": "A flying mammal", "answer": "BAT"},
    {"id": 12, "clue": "Computer brain", "answer": "CPU"},
    {"id": 13, "clue": "Unit of memory", "answer": "BYTE"},
    {"id": 14, "clue": "Ocean animal with eight arms", "answer": "OCTOPUS"},
    {"id": 15, "clue": "Yellow fruit", "answer": "BANANA"},
    {"id": 16, "clue": "Precious metal", "answer": "GOLD"},
    {"id": 17, "clue": "Time of day [abbr]", "answer": "AM"},
    {"id": 18, "clue": "A fast animal", "answer": "CHEETAH"},
    {"id": 19, "clue": "Bird that cannot fly", "answer": "EMU"},
    {"id": 20, "clue": "Opposite of left", "answer": "RIGHT"},
]

SCORE_BY_WRONG = {0: 25, 1: 18, 2: 15, 3: 12, 4: 10, 5: 8, 6: 6, 7: 4, 8: 2}

FEEDBACK_WORDS = {
    range(1, 3): "Very Poor",
    range(3, 5): "Needs Improvement",
    range(5, 7): "Good",
    range(7, 9): "Great",
    range(9, 11): "Fantastic",
}

def feedback_word_for_rating(r):
    for rng, w in FEEDBACK_WORDS.items():
        if r in rng:
            return w
    return "Good"

# --- file utilities ---
def ensure_config():
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"admin_password": ADMIN_PASSWORD, "leaderboard_file": LEADERBOARD_FILE}, f)
        except Exception:
            traceback.print_exc()

def load_config():
    ensure_config()
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"admin_password": ADMIN_PASSWORD, "leaderboard_file": LEADERBOARD_FILE}

def load_leaderboard():
    # Ensure file exists with required columns
    required = ["EntryID", "Name", "Class", "Section", "Score", "TimeSeconds", "Rating", "FeedbackWord", "Heart"]
    if not os.path.exists(LEADERBOARD_FILE):
        df = pd.DataFrame(columns=required)
        try:
            df.to_csv(LEADERBOARD_FILE, index=False)
        except Exception:
            traceback.print_exc()
        return df
    try:
        df = pd.read_csv(LEADERBOARD_FILE)
        for col in required:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        traceback.print_exc()
        # return a safe empty dataframe with required columns
        return pd.DataFrame(columns=required)

def save_leaderboard_df(df):
    try:
        # ensure df has required cols
        required = ["EntryID", "Name", "Class", "Section", "Score", "TimeSeconds", "Rating", "FeedbackWord", "Heart"]
        for c in required:
            if c not in df.columns:
                df[c] = ""
        df.to_csv(LEADERBOARD_FILE, index=False)
    except Exception:
        traceback.print_exc()

def append_leaderboard_entry(name, clas, section, score, time_seconds):
    # defensively create an entry even if inputs are None or malformed
    try:
        df = load_leaderboard()
        entry_id = str(uuid.uuid4())
        safe_name = str(name) if name is not None else "Anonymous"
        safe_class = str(clas) if clas is not None else ""
        safe_section = str(section) if section is not None else ""
        safe_score = int(score) if (isinstance(score, (int, float)) or (str(score).isdigit())) else 0
        safe_time = int(time_seconds) if (isinstance(time_seconds, (int, float)) or (str(time_seconds).isdigit())) else 0
        new = pd.DataFrame([{
            "EntryID": entry_id,
            "Name": safe_name, "Class": safe_class, "Section": safe_section,
            "Score": safe_score, "TimeSeconds": safe_time,
            "Rating": "", "FeedbackWord": "", "Heart": ""
        }])
        df = pd.concat([df, new], ignore_index=True)
        df = df.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
        save_leaderboard_df(df)
        return df, entry_id
    except Exception:
        traceback.print_exc()
        # return an empty df and a generated id to avoid crash
        return load_leaderboard(), str(uuid.uuid4())

def update_leaderboard_by_entryid(entry_id, rating=None, feedback_word=None, heart=None):
    try:
        df = load_leaderboard()
        if df.empty:
            return False
        # robust lookup: cast to str and compare
        if "EntryID" in df.columns:
            idxs = df.index[df["EntryID"].astype(str) == str(entry_id)].tolist()
        else:
            idxs = []
        if not idxs:
            # fallback: try to find last row if entry id missing
            idxs = [len(df)-1] if len(df) > 0 else []
        changed = False
        for idx in idxs:
            if rating is not None:
                df.at[idx, "Rating"] = rating; changed = True
            if feedback_word is not None:
                df.at[idx, "FeedbackWord"] = feedback_word; changed = True
            if heart is not None:
                df.at[idx, "Heart"] = heart; changed = True
        if changed:
            df = df.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
            save_leaderboard_df(df)
        return changed
    except Exception:
        traceback.print_exc()
        return False

# --- crossword generation ---
class Placement:
    def __init__(self, word, clue, r, c, dr, dc):
        self.word = word; self.clue = clue; self.r = r; self.c = c; self.dr = dr; self.dc = dc

def empty_grid(n=GRID_SIZE):
    return [[" " for _ in range(n)] for __ in range(n)]

def fits(grid, word, r, c, dr, dc):
    n = len(grid)
    end_r = r + dr*(len(word)-1)
    end_c = c + dc*(len(word)-1)
    if not (0 <= r < n and 0 <= c < n and 0 <= end_r < n and 0 <= end_c < n):
        return False
    for i, ch in enumerate(word):
        rr = r + dr*i; cc = c + dc*i
        existing = grid[rr][cc]
        if existing != " " and existing != ch:
            return False
        if existing == " ":
            perp_dr, perp_dc = dc, dr
            for offset in (-1, 1):
                rr2 = rr + perp_dr*offset; cc2 = c + perp_dc*offset
                if 0 <= rr2 < n and 0 <= cc2 < n and grid[rr2][cc2] != " ":
                    return False
    before_r = r - dr; before_c = c - dc
    if 0 <= before_r < n and 0 <= before_c < n and grid[before_r][before_c] != " ":
        return False
    after_r = end_r + dr; after_c = end_c + dc
    if 0 <= after_r < n and 0 <= after_c < n and grid[after_r][after_c] != " ":
        return False
    return True

def place_word_on_grid(grid, word, r, c, dr, dc):
    for i, ch in enumerate(word):
        grid[r+dr*i][c+dc*i] = ch

def try_generate_grid_for_words(words):
    n = GRID_SIZE
    words_sorted = sorted(words, key=lambda w: -len(w["answer"]))
    orientations = [(0, 1), (1, 0)]
    for attempt in range(200):
        grid = empty_grid(n)
        placements = []
        first = words_sorted[0]["answer"]
        placed_first = False
        for _ in range(200):
            dr, dc = random.choice(orientations)
            r = random.randint(0, n-1); c = random.randint(0, n-1)
            if fits(grid, first, r, c, dr, dc):
                place_word_on_grid(grid, first, r, c, dr, dc)
                placements.append(Placement(first, words_sorted[0]["clue"], r, c, dr, dc))
                placed_first = True; break
        if not placed_first:
            continue
        ok = True
        for wobj in words_sorted[1:]:
            word = wobj["answer"]
            placed_this = False
            letter_positions = [(r0, c0, grid[r0][c0]) for r0 in range(n) for c0 in range(n) if grid[r0][c0] != " "]
            random.shuffle(letter_positions)
            for r0, c0, ch in letter_positions:
                for idx, ch2 in enumerate(word):
                    if ch2 != ch: continue
                    for dr, dc in orientations:
                        start_r = r0 - dr*idx; start_c = c0 - dc*idx
                        if fits(grid, word, start_r, start_c, dr, dc):
                            place_word_on_grid(grid, word, start_r, start_c, dr, dc)
                            placements.append(Placement(word, wobj["clue"], start_r, start_c, dr, dc))
                            placed_this = True; break
                    if placed_this: break
                if placed_this: break
            if placed_this: continue
            all_positions = []
            for rr in range(n):
                for cc in range(n):
                    for dr, dc in orientations:
                        if fits(grid, word, rr, cc, dr, dc):
                            all_positions.append((rr, cc, dr, dc))
            if all_positions:
                rpos, cpos, drpos, dcpos = random.choice(all_positions)
                place_word_on_grid(grid, word, rpos, cpos, drpos, dcpos)
                placements.append(Placement(word, wobj["clue"], rpos, cpos, drpos, dcpos))
            else:
                ok = False; break
        if ok:
            return grid, placements
    return None, None

def create_crossword_for_student(question_pool, pick_count=WORDS_TO_PICK):
    pool = question_pool.copy()
    if len(pool) < pick_count:
        pool = DUMMY_QUESTIONS.copy()
    pick = random.sample(pool, k=pick_count)
    for p in pick:
        p["answer"] = p["answer"].upper().replace(" ", "")
    grid, placements = try_generate_grid_for_words(pick)
    if grid is None:
        for _ in range(5):
            grid, placements = try_generate_grid_for_words(pick)
            if grid is not None:
                break
    return pick, grid, placements

# --- GUI widgets ---
class CellWidget(QtWidgets.QLineEdit):
    clicked = QtCore.pyqtSignal(int, int)
    def __init__(self, r, c, parent=None):
        super().__init__(parent)
        self.r = r; self.c = c
        self.setMaxLength(1)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setFont(QtGui.QFont("Consolas", 12))
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.setFixedSize(36, 36)
        self.correct_letter = None
        self.is_block = False
        self.locked = False
        self.setStyleSheet("background-color: white; color: black; border: 1px solid #ddd;")

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self.clicked.emit(self.r, self.c)

    def set_block(self):
        self.is_block = True
        self.setDisabled(True)
        self.setStyleSheet("background-color: #4a4a4a; border: 1px solid #333; color: white;")

    def set_locked(self):
        self.locked = True
        self.setReadOnly(True)
        self.setDisabled(True)

    def set_answer(self, ch):
        self.correct_letter = ch

    def clear_visuals(self):
        if not self.is_block:
            self.setStyleSheet("background-color: white; color: black; border: 1px solid #ddd;")

    def mark_correct(self):
        self.setStyleSheet("background-color: #b6e7b6; border: 1px solid #2e8b57; color: black;")

    def mark_incorrect(self):
        self.setStyleSheet("background-color: #f7c6c6; border: 1px solid #a52a2a; color: black;")

class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — How to Play")
        self.resize(700, 600)
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        help_html = """
        <h2>How to Play — Step by Step</h2>
        <ol>
          <li><b>Enter your Name, Class, and Section</b> and press <b>Start</b>. A new puzzle will be generated.</li>
          <li>The puzzle contains <b>7 words</b>. Words are placed horizontally (Across) or vertically (Down).</li>
          <li><b>White cells</b> are editable. Dark gray cells are blocked and not editable.</li>
          <li>Click any white cell to focus a word. The app will usually guess the direction (Across or Down) based on space available; you can press arrow keys to switch.</li>
          <li>Type letters in each white cell. Each cell only accepts a single uppercase letter.</li>
          <li>Use Backspace to clear a cell or to move backward in the current word.</li>
          <li>Press <b>Check Word</b> to evaluate the currently focused word — correct letters will be locked green; incorrect letters will be highlighted red and locked.</li>
          <li>Press <b>Check All</b> to evaluate and lock every word (you will be asked to confirm).</li>
          <li>When you've finished, press <b>Finish</b> — this will evaluate any remaining words, store your score and time on the leaderboard, and ask for feedback.</li>
        </ol>

        <h3>Scoring</h3>
        <p>Each word is scored based on the number of incorrect letters when checked:</p>
        <ul>
          <li>0 wrong — <b>25 points</b></li>
          <li>1 wrong — 18 points</li>
          <li>2 wrong — 15 points</li>
          <li>3 wrong — 12 points</li>
          <li>4 wrong — 10 points</li>
          <li>5 wrong — 8 points</li>
          <li>6 wrong — 6 points</li>
          <li>7 wrong — 4 points</li>
          <li>8+ wrong — 2 points</li>
        </ul>

        <h3>Leaderboard</h3>
        <p>After finishing, your score and time are recorded in the leaderboard (top 5 shown on the right panel). The Admin panel allows exporting, editing, or removing entries (admins only).</p>

        <h3>Tips</h3>
        <ul>
          <li>Fill obvious short words first to get intersections that help the longer ones.</li>
          <li>If you get stuck, use <b>Check Word</b> to reveal correct letters for that word (they will lock).</li>
        </ul>
        """
        text.setHtml(help_html)
        layout.addWidget(text)
        btn = QtWidgets.QPushButton("Got it")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

# --- main application ---
class CrosswordApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 820)
        ensure_config()
        cfg = load_config()
        self.admin_password = ADMIN_PASSWORD

        # state
        self.player_name = None
        self.player_class = None
        self.player_section = None
        self.question_pool = DUMMY_QUESTIONS.copy()
        self.current_questions = []
        self.grid = None
        self.placements = []
        self.cell_widgets = [[None]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.per_word_scores = {}
        self.user_locked_words = set()
        self.total_score = 0
        self.start_time = None
        self.end_time = None
        self.time_seconds = 0
        self.admin_mode = False
        self.is_dark_mode = False
        self._last_saved_entryid = None

        self.word_cells = []
        self.current_direction = None
        self.active_cell = None

        self.init_ui()

    def init_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        # left grid
        grid_frame = QtWidgets.QFrame()
        grid_layout = QtWidgets.QGridLayout(grid_frame)
        grid_layout.setSpacing(3)
        grid_layout.setContentsMargins(8, 8, 8, 8)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cw = CellWidget(r, c)
                cw.setDisabled(True)
                # The eventFilter is correctly installed here, but the method itself was missing.
                cw.installEventFilter(self)
                cw.clicked.connect(lambda rr, cc, cw=cw: self.on_cell_clicked(rr, cc, cw))
                grid_layout.addWidget(cw, r, c)
                self.cell_widgets[r][c] = cw
        main_layout.addWidget(grid_frame, 3)

        # right panel
        right = QtWidgets.QFrame()
        right.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        # player info
        pgroup = QtWidgets.QGroupBox("Player")
        pgroup.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold))
        pfl = QtWidgets.QFormLayout()
        self.label_player = QtWidgets.QLabel("Not started")
        self.label_player.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Weight.Bold))
        self.label_class = QtWidgets.QLabel("-"); self.label_class.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Weight.Bold))
        self.label_section = QtWidgets.QLabel("-"); self.label_section.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Weight.Bold))
        pfl.addRow("Name:", self.label_player)
        pfl.addRow("Class:", self.label_class)
        pfl.addRow("Section:", self.label_section)
        pgroup.setLayout(pfl)
        right_layout.addWidget(pgroup)

        # clue tabs
        self.tab_clues = QtWidgets.QTabWidget()
        self.tab_across = QtWidgets.QWidget()
        self.tab_down = QtWidgets.QWidget()
        self.tab_clues.addTab(self.tab_across, "Across")
        self.tab_clues.addTab(self.tab_down, "Down")

        # across table
        self.across_table = QtWidgets.QTableWidget()
        self.across_table.setColumnCount(3)
        self.across_table.setHorizontalHeaderLabels(["Clue No.", "Clue", "Letters"])
        self.across_table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.across_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.across_table.setSelectionMode(QtWidgets.QTableWidget.SelectionMode.SingleSelection)
        self.across_table.verticalHeader().setVisible(False)
        self.across_table.setFont(QtGui.QFont("Segoe UI", 10))
        ac_layout = QtWidgets.QVBoxLayout(self.tab_across)
        ac_layout.addWidget(self.across_table)

        # down table
        self.down_table = QtWidgets.QTableWidget()
        self.down_table.setColumnCount(3)
        self.down_table.setHorizontalHeaderLabels(["Clue No.", "Clue", "Letters"])
        self.down_table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.down_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        self.down_table.setSelectionMode(QtWidgets.QTableWidget.SelectionMode.SingleSelection)
        self.down_table.verticalHeader().setVisible(False)
        self.down_table.setFont(QtGui.QFont("Segoe UI", 10))
        dn_layout = QtWidgets.QVBoxLayout(self.tab_down)
        dn_layout.addWidget(self.down_table)

        right_layout.addWidget(self.tab_clues, 1)

        # set header resize modes to avoid big gaps:
        # keep Clue No. and Letters compact, Clue stretches to fill middle space
        ac_header = self.across_table.horizontalHeader()
        ac_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        ac_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        ac_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        dn_header = self.down_table.horizontalHeader()
        dn_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        dn_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        dn_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # connect clicks to jump
        self.across_table.cellClicked.connect(lambda r, c: self.on_clue_table_clicked(self.across_table, r))
        self.down_table.cellClicked.connect(lambda r, c: self.on_clue_table_clicked(self.down_table, r))

        # jump controls
        jump_h = QtWidgets.QHBoxLayout()
        self.jump_num = QtWidgets.QLineEdit(); self.jump_num.setFixedWidth(70); self.jump_num.setPlaceholderText("Clue #")
        self.jump_dir = QtWidgets.QComboBox(); self.jump_dir.addItems(["Across", "Down"])
        self.btn_jump = QtWidgets.QPushButton("Jump"); self.btn_jump.clicked.connect(self.on_jump)
        jump_h.addWidget(self.jump_num); jump_h.addWidget(self.jump_dir); jump_h.addWidget(self.btn_jump)
        right_layout.addLayout(jump_h)

        # control buttons
        btn_grid = QtWidgets.QGridLayout()
        self.btn_check_word = QtWidgets.QPushButton("Check Word")
        self.btn_check_all = QtWidgets.QPushButton("Check All")
        self.btn_finish = QtWidgets.QPushButton("Finish")
        self.btn_help = QtWidgets.QPushButton("Help")
        self.btn_admin = QtWidgets.QPushButton("Admin")
        self.btn_toggle_theme = QtWidgets.QPushButton("Toggle Theme")
        self.btn_about = QtWidgets.QPushButton("About")
        self.btn_exit = QtWidgets.QPushButton("Exit")

        btn_grid.addWidget(self.btn_check_word, 0, 0)
        btn_grid.addWidget(self.btn_check_all, 0, 1)
        btn_grid.addWidget(self.btn_finish, 1, 0)
        btn_grid.addWidget(self.btn_help, 1, 1)
        btn_grid.addWidget(self.btn_admin, 2, 0)
        btn_grid.addWidget(self.btn_toggle_theme, 2, 1)
        btn_grid.addWidget(self.btn_about, 3, 0, 1, 2)
        btn_grid.addWidget(self.btn_exit, 4, 0, 1, 2)

        right_layout.addLayout(btn_grid)

        # score
        sgroup = QtWidgets.QGroupBox("Score")
        sgroup.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold))
        s_v = QtWidgets.QVBoxLayout()
        self.label_score = QtWidgets.QLabel("0")
        self.label_score.setFont(QtGui.QFont("Segoe UI", 18, QtGui.QFont.Weight.Bold))
        s_v.addWidget(self.label_score)
        sgroup.setLayout(s_v)
        right_layout.addWidget(sgroup)

        # leaderboard (top 5)
        lbbox = QtWidgets.QGroupBox("Leaderboard")
        lbbox.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold))
        lb_v = QtWidgets.QVBoxLayout()
        self.lb_table = QtWidgets.QTableWidget()
        self.lb_table.setColumnCount(5)
        self.lb_table.setHorizontalHeaderLabels(["Rank", "Name", "Class", "Section", "Score"])
        self.lb_table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.lb_table.setFont(QtGui.QFont("Segoe UI", 10))
        lb_v.addWidget(self.lb_table)
        lbbox.setLayout(lb_v)
        right_layout.addWidget(lbbox, 1)

        # let the leaderboard header stretch evenly to avoid blank right-side gap
        lb_header = self.lb_table.horizontalHeader()
        lb_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        main_layout.addWidget(right, 2)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(1, 2)

        # connections
        self.btn_help.clicked.connect(self.show_help)
        self.btn_exit.clicked.connect(self.on_exit_clicked)
        self.btn_admin.clicked.connect(self.show_admin_login)
        self.btn_check_word.clicked.connect(self.check_current_word_action)
        # ERROR FIX: This connection now points to the newly added method check_all_action
        self.btn_check_all.clicked.connect(self.check_all_action)
        self.btn_finish.clicked.connect(self.finish_action)
        self.btn_toggle_theme.clicked.connect(self.toggle_theme)
        self.btn_about.clicked.connect(self.show_about_dialog)

        # initial refresh
        self.refresh_leaderboard_table()

    # -----------------------
    # Player info & motivational
    # -----------------------
    def show_player_info_dialog(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Enter Player Info")
        dlg.setModal(True)
        dlg.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        dlg_layout = QtWidgets.QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(80, 80, 80, 80)
        dlg_layout.setSpacing(24)

        title = QtWidgets.QLabel("CROSSWORD PUZZLE")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setFont(QtGui.QFont("Segoe UI", 28, QtGui.QFont.Weight.Bold))
        dlg_layout.addWidget(title)

        form_frame = QtWidgets.QFrame()
        form_layout = QtWidgets.QFormLayout(form_frame)
        name = QtWidgets.QLineEdit(); name.setFixedHeight(36); name.setFont(QtGui.QFont("Segoe UI", 14))
        clas = QtWidgets.QComboBox(); clas.addItems([str(x) for x in range(8, 13)])
        section = QtWidgets.QComboBox(); section.addItems(["Sapphire", "Topaz", "Ruby", "Emerald", "Opal", "Pearl"])
        combo_style = "background-color: white; color: black; font-weight: bold; font-size: 14px; padding: 4px;"
        clas.setStyleSheet(combo_style); section.setStyleSheet(combo_style)
        clas.setFixedHeight(34); section.setFixedHeight(34)
        btn = QtWidgets.QPushButton("Start"); btn.setFixedHeight(40); btn.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Weight.Bold))
        form_layout.addRow(QtWidgets.QLabel("Name:"), name)
        form_layout.addRow(QtWidgets.QLabel("Class:"), clas)
        form_layout.addRow(QtWidgets.QLabel("Section:"), section)
        form_layout.addRow(btn)
        dlg_layout.addWidget(form_frame, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        dlg.showFullScreen()

        def do_start():
            nm = name.text().strip()
            cl = clas.currentText().strip()
            se = section.currentText().strip()
            if not nm:
                QtWidgets.QMessageBox.warning(dlg, "Missing", "Enter your name")
                return
            self.player_name = nm; self.player_class = cl; self.player_section = se
            self.label_player.setText(nm); self.label_class.setText(cl); self.label_section.setText(se)
            dlg.accept()
            self.show_motivational_screen_and_start()

        btn.clicked.connect(do_start)
        dlg.exec()

    def show_motivational_screen_and_start(self):
        md = QtWidgets.QDialog(self)
        md.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Dialog)
        md_layout = QtWidgets.QVBoxLayout(md)
        md_layout.setContentsMargins(40, 40, 40, 40)
        md.setModal(True)

        lbl1 = QtWidgets.QLabel("GOOD PLAYERS WIN GAMES"); lbl1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl1.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Weight.Bold))
        lbl2 = QtWidgets.QLabel("GREAT ONES BREAK RECORDS"); lbl2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl2.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Weight.Bold))
        lbl3 = QtWidgets.QLabel(); lbl3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl3.setText("<span style='font-size:24pt; font-weight:bold;'><span style='color:red;'>LEGENDS</span> CHANGE THE GAME</span>")
        lbl3.setTextFormat(QtCore.Qt.TextFormat.RichText)

        md_layout.addStretch()
        md_layout.addWidget(lbl1)
        md_layout.addWidget(lbl2)
        md_layout.addWidget(lbl3)
        md_layout.addStretch()

        md.showFullScreen()
        QtCore.QTimer.singleShot(4000, lambda: (md.accept(), md.close(), self.generate_and_build()))

    # -----------------------
    # Generate / build grid
    # -----------------------
    def generate_and_build(self):
        try:
            pool = self.question_pool.copy()
            if len(pool) < WORDS_TO_PICK:
                pool = DUMMY_QUESTIONS.copy()
            self.current_questions = random.sample(pool, k=WORDS_TO_PICK)
            pick, grid, placements = create_crossword_for_student(self.current_questions, WORDS_TO_PICK)
            if grid is None:
                for _ in range(5):
                    pick, grid, placements = create_crossword_for_student(self.current_questions, WORDS_TO_PICK)
                    if grid is not None:
                        break
            if grid is None or placements is None:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to generate crossword. Try again.")
                return
            self.current_questions = pick; self.grid = grid; self.placements = placements
            self.build_grid_ui_from_solution()
            self.start_time = None; self.total_score = 0; self.label_score.setText(str(self.total_score))
            self.compute_clues_and_numbers()
        except Exception:
            traceback.print_exc()

    def build_grid_ui_from_solution(self):
        n = GRID_SIZE
        for r in range(n):
            for c in range(n):
                cw = self.cell_widgets[r][c]
                ch = self.grid[r][c] if self.grid else " "
                cw.setReadOnly(False); cw.setDisabled(False)
                cw.clear(); cw.set_answer(None); cw.locked = False; cw.is_block = False; cw.clear_visuals()

                # FIX: Connect textChanged signal for auto-advance (Horizontal movement fix)
                # The lambda ensures the current 'cw' is captured correctly
                cw.textChanged.connect(lambda txt, cw=cw: self.on_text_changed(cw))

                def make_focus(r_, c_, cw_):
                    def on_focus(ev):
                        try:
                            self.on_cell_focus(r_, c_, cw_, ev)
                        except Exception:
                            traceback.print_exc()
                        return QtWidgets.QLineEdit.focusInEvent(cw_, ev)
                    return on_focus
                cw.focusInEvent = make_focus(r, c, cw)

                if ch == " ":
                    cw.set_block()
                else:
                    cw.setEnabled(True); cw.set_answer(ch); cw.setText("")
                cw.clear_visuals()
        self.compute_clues_and_numbers()

    # -----------------------
    # clue numbering & tables
    # -----------------------
    def compute_clues_and_numbers(self):
        n = GRID_SIZE; next_num = 1
        across_clues = []; down_clues = []; placed_map = {}
        for pl in self.placements:
            placed_map[pl.word] = (pl.clue, pl)
        for r in range(n):
            for c in range(n):
                if self.grid[r][c] == " ": continue
                start_across = (c == 0 or self.grid[r][c-1] == " ")
                start_down = (r == 0 or self.grid[r-1][c] == " ")
                if start_across or start_down:
                    num = next_num; next_num += 1
                else:
                    num = 0
                if start_across:
                    cc = c; word = ""
                    while cc < n and self.grid[r][cc] != " ":
                        word += self.grid[r][cc]; cc += 1
                    clue = placed_map.get(word, ("?", None))[0]
                    across_clues.append((num, word, clue, r, c))
                if start_down:
                    rr = r; word = ""
                    while rr < n and self.grid[rr][c] != " ":
                        word += self.grid[rr][c]; rr += 1
                    clue = placed_map.get(word, ("?", None))[0]
                    down_clues.append((num, word, clue, r, c))
        self.across_clues = across_clues; self.down_clues = down_clues
        self.refresh_clue_tables()

    def refresh_clue_tables(self):
        # across
        self.across_table.setRowCount(0)
        for num, word, clue, r, c in sorted(self.across_clues, key=lambda x: x[0]):
            row = self.across_table.rowCount(); self.across_table.insertRow(row)
            item0 = QtWidgets.QTableWidgetItem(str(num))
            item1 = QtWidgets.QTableWidgetItem(str(clue))
            item2 = QtWidgets.QTableWidgetItem(str(len(word)))
            item0.setData(QtCore.Qt.ItemDataRole.UserRole, ("across", num, word, r, c))
            self.across_table.setItem(row, 0, item0); self.across_table.setItem(row, 1, item1); self.across_table.setItem(row, 2, item2)
        # down
        self.down_table.setRowCount(0)
        for num, word, clue, r, c in sorted(self.down_clues, key=lambda x: x[0]):
            row = self.down_table.rowCount(); self.down_table.insertRow(row)
            item0 = QtWidgets.QTableWidgetItem(str(num))
            item1 = QtWidgets.QTableWidgetItem(str(clue))
            item2 = QtWidgets.QTableWidgetItem(str(len(word)))
            item0.setData(QtCore.Qt.ItemDataRole.UserRole, ("down", num, word, r, c))
            self.down_table.setItem(row, 0, item0); self.down_table.setItem(row, 1, item1); self.down_table.setItem(row, 2, item2)

    def on_clue_table_clicked(self, table, row_index):
        item = table.item(row_index, 0)
        if not item: return
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not data: return
        direction, num, word, r, c = data
        self.jump_to(num, direction)

    # -----------------------
    # jump & focus helpers
    # -----------------------
    # ... (jump_to, on_jump, on_cell_clicked, find_word_start, on_cell_focus) ...
    def jump_to(self, clue_num, direction):
        if direction.lower() == "across":
            clues = self.across_clues
            dr, dc = 0, 1
        elif direction.lower() == "down":
            clues = self.down_clues
            dr, dc = 1, 0
        else: return
        target = None
        for num, word, clue, r, c in clues:
            if num == int(clue_num):
                target = (r, c, dr, dc)
                break
        if target is None: return
        r, c, dr, dc = target
        cw = self.cell_widgets[r][c]
        if cw: cw.setFocus()
        self.current_direction = (dr, dc)
        seq = []
        rr, cc = r, c
        while 0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE and self.grid[rr][cc] != " ":
            seq.append((rr, cc, self.cell_widgets[rr][cc])); rr += dr; cc += dc
        self.word_cells = seq

    def on_jump(self):
        num_str = self.jump_num.text().strip()
        direction = self.jump_dir.currentText().strip()
        if num_str.isdigit():
            self.jump_to(int(num_str), direction)
        else:
            QtWidgets.QMessageBox.warning(self, "Invalid", "Please enter a valid clue number.")

    def on_cell_clicked(self, r, c, cw):
        # When a cell is clicked, we call on_cell_focus to determine the word/direction.
        # This will set the focus if it wasn't already set, and set self.current_direction
        self.active_cell = (r, c)
        self.on_cell_focus(r, c, cw, None)

    def find_word_start(self, r, c, dr, dc):
        # Finds the start (top/left) cell of the word passing through (r, c) in direction (dr, dc)
        start_r, start_c = r, c
        while True:
            prev_r, prev_c = start_r - dr, start_c - dc
            if 0 <= prev_r < GRID_SIZE and 0 <= prev_c < GRID_SIZE and self.grid[prev_r][prev_c] != " ":
                start_r, start_c = prev_r, prev_c
            else:
                break
        return start_r, start_c

    # -----------------------
    # focus & typing handling (auto-advance)
    # -----------------------
    def on_cell_focus(self, r, c, cw, event):
        try:
            self.active_cell = (r, c)
            ac_start_r, ac_start_c = self.find_word_start(r, c, 0, 1)
            ac_cells = []; cc = ac_start_c
            while cc < GRID_SIZE and self.grid[ac_start_r][cc] != " ":
                ac_cells.append((ac_start_r, cc, self.cell_widgets[ac_start_r][cc])); cc += 1

            dn_start_r, dn_start_c = self.find_word_start(r, c, 1, 0)
            dn_cells = []; rr = dn_start_r
            while rr < GRID_SIZE and self.grid[rr][dn_start_c] != " ":
                dn_cells.append((rr, dn_start_c, self.cell_widgets[rr][dn_start_c])); rr += 1

            cd = getattr(self, "current_direction", None)

            # Logic to switch/choose direction when a cell is focused
            if cd == (0, 1) and len(ac_cells) > 1: # Prefer Across if it was already selected and valid
                self.word_cells = ac_cells; self.current_direction = (0, 1)
            elif cd == (1, 0) and len(dn_cells) > 1: # Prefer Down if it was already selected and valid
                self.word_cells = dn_cells; self.current_direction = (1, 0)
            elif len(ac_cells) >= len(dn_cells) and len(ac_cells) > 1: # Choose the longest valid direction
                self.word_cells = ac_cells; self.current_direction = (0, 1)
            elif len(dn_cells) > 1:
                self.word_cells = dn_cells; self.current_direction = (1, 0)
            else:
                 # Fallback, just pick one
                self.word_cells = ac_cells if ac_cells else dn_cells
                self.current_direction = (0, 1) if ac_cells else (1, 0)

            # Style the current active word cells
            for cr, cc, cell in self.cell_widgets_flat():
                cell.clear_visuals()
            for wr, wc, wcell in self.word_cells:
                wcell.setStyleSheet("background-color: #e6e6ff; color: black; border: 2px solid #0056b3;")

            # Style the focused cell differently
            cw.setStyleSheet("background-color: #ccccff; color: black; border: 2px solid #0056b3; font-weight: bold;")
           
            # Update the clue tab to reflect the chosen direction
            self.tab_clues.setCurrentIndex(0 if self.current_direction == (0, 1) else 1)

        except Exception:
            traceback.print_exc()

    def on_text_changed(self, obj):
        try:
            txt = obj.text().upper()
            if txt: obj.blockSignals(True); obj.setText(txt[0]); obj.blockSignals(False)
            if self.start_time is None: self.start_time = time.time()
           
            # This block of code determines the next cell for auto-advance
            dr, dc = self.current_direction if self.current_direction is not None else (0, 1)
           
            # Find the current cell's index within the active word sequence
            current_index = -1
            for i, (r, c, cell) in enumerate(self.word_cells):
                if r == obj.r and c == obj.c:
                    current_index = i
                    break
           
            # Move to the next cell in the sequence if one exists
            next_index = current_index + 1
            if 0 <= next_index < len(self.word_cells):
                nr, nc, next_cell = self.word_cells[next_index]
                if not next_cell.is_block and not next_cell.locked:
                    next_cell.setFocus()
           
        except Exception:
            traceback.print_exc()

    def can_move(self, r, c, dr, dc):
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
            nw = self.cell_widgets[nr][nc]; return (not nw.is_block) and (not nw.locked)
        return False

    def move_focus(self, r, c):
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            cw = self.cell_widgets[r][c]
            if cw and not cw.is_block and not cw.locked:
                cw.setFocus()

    # FIX: Add eventFilter to handle arrow keys and backspace (Horizontal movement fix)
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress and isinstance(obj, CellWidget):
            key = event.key()
            r, c = obj.r, obj.c
           
            # Handle direction switching by re-clicking the cell (Space or Enter key is usually better, but arrow keys can also trigger an internal direction switch based on context if not moving)
            if key in (QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, QtCore.Qt.Key.Key_Left, QtCore.Qt.Key.Key_Right) and (r, c) == self.active_cell:
                # If the key press is one of the directional arrows, check if we should switch direction.
                # A simple way to toggle direction is to re-run the on_cell_focus logic with the opposite initial preference.
                # However, the current on_cell_focus logic doesn't support a simple toggle flag.
                # We'll stick to simple movement and let on_cell_focus re-establish the active word on focus change.
                pass
               
            # 1. Handle standard movement (manually move focus)
            if key == QtCore.Qt.Key.Key_Right:
                self.move_focus(r, c + 1)
                return True # Event handled
            elif key == QtCore.Qt.Key.Key_Left:
                self.move_focus(r, c - 1)
                return True # Event handled
            elif key == QtCore.Qt.Key.Key_Down:
                self.move_focus(r + 1, c)
                return True # Event handled
            elif key == QtCore.Qt.Key.Key_Up:
                self.move_focus(r - 1, c)
                return True # Event handled

            # 2. Handle Backspace (move focus backwards in the current word, if the cell is empty)
            elif key == QtCore.Qt.Key.Key_Backspace and not obj.text():
                if self.current_direction is not None:
                    dr, dc = self.current_direction
                    # Move backwards: r - dr, c - dc
                    prev_r, prev_c = r - dr, c - dc
                    if 0 <= prev_r < GRID_SIZE and 0 <= prev_c < GRID_SIZE:
                        prev_cell = self.cell_widgets[prev_r][prev_c]
                        if not prev_cell.is_block and not prev_cell.locked:
                            prev_cell.setFocus()
                            return True # Event handled

        return super().eventFilter(obj, event)

    # FIX: Missing method added (Likely cause of runtime error)
    def recompute_total_score(self):
        """Recalculates the total score from individual word scores and updates the display."""
        try:
            self.total_score = sum(self.per_word_scores.values())
            self.label_score.setText(str(self.total_score))
        except Exception:
            traceback.print_exc()

    # -----------------------
    # word check & scoring
    # -----------------------
    def get_current_word_cells(self):
        focus = QtWidgets.QApplication.focusWidget(); focus_is_cell = isinstance(focus, CellWidget)
        if not focus_is_cell:
            if self.active_cell is None:
                QtWidgets.QMessageBox.information(self, "No cell selected", "Please select a cell in the word you want to check.")
                return None, None, None
            else:
                r, c = self.active_cell; focus = self.cell_widgets[r][c]
                if not isinstance(focus, CellWidget):
                    QtWidgets.QMessageBox.information(self, "No cell selected", "Please select a cell in the word you want to check.")
                    return None, None, None

        r, c = focus.r, focus.c
        cd = self.current_direction
        if cd is None: # fallback, re-run focus logic if needed
            self.on_cell_focus(r, c, focus, None)
            cd = self.current_direction

        if cd is None: # Still none, cannot proceed
            QtWidgets.QMessageBox.warning(self, "Invalid Word", "Cannot determine word direction.")
            return None, None, None

        dr, dc = cd
        start_r, start_c = self.find_word_start(r, c, dr, dc)

        cells = []
        rr, cc = start_r, start_c
        while 0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE and self.grid[rr][cc] != " ":
            cells.append((rr, cc)); rr += dr; cc += dc
        word = "".join(self.grid[r][c] for r, c in cells)
        return cells, word, cd

    def check_current_word_action(self):
        cells, solution_word, direction = self.get_current_word_cells()
        if cells is None: return
       
        key = (solution_word, cells[0][0], cells[0][1])
        if key in self.user_locked_words:
            QtWidgets.QMessageBox.information(self, "Locked", "This word has already been checked and locked."); return
           
        wrong_positions = []
        for idx, (r, c) in enumerate(cells):
            user_ch = self.cell_widgets[r][c].text().strip().upper()
            sol_ch = self.grid[r][c]
            if user_ch != sol_ch:
                wrong_positions.append(idx)
       
        wrong_count = len(wrong_positions); score = SCORE_BY_WRONG.get(wrong_count, 1)

        if wrong_count == 0:
            for r, c in cells:
                self.cell_widgets[r][c].setText(self.grid[r][c]); self.cell_widgets[r][c].mark_correct(); self.cell_widgets[r][c].set_locked()
        else:
            for idx, (r, c) in enumerate(cells):
                if idx in wrong_positions:
                    self.cell_widgets[r][c].mark_incorrect()
                else:
                    self.cell_widgets[r][c].mark_correct()
                self.cell_widgets[r][c].set_locked()
               
        if key not in self.per_word_scores:
            self.per_word_scores[key] = score; self.user_locked_words.add(key)
           
        self.recompute_total_score()
        QtWidgets.QMessageBox.information(self, "Checked", f"Word checked. Wrong letters: {wrong_count}. Score: {score}")

    # FIX: Add the missing method to resolve the AttributeError
    def check_all_action(self):
        """Action handler for the 'Check All' button, including confirmation."""
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Check All Words",
            "Are you sure you want to check and lock ALL remaining words? This cannot be undone.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            self.evaluate_all_words()
            QtWidgets.QMessageBox.information(self, "Complete", "All remaining words have been checked and locked.")


    def evaluate_all_words(self):
        for pl in self.placements:
            cells = []
            for i in range(len(pl.word)):
                rr = pl.r + pl.dr * i; cc = pl.c + pl.dc * i; cells.append((rr, cc))
           
            key = (pl.word, pl.r, pl.c)
            if key in self.user_locked_words: continue
           
            wrong_positions = []
            for idx, (r, c) in enumerate(cells):
                user_ch = self.cell_widgets[r][c].text().strip().upper()
                sol_ch = pl.word[idx]
                if user_ch != sol_ch:
                    wrong_positions.append(idx)
                   
            wrong_count = len(wrong_positions); score = SCORE_BY_WRONG.get(wrong_count, 1)

            if wrong_count == 0:
                for r, c in cells:
                    self.cell_widgets[r][c].setText(self.grid[r][c]); self.cell_widgets[r][c].mark_correct(); self.cell_widgets[r][c].set_locked()
            else:
                for idx, (r, c) in enumerate(cells):
                    if idx in wrong_positions:
                        self.cell_widgets[r][c].mark_incorrect()
                    else:
                        self.cell_widgets[r][c].mark_correct()
                    self.cell_widgets[r][c].set_locked()
                   
            if key not in self.per_word_scores:
                self.per_word_scores[key] = score; self.user_locked_words.add(key)
               
        self.recompute_total_score()

    def finish_action(self):
        try:
            # calculate time
            if self.start_time is not None:
                self.end_time = time.time(); self.time_seconds = int(self.end_time - self.start_time)
            else:
                self.time_seconds = 0
               
            # evaluate words (defensive)
            try: self.evaluate_all_words()
            except Exception: traceback.print_exc()

            # append entry safely, ensuring name/class/section present
            try:
                name = self.player_name if self.player_name else "Anonymous"
                clas = self.player_class if self.player_class else ""
                section = self.player_section if self.player_section else ""
                df, entryid = append_leaderboard_entry(name, clas, section, self.total_score, self.time_seconds)
                self._last_saved_entryid = entryid
               
                # refresh leaderboard from df safely
                try: self.refresh_leaderboard_table_from_df(df)
                except Exception: traceback.print_exc()
                self.refresh_leaderboard_table()
               
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.information(self, "Warning", "Could not save your score to the leaderboard right now.")

            # notify and lock UI (defensive)
            try:
                QtWidgets.QMessageBox.information(self, "Finished", f"Great job, {self.player_name or 'Player'}! You scored {self.total_score} points!")
            except Exception: pass
           
            try:
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        cw = self.cell_widgets[r][c]
                        if cw: cw.setDisabled(True)
            except Exception: traceback.print_exc()
           
            # show feedback in timer to avoid nested modal issues
            QtCore.QTimer.singleShot(100, self.show_feedback_dialog)
           
        except Exception:
            # catch everything to avoid a silent crash
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "Error", "An unexpected error occurred while finishing. Your progress should be safe.")

    def show_feedback_dialog(self):
        d = QtWidgets.QDialog(self); d.setWindowTitle("Crossword Feedback"); d.setModal(True); d.resize(420, 300)
        layout = QtWidgets.QVBoxLayout(d)
        lbl = QtWidgets.QLabel("How would you rate this crossword puzzle?"); lbl.setFont(QtGui.QFont("Segoe UI", 11)); layout.addWidget(lbl)
       
        rating_h = QtWidgets.QHBoxLayout(); self.rating_combo = QtWidgets.QComboBox(); self.rating_combo.addItems([str(i) for i in range(1, 11)]); self.rating_combo.setCurrentIndex(8)
        rating_h.addWidget(self.rating_combo); self.rating_word_label = QtWidgets.QLabel(feedback_word_for_rating(9)); self.rating_word_label.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Weight.Bold)); rating_h.addWidget(self.rating_word_label)
        layout.addLayout(rating_h)
       
        def on_rating_changed(idx):
            val = int(self.rating_combo.currentText()); self.rating_word_label.setText(feedback_word_for_rating(val))
        self.rating_combo.currentIndexChanged.connect(on_rating_changed)

        layout.addWidget(QtWidgets.QFrame(frameShape=QtWidgets.QFrame.Shape.HLine))
        layout.addWidget(QtWidgets.QLabel("Would you like to give a ❤️ to the developer?"))
       
        heart_h = QtWidgets.QHBoxLayout(); self.btn_heart_yes = QtWidgets.QPushButton("Yes ❤️"); self.btn_heart_no = QtWidgets.QPushButton("No"); heart_h.addWidget(self.btn_heart_yes); heart_h.addWidget(self.btn_heart_no)
        layout.addLayout(heart_h)

        btn_submit = QtWidgets.QPushButton("Submit Feedback"); layout.addWidget(btn_submit)

        def do_submit(heart_choice):
            try:
                rating = int(self.rating_combo.currentText())
                feedback_word = feedback_word_for_rating(rating)
                update_leaderboard_by_entryid(self._last_saved_entryid, rating=rating, feedback_word=feedback_word, heart=heart_choice)
                self.refresh_leaderboard_table()
                d.accept()
                QtWidgets.QMessageBox.information(self, "Thank You", "Your feedback has been saved!")
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(self, "Error", "Could not save feedback.")
       
        self.btn_heart_yes.clicked.connect(lambda: do_submit("❤️"))
        self.btn_heart_no.clicked.connect(lambda: do_submit(""))
        btn_submit.clicked.connect(lambda: do_submit("")) # Default submit with no heart
        d.exec()


    # ---- Compatibility wrapper (V21 fix) ----
    def populate_clue_lists(self):
        self.compute_clues_and_numbers()

    # -----------------------
    # utility functions
    # -----------------------
    def cell_widgets_flat(self):
        # A generator for all non-block cell widgets
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cw = self.cell_widgets[r][c]
                if cw and not cw.is_block:
                    yield r, c, cw

    def show_about_dialog(self):
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "CROSSWORD PUZZLE — V21\n\n"
            "Built with passion, precision, and problem-solving excellence.\n"
            "This crossword app reflects strong logic, clean design, and\n"
            "a commitment to making learning engaging and enjoyable.\n\n"
            "Huge respect to the developers who turned ideas into an\n"
            "interactive experience worth playing. ❤️\n\n"
            "Version: V21\n"
            "© 2024"
        )

    def show_help(self):
        dlg = HelpDialog(self); dlg.exec()

    def on_exit_clicked(self):
        ans = QtWidgets.QMessageBox.question(self, "Exit", "Are you sure you want to exit? Unsaved progress will be lost.")
        if ans == QtWidgets.QMessageBox.StandardButton.Yes:
            QtWidgets.QApplication.quit()

    def show_admin_login(self):
        dlg = QtWidgets.QDialog(self); dlg.setWindowTitle("Admin Login"); v = QtWidgets.QVBoxLayout(dlg)
        v.addWidget(QtWidgets.QLabel("Enter admin password:")); pwd = QtWidgets.QLineEdit(); pwd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password); v.addWidget(pwd)
        btn = QtWidgets.QPushButton("Login"); v.addWidget(btn)
       
        def do_login():
            if pwd.text() == ADMIN_PASSWORD:
                dlg.accept(); self.admin_mode = True; self.show_admin_panel()
            else:
                QtWidgets.QMessageBox.warning(dlg, "Wrong", "Incorrect password.")
       
        btn.clicked.connect(do_login); dlg.exec()

    # -----------------------
    # admin panel (hardened)
    # -----------------------
    def show_admin_panel(self):
        dlg = QtWidgets.QDialog(self); dlg.setWindowTitle("Admin Panel — V21"); dlg.resize(1000, 640)
        v = QtWidgets.QVBoxLayout(dlg)
        cols = ["Rank", "Name", "Class", "Section", "Score", "TimeSeconds", "Rating", "Heart"]
        table = QtWidgets.QTableWidget(); table.setColumnCount(len(cols)); table.setHorizontalHeaderLabels(cols); table.setSelectionBehavior(QtWidgets.QTableWidget.SelectionBehavior.SelectRows)
        v.addWidget(table)
       
        # stats area widgets (create early so update_stats_labels can reference safely)
        stats_frame = QtWidgets.QFrame(); stats_layout = QtWidgets.QHBoxLayout(stats_frame)
        self.stats_hearts_label = QtWidgets.QLabel("❤️ Total Hearts: 0"); self.stats_avg_label = QtWidgets.QLabel("⭐ Average Rating: N/A") # FIX: Initial N/A
        stats_layout.addWidget(self.stats_hearts_label); stats_layout.addStretch(); stats_layout.addWidget(self.stats_avg_label); v.addWidget(stats_frame)

        # FIX: Corrected Average Rating Calculation and Display
        def update_stats_labels_safe():
            try:
                df_all = load_leaderboard()
                if df_all is None or df_all.empty:
                    self.stats_hearts_label.setText("❤️ Total Hearts: 0")
                    self.stats_avg_label.setText("⭐ Average Rating: N/A")
                    return
                # hearts: count exact "❤️"
                hearts = 0
                if "Heart" in df_all.columns:
                    try:
                        hearts = df_all["Heart"].astype(str).fillna("").apply(lambda x: 1 if x.strip() == "❤️" else 0).sum()
                    except Exception: hearts = 0
                self.stats_hearts_label.setText(f"❤️ Total Hearts: {hearts}")
               
                ratings = []
                if "Rating" in df_all.columns:
                    for v_ in df_all["Rating"].astype(str).fillna(""):
                        try:
                            # Only count valid integer ratings (1 to 10)
                            iv = int(v_)
                            if 1 <= iv <= 10:
                                ratings.append(iv)
                        except: pass
               
                if ratings:
                    # FIX: Calculate average only on valid ratings
                    avg = round(sum(ratings)/len(ratings), 1)
                    self.stats_avg_label.setText(f"⭐ Average Rating: {avg} / 10")
                else:
                    # FIX: Set to N/A if no valid ratings are found
                    self.stats_avg_label.setText("⭐ Average Rating: N/A")

            except Exception:
                traceback.print_exc()
                self.stats_hearts_label.setText("❤️ Total Hearts: 0")
                self.stats_avg_label.setText("⭐ Average Rating: N/A")
       
        def refresh_table_safe():
            try:
                table.setRowCount(0)
                df_all = load_leaderboard()
                if df_all.empty:
                    table.setRowCount(0); return
                df_all = df_all.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
                for i, row_data in df_all.iterrows():
                    row = row_data.to_dict()
                    row_idx = table.rowCount(); table.insertRow(row_idx)
                   
                    item0 = QtWidgets.QTableWidgetItem(str(i+1))
                    item0.setData(QtCore.Qt.ItemDataRole.UserRole, str(row.get("EntryID", "")))
                    table.setItem(row_idx, 0, item0)
                   
                    table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row.get("Name", ""))))
                    table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(row.get("Class", ""))))
                    table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(row.get("Section", ""))))
                    table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(str(row.get("Score", ""))))
                    table.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(str(row.get("TimeSeconds", ""))))
                    table.setItem(row_idx, 6, QtWidgets.QTableWidgetItem(str(row.get("Rating", ""))))
                    table.setItem(row_idx, 7, QtWidgets.QTableWidgetItem(str(row.get("Heart", ""))))
            except Exception:
                traceback.print_exc()
            table.resizeColumnsToContents()
            update_stats_labels_safe()
           
        try:
            refresh_table_safe()
        except Exception:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(dlg, "Error", "Could not refresh leaderboard table.")

        h = QtWidgets.QHBoxLayout()
        btn_add = QtWidgets.QPushButton("Add Student"); btn_remove = QtWidgets.QPushButton("Remove Selected"); btn_edit = QtWidgets.QPushButton("Edit Score Selected")
        btn_export = QtWidgets.QPushButton("Export CSV"); btn_change_time = QtWidgets.QPushButton("Edit Time"); btn_newp = QtWidgets.QPushButton("New Puzzle")
        btn_erase = QtWidgets.QPushButton("Erase Leaderboard")
        # new button
        h.addWidget(btn_add); h.addWidget(btn_remove); h.addWidget(btn_edit); h.addWidget(btn_export); h.addWidget(btn_change_time); h.addWidget(btn_newp); h.addWidget(btn_erase)
        v.addLayout(h)

        # helper to find indexes by entryid or by name
        def find_indexes_by_entry_or_name(df_all, entryid, name):
            if df_all is None or df_all.empty: return []
            if entryid:
                try:
                    idxs = df_all.index[df_all["EntryID"].astype(str) == str(entryid)].tolist()
                    if idxs: return idxs
                except Exception: pass
            # fallback to name match (exact)
            if name:
                try:
                    idxs2 = df_all.index[df_all["Name"].astype(str) == str(name)].tolist()
                    if idxs2: return idxs2
                except Exception: pass
            return []

        def add_student():
            try:
                d = QtWidgets.QDialog(dlg); d.setWindowTitle("Add Student"); f = QtWidgets.QFormLayout(d)
                e_name = QtWidgets.QLineEdit(); e_class = QtWidgets.QLineEdit(); e_section = QtWidgets.QLineEdit(); e_score = QtWidgets.QLineEdit("0")
                btn_ok = QtWidgets.QPushButton("Add"); f.addRow("Name:", e_name); f.addRow("Class:", e_class); f.addRow("Section:", e_section); f.addRow("Score:", e_score); f.addRow(btn_ok)
               
                def do_add():
                    try:
                        nm = e_name.text().strip(); cl = e_class.text().strip(); se = e_section.text().strip()
                        sc = int(e_score.text().strip())
                    except Exception:
                        QtWidgets.QMessageBox.warning(d, "Invalid", "Enter valid values (score must be numeric).")
                        return
                   
                    try:
                        df2 = load_leaderboard(); entry_id = str(uuid.uuid4())
                        new_entry = pd.DataFrame([{"EntryID": entry_id, "Name": nm, "Class": cl, "Section": se, "Score": sc, "TimeSeconds": 0, "Rating": "", "FeedbackWord": "", "Heart": ""}])
                        df2 = pd.concat([df2, new_entry], ignore_index=True)
                        df2 = df2.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
                        save_leaderboard_df(df2); refresh_table_safe(); d.accept()
                    except Exception:
                        traceback.print_exc()
                        QtWidgets.QMessageBox.warning(d, "Error", "Could not save entry.")

                btn_ok.clicked.connect(do_add); d.exec()
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Add student failed.")

        def remove_selected():
            try:
                sel = table.selectedItems()
                if not sel:
                    QtWidgets.QMessageBox.information(dlg, "Select", "Select a row first.")
                    return
                row = sel[0].row()
                entryid = ""
                try:
                    it = table.item(row,0)
                    if it: entryid = it.data(QtCore.Qt.ItemDataRole.UserRole) or ""
                except Exception: entryid = ""

                confirm = QtWidgets.QMessageBox.question(dlg, "Remove Entry", "Are you sure you want to remove the selected entry?", QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes: return
               
                df_all = load_leaderboard()
                idxs = find_indexes_by_entry_or_name(df_all, entryid, table.item(row,1).text() if table.item(row,1) else "")
               
                if not idxs:
                    QtWidgets.QMessageBox.warning(dlg, "Not found", "Could not identify the selected entry to remove.")
                    return
                else:
                    df_all = df_all.drop(index=idxs)
                    df_all = df_all.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
                    save_leaderboard_df(df_all)
                    refresh_table_safe()
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Could not remove selected entry.")

        def edit_selected_score():
            try:
                sel = table.selectedItems()
                if not sel:
                    QtWidgets.QMessageBox.information(dlg, "Select", "Select a row first.")
                    return
                row = sel[0].row()
                entryid = ""
                try:
                    it = table.item(row,0)
                    if it: entryid = it.data(QtCore.Qt.ItemDataRole.UserRole) or ""
                except Exception: entryid = ""
               
                curr = table.item(row,4).text() if table.item(row,4) else "0"
                d = QtWidgets.QDialog(dlg); d.setWindowTitle("Edit Score"); f = QtWidgets.QFormLayout(d); e = QtWidgets.QLineEdit(curr); btn_ok = QtWidgets.QPushButton("Save"); f.addRow("New score:", e); f.addRow(btn_ok)
               
                def do_save():
                    try:
                        nv = int(e.text().strip())
                    except:
                        QtWidgets.QMessageBox.warning(d, "Invalid", "Enter numeric value")
                        return
                    try:
                        df_all = load_leaderboard()
                        idxs = find_indexes_by_entry_or_name(df_all, entryid, table.item(row,1).text() if table.item(row,1) else "")
                        if not idxs:
                            QtWidgets.QMessageBox.warning(d, "Not found", "Entry not found")
                            d.accept()
                            return
                        for i in idxs:
                            df_all.at[i, "Score"] = nv
                        df_all = df_all.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
                        save_leaderboard_df(df_all); refresh_table_safe(); d.accept()
                    except Exception:
                        traceback.print_exc()
                        QtWidgets.QMessageBox.warning(d, "Error", "Could not save score.")
                       
                btn_ok.clicked.connect(do_save); d.exec()
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Edit score failed.")

        def export_csv():
            try:
                path, _ = QtWidgets.QFileDialog.getSaveFileName(dlg, "Save CSV", "leaderboard_export.csv", "CSV Files (*.csv)")
                if not path: return
                load_leaderboard().to_csv(path, index=False)
                QtWidgets.QMessageBox.information(dlg, "Saved", f"Exported to {path}")
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Export failed.")

        def edit_time_selected():
            try:
                sel = table.selectedItems()
                if not sel:
                    QtWidgets.QMessageBox.information(dlg, "Select", "Select a row first.")
                    return
                row = sel[0].row()
                entryid = ""
                try:
                    it = table.item(row,0)
                    if it: entryid = it.data(QtCore.Qt.ItemDataRole.UserRole) or ""
                except Exception: entryid = ""
               
                curr = table.item(row,5).text() if table.item(row,5) else "0"
                d = QtWidgets.QDialog(dlg); d.setWindowTitle("Edit Time"); f = QtWidgets.QFormLayout(d); e = QtWidgets.QLineEdit(curr); btn_ok = QtWidgets.QPushButton("Save"); f.addRow("New time (seconds):", e); f.addRow(btn_ok)
               
                def do_save():
                    try:
                        nv = int(e.text().strip())
                    except:
                        QtWidgets.QMessageBox.warning(d, "Invalid", "Enter numeric value")
                        return
                    try:
                        df_all = load_leaderboard()
                        idxs = find_indexes_by_entry_or_name(df_all, entryid, table.item(row,1).text() if table.item(row,1) else "")
                        if not idxs:
                            QtWidgets.QMessageBox.warning(d, "Not found", "Entry not found")
                            d.accept()
                            return
                        for i in idxs:
                            df_all.at[i, "TimeSeconds"] = nv
                        df_all = df_all.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
                        save_leaderboard_df(df_all); refresh_table_safe(); d.accept()
                    except Exception:
                        traceback.print_exc()
                        QtWidgets.QMessageBox.warning(d, "Error", "Could not save time.")

                btn_ok.clicked.connect(do_save); d.exec()
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Edit time failed.")

        def do_new_puzzle():
            try:
                confirm = QtWidgets.QMessageBox.question(dlg, "New Puzzle", "This will reset the main application screen to prompt for a new player. Continue?", QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes: return
                dlg.accept(); self.prompt_new_puzzle()
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Could not start new puzzle.")

        def erase_leaderboard():
            try:
                confirm = QtWidgets.QMessageBox.question(dlg, "Erase Leaderboard", "This will permanently erase all leaderboard data. Are you sure?", QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes: return
               
                # create an empty leaderboard with required columns
                required = ["EntryID", "Name", "Class", "Section", "Score", "TimeSeconds", "Rating", "FeedbackWord", "Heart"]
                df_empty = pd.DataFrame(columns=required)
                save_leaderboard_df(df_empty)
                refresh_table_safe()
                QtWidgets.QMessageBox.information(dlg, "Erased", "Leaderboard has been erased.")
            except Exception:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(dlg, "Error", "Could not erase leaderboard.")

        btn_add.clicked.connect(add_student); btn_remove.clicked.connect(remove_selected); btn_edit.clicked.connect(edit_selected_score)
        btn_export.clicked.connect(export_csv); btn_change_time.clicked.connect(edit_time_selected); btn_newp.clicked.connect(do_new_puzzle); btn_erase.clicked.connect(erase_leaderboard)
       
        dlg.exec()

    # -----------------------
    # leaderboard (player side)
    # -----------------------
    def refresh_leaderboard_table(self):
        df = load_leaderboard()
        if df.empty: self.lb_table.setRowCount(0); return
       
        df2 = df.sort_values(by=["Score", "Name"], ascending=[False, True]).reset_index(drop=True)
        # ensure rank column exists safely
        if "Rank" not in df2.columns:
            df2.insert(0, "Rank", df2.index + 1)
        else:
            df2["Rank"] = df2.index + 1
        df2 = df2.head(5)
        self.refresh_leaderboard_table_from_df(df2)

    def refresh_leaderboard_table_from_df(self, df):
        df2 = df.copy().reset_index(drop=True)
        self.lb_table.setRowCount(df2.shape[0])
        for i, row in df2.iterrows():
            self.lb_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row.get("Rank", i+1))))
            self.lb_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row.get("Name", ""))))
            self.lb_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row.get("Class", ""))))
            self.lb_table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row.get("Section", ""))))
            self.lb_table.setItem(i, 4, QtWidgets.QTableWidgetItem(str(row.get("Score", ""))))
        self.lb_table.resizeColumnsToContents()

    # -----------------------
    # theme toggle (safe, assumes light/dark)
    # -----------------------
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        is_dark = getattr(self, "is_dark_mode", False)
        app = QtWidgets.QApplication.instance(); pal = QtGui.QPalette()
        if self.is_dark_mode:
            pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#0f0f0f"))
            pal.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#ffffff"))
            pal.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#1e1e1e"))
            pal.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#2a2a2a"))
            pal.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#ffffff"))
            pal.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#333333"))
            pal.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#ffffff"))
            pal.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#0056b3"))
            pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
        else:
            pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#f5f5f5"))
            pal.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#222222"))
            pal.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#ffffff"))
            pal.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#f0f0f0"))
            pal.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#000000"))
            pal.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#e0e0e0"))
            pal.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#000000"))
            pal.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#0078d7"))
            pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
        app.setPalette(pal)

    def prompt_new_puzzle(self): self.show_player_info_dialog() # Changed to show_player_info_dialog to restart process

# --- entrypoint ---
def main():
    app = QtWidgets.QApplication(sys.argv); app.setStyle("Fusion")
    pal = QtGui.QPalette(); pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#f5f5f5")); pal.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#222222")); pal.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#ffffff")); pal.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#f0f0f0")); pal.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#000000")); pal.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#e0e0e0")); pal.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#000000")); pal.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#0078d7")); pal.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(pal)
    window = CrosswordApp()
    window.show()
    window.show_player_info_dialog() # Start with player info
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
