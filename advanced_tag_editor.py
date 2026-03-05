import sys
import os
import requests

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeView, QFileSystemModel, QFormLayout, QLineEdit,
    QPushButton, QLabel, QToolBar, QMessageBox, QFileDialog, QGroupBox, 
    QStyle, QTabWidget, QTextEdit, QStatusBar, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMenu, QSlider
)
from PySide6.QtGui import QAction, QPixmap, QIcon
from PySide6.QtCore import Qt, QDir, QSize, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import mutagen
from mutagen.id3 import ID3, APIC, USLT
from mutagen.flac import FLAC, Picture as FLACPicture
from mutagen.mp4 import MP4, MP4Cover

class AdvancedTagEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Tag Editor - Enterprise Edition")
        self.resize(1200, 800)
        icon_path = "tag.ico"
        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, icon_path)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.current_file_path = None
        self.audio_file = None
        self.current_artwork_data = None  
        self.art_deleted = False

        # Setup Multimedia Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)

        self.player.positionChanged.connect(self.update_seekbar)
        self.player.durationChanged.connect(self.update_duration)

        self.setup_actions()
        self.setup_menu_and_toolbar()
        self.setup_ui()
        self.setup_statusbar()

    def setup_actions(self):
        self.open_dir_action = QAction(self.style().standardIcon(QStyle.SP_DirIcon), "Locate Folder...", self)
        self.open_dir_action.triggered.connect(self.open_directory)

        self.save_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "Save Metadata", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_metadata)
        self.save_action.setEnabled(False)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.auto_tag_action = QAction(self.style().standardIcon(QStyle.SP_ComputerIcon), "Auto Tag (Magic)", self)
        self.auto_tag_action.triggered.connect(self.auto_tag)
        self.auto_tag_action.setEnabled(False)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)

        self.btn_play_pause = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Play", self)
        self.btn_play_pause.triggered.connect(self.toggle_playback)
        self.btn_play_pause.setEnabled(False)

    def setup_menu_and_toolbar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.open_dir_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.auto_tag_action)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.about_action)

        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.open_dir_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.auto_tag_action)
        toolbar.addSeparator()
        
        toolbar.addAction(self.btn_play_pause)
        
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setFixedWidth(200)
        self.seek_slider.setToolTip("Seek Position")
        self.seek_slider.setEnabled(False)
        self.seek_slider.sliderMoved.connect(self.set_position)
        toolbar.addWidget(self.seek_slider)
        
        vol_label = QLabel("  Vol: ")
        toolbar.addWidget(vol_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.valueChanged.connect(self.set_volume)
        toolbar.addWidget(self.volume_slider)

    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Open a folder to begin.")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.dir_model = QFileSystemModel()
        self.dir_model.setRootPath("") 
        self.dir_model.setFilter(QDir.Dirs | QDir.NoDotAndDotDot | QDir.Drives)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index(""))
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.clicked.connect(self.on_folder_selected)
        
        for i in range(1, 4):
            self.tree_view.hideColumn(i)

        splitter.addWidget(self.tree_view)

        self.tabs = QTabWidget()
        
        tab_basic = QWidget()
        basic_layout = QVBoxLayout(tab_basic)
        
        v_splitter = QSplitter(Qt.Vertical)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(8)
        self.file_table.setHorizontalHeaderLabels(
            ["Filename", "Title", "Artist", "Album", "Year", "Genre", "Size", "Duration"]
        )
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.file_table.horizontalHeader().setStretchLastSection(True)
        # Mendukung seleksi banyak baris (Multiple Rows)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.file_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.file_table.itemSelectionChanged.connect(self.on_file_selected_from_table)
        
        v_splitter.addWidget(self.file_table)

        editor_widget = QWidget()
        editor_layout = QHBoxLayout(editor_widget)

        info_group = QGroupBox("Metadata Properties")
        form_layout = QFormLayout(info_group)
        self.field_title = QLineEdit()
        self.field_artist = QLineEdit()
        self.field_album = QLineEdit()
        self.field_year = QLineEdit()
        self.field_genre = QLineEdit()
        self.field_track = QLineEdit()

        form_layout.addRow("Title:", self.field_title)
        form_layout.addRow("Artist:", self.field_artist)
        form_layout.addRow("Album:", self.field_album)
        form_layout.addRow("Year:", self.field_year)
        form_layout.addRow("Genre:", self.field_genre)
        form_layout.addRow("Track:", self.field_track)

        editor_layout.addWidget(info_group)

        art_group = QGroupBox("Album Artwork & Tools")
        art_layout = QVBoxLayout(art_group)

        self.lbl_album_art = QLabel("No Artwork")
        self.lbl_album_art.setAlignment(Qt.AlignCenter)
        self.lbl_album_art.setFixedSize(220, 220)
        self.lbl_album_art.setStyleSheet("background-color: #2b2b2b; color: #888; border: 1px solid #555;")
        
        btn_layout = QHBoxLayout()
        self.btn_fetch_art = QPushButton("Fetch Art (iTunes)")
        self.btn_remove_art = QPushButton("Remove Art")
        btn_layout.addWidget(self.btn_fetch_art)
        btn_layout.addWidget(self.btn_remove_art)
        
        self.btn_auto_tag = QPushButton("Auto Tag Metadata (Magic)")
        self.btn_auto_tag.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        self.btn_auto_tag.clicked.connect(self.auto_tag)
        self.btn_fetch_art.clicked.connect(self.fetch_itunes_art)
        self.btn_remove_art.clicked.connect(self.remove_artwork)

        self.btn_auto_tag.setEnabled(False)
        self.btn_fetch_art.setEnabled(False)
        self.btn_remove_art.setEnabled(False)

        art_layout.addWidget(self.lbl_album_art)
        art_layout.addLayout(btn_layout)
        art_layout.addWidget(self.btn_auto_tag)
        art_layout.addStretch()

        editor_layout.addWidget(art_group)
        
        v_splitter.addWidget(editor_widget)
        v_splitter.setSizes([400, 300])
        basic_layout.addWidget(v_splitter)

        self.tabs.addTab(tab_basic, "Explorer & Basic Metadata")

        tab_lyrics = QWidget()
        lyrics_layout = QVBoxLayout(tab_lyrics)
        
        self.field_lyrics = QTextEdit()
        self.field_lyrics.setPlaceholderText("Lyrics will appear here...")
        
        self.btn_fetch_lyrics = QPushButton("Fetch Lyrics from LRCLIB")
        self.btn_fetch_lyrics.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.btn_fetch_lyrics.clicked.connect(self.fetch_lyrics)
        self.btn_fetch_lyrics.setEnabled(False)

        lyrics_layout.addWidget(self.field_lyrics)
        lyrics_layout.addWidget(self.btn_fetch_lyrics)
        self.tabs.addTab(tab_lyrics, "Lyrics")

        splitter.addWidget(self.tabs)
        splitter.setSizes([250, 950])

    def toggle_playback(self):
        if not self.current_file_path: return
        
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.btn_play_pause.setText("Play")
        else:
            self.player.play()
            self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.btn_play_pause.setText("Pause")

    def update_seekbar(self, position):
        self.seek_slider.setValue(position)

    def update_duration(self, duration):
        self.seek_slider.setRange(0, duration)

    def set_position(self, position):
        self.player.setPosition(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)

    def open_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Locate Music Folder", QDir.homePath())
        if dir_path:
            index = self.dir_model.index(dir_path)
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)
            self.tree_view.expand(index)
            self.populate_file_table(dir_path)

    def on_folder_selected(self, index):
        dir_path = self.dir_model.filePath(index)
        self.populate_file_table(dir_path)

    def populate_file_table(self, dir_path):
        self.file_table.setRowCount(0)
        self.clear_fields()
        self.current_file_path = None
        self.audio_file = None
        self.player.stop()
        self.btn_play_pause.setEnabled(False)
        self.seek_slider.setEnabled(False)
        
        folder = QDir(dir_path)
        filters = ["*.mp3", "*.m4a", "*.flac"]
        folder.setNameFilters(filters)
        folder.setFilter(QDir.Files)
        files = folder.entryInfoList()

        self.file_table.setRowCount(len(files))
        
        for row, file_info in enumerate(files):
            filepath = file_info.absoluteFilePath()
            filename = file_info.fileName()
            size_mb = file_info.size() / (1024 * 1024)

            title, artist, album, year, genre = "", "", "", "", ""
            duration_str = ""

            try:
                f = mutagen.File(filepath, easy=True)
                if f and getattr(f, 'tags', None) is not None:
                    title = f.tags.get('title', [''])[0]
                    artist = f.tags.get('artist', [''])[0]
                    album = f.tags.get('album', [''])[0]
                    year = f.tags.get('date', f.tags.get('year', ['']))[0]
                    genre = f.tags.get('genre', [''])[0]
                
                if f and getattr(f, 'info', None) is not None:
                    mins, secs = divmod(int(f.info.length), 60)
                    duration_str = f"{mins}:{secs:02d}"
            except Exception:
                pass

            item_filename = QTableWidgetItem(filename)
            item_filename.setData(Qt.UserRole, filepath) 
            
            self.file_table.setItem(row, 0, item_filename)
            self.file_table.setItem(row, 1, QTableWidgetItem(title))
            self.file_table.setItem(row, 2, QTableWidgetItem(artist))
            self.file_table.setItem(row, 3, QTableWidgetItem(album))
            self.file_table.setItem(row, 4, QTableWidgetItem(str(year)))
            self.file_table.setItem(row, 5, QTableWidgetItem(genre))
            self.file_table.setItem(row, 6, QTableWidgetItem(f"{size_mb:.2f} MB"))
            self.file_table.setItem(row, 7, QTableWidgetItem(duration_str))

        self.status_bar.showMessage(f"Folder loaded. Found {len(files)} audio files.")

    def show_table_context_menu(self, pos):
        item = self.file_table.itemAt(pos)
        if item is None:
            return
        
        menu = QMenu(self)
        
        action_play_pause = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Play/Pause Audio", self)
        action_play_pause.triggered.connect(self.toggle_playback)

        action_auto_tag = QAction(self.style().standardIcon(QStyle.SP_ComputerIcon), "Auto Tag Selected", self)
        action_auto_tag.triggered.connect(self.auto_tag)
        
        action_fetch_lyrics = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Fetch Lyrics (LRCLIB)", self)
        action_fetch_lyrics.triggered.connect(self.fetch_lyrics)

        menu.addAction(action_play_pause)
        menu.addSeparator()
        menu.addAction(action_auto_tag)
        menu.addAction(action_fetch_lyrics)
        menu.exec(self.file_table.viewport().mapToGlobal(pos))

    def on_file_selected_from_table(self):
        selected_rows = self.file_table.selectedItems()
        if not selected_rows:
            return
        
        # Load metadata hanya untuk baris pertama yang dipilih (untuk preview)
        row = selected_rows[0].row()
        file_path = self.file_table.item(row, 0).data(Qt.UserRole)
        self.load_metadata(file_path)

    def display_artwork(self, data):
        self.current_artwork_data = data
        self.art_deleted = False
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        scaled_pixmap = pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_album_art.setPixmap(scaled_pixmap)
        
    def remove_artwork(self):
        self.current_artwork_data = None
        self.art_deleted = True
        self.lbl_album_art.clear()
        self.lbl_album_art.setText("No Artwork\n(Will be deleted on Save)")

    def load_metadata(self, file_path):
        self.current_file_path = file_path
        self.current_artwork_data = None 
        self.art_deleted = False
        
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.btn_play_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play_pause.setText("Play")
        self.btn_play_pause.setEnabled(True)
        self.seek_slider.setEnabled(True)
        self.seek_slider.setValue(0)
        
        self.field_title.clear()
        self.field_artist.clear()
        self.field_album.clear()
        self.field_year.clear()
        self.field_genre.clear()
        self.field_track.clear()
        self.field_lyrics.clear()
        self.lbl_album_art.clear()
        self.lbl_album_art.setText("No Artwork")
        
        try:
            try:
                self.audio_file = mutagen.File(file_path, easy=True)
                if self.audio_file is None:
                    raise ValueError("Unsupported format.")
                if self.audio_file.tags is None:
                    self.audio_file.add_tags()
            except Exception:
                self.audio_file = mutagen.File(file_path)
                if getattr(self.audio_file, 'tags', None) is None:
                     self.audio_file.add_tags()

            tags = self.audio_file.tags if self.audio_file.tags else {}
            
            self.field_title.setText(tags.get('title', [''])[0])
            self.field_artist.setText(tags.get('artist', [''])[0])
            self.field_album.setText(tags.get('album', [''])[0])
            year_val = tags.get('date', tags.get('year', ['']))[0]
            self.field_year.setText(str(year_val))
            self.field_genre.setText(tags.get('genre', [''])[0])
            self.field_track.setText(str(tags.get('tracknumber', [''])[0]))

            ext = file_path.lower().split('.')[-1]
            try:
                if ext == 'mp3':
                    id3 = ID3(file_path)
                    apic = id3.getall('APIC')
                    if apic:
                        self.display_artwork(apic[0].data)
                    for key in id3.keys():
                        if key.startswith('USLT'):
                            self.field_lyrics.setPlainText(id3[key].text)
                            break
                            
                elif ext == 'm4a':
                    mp4 = MP4(file_path)
                    covr = mp4.tags.get('covr')
                    if covr:
                        self.display_artwork(covr[0])
                    lyr = mp4.tags.get('\xa9lyr')
                    if lyr:
                        self.field_lyrics.setPlainText(lyr[0])
                        
                elif ext == 'flac':
                    flac = FLAC(file_path)
                    pics = flac.pictures
                    if pics:
                        self.display_artwork(pics[0].data)
                    lyr = flac.get('lyrics') or flac.get('unsyncedlyrics')
                    if lyr:
                        self.field_lyrics.setPlainText(lyr[0])
            except Exception:
                pass

            file_name = os.path.basename(file_path)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            duration = getattr(self.audio_file.info, 'length', 0)
            mins, secs = divmod(int(duration), 60)
            
            status_text = f"Editing: {file_name}  |  Size: {size_mb:.2f} MB  |  Duration: {mins}:{secs:02d}"
            self.status_bar.showMessage(status_text)

            self.save_action.setEnabled(True)
            self.auto_tag_action.setEnabled(True)
            self.btn_auto_tag.setEnabled(True)
            self.btn_fetch_art.setEnabled(True)
            self.btn_remove_art.setEnabled(True)
            self.btn_fetch_lyrics.setEnabled(True)

        except Exception as e:
            self.current_file_path = None
            self.status_bar.showMessage("Error loading file.")
            self.save_action.setEnabled(False)
            self.auto_tag_action.setEnabled(False)
            self.btn_auto_tag.setEnabled(False)

    def auto_tag(self):
        # Ambil semua baris yang sedang disorot (bisa lebih dari satu)
        selected_items = self.file_table.selectedItems()
        if not selected_items:
            return

        unique_rows = list(set([item.row() for item in selected_items]))
        
        self.btn_auto_tag.setText(f"Tagging {len(unique_rows)} files...")
        self.btn_auto_tag.setEnabled(False)
        self.auto_tag_action.setEnabled(False)
        QApplication.processEvents()

        success_count = 0

        for row in unique_rows:
            file_path = self.file_table.item(row, 0).data(Qt.UserRole)
            
            # Coba cari dari nama file jika tabel kosong
            title_text = self.file_table.item(row, 1).text() if self.file_table.item(row, 1) else ""
            artist_text = self.file_table.item(row, 2).text() if self.file_table.item(row, 2) else ""
            
            query = f"{title_text} {artist_text}".strip()
            if not query:
                base_name = os.path.basename(file_path)
                query = os.path.splitext(base_name)[0]

            self.status_bar.showMessage(f"Processing ({success_count}/{len(unique_rows)}): {query} ...")
            QApplication.processEvents()

            url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"

            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data['resultCount'] > 0:
                        track = data['results'][0]
                        
                        new_title = track.get('trackName', title_text)
                        new_artist = track.get('artistName', artist_text)
                        new_album = track.get('collectionName', "")
                        release_date = track.get('releaseDate', '')
                        new_year = release_date[:4] if release_date else ""
                        new_genre = track.get('primaryGenreName', "")
                        new_track = str(track.get('trackNumber', ''))

                        art_data = None
                        art_url_100 = track.get('artworkUrl100', '')
                        if art_url_100:
                            art_url_600 = art_url_100.replace('100x100bb', '600x600bb')
                            img_response = requests.get(art_url_600)
                            if img_response.status_code == 200:
                                art_data = img_response.content

                        # Simpan langsung ke file di belakang layar
                        self._save_metadata_to_file(
                            file_path, new_title, new_artist, new_album, 
                            new_year, new_genre, new_track, art_data
                        )

                        # Update UI Tabel
                        self.file_table.setItem(row, 1, QTableWidgetItem(new_title))
                        self.file_table.setItem(row, 2, QTableWidgetItem(new_artist))
                        self.file_table.setItem(row, 3, QTableWidgetItem(new_album))
                        self.file_table.setItem(row, 4, QTableWidgetItem(new_year))
                        self.file_table.setItem(row, 5, QTableWidgetItem(new_genre))

                        success_count += 1
            except Exception as e:
                print(f"Error auto-tagging {file_path}: {e}")
                continue

        # Refresh preview panel jika file yang sedang aktif ikut di-update
        if self.current_file_path:
            self.load_metadata(self.current_file_path)

        self.btn_auto_tag.setText("Auto Tag Metadata (Magic)")
        self.btn_auto_tag.setEnabled(True)
        self.auto_tag_action.setEnabled(True)
        
        QMessageBox.information(self, "Auto Tag Complete", f"Successfully tagged {success_count} out of {len(unique_rows)} files.")
        self.status_bar.showMessage(f"Auto-tag complete. Tagged {success_count}/{len(unique_rows)} files.", 5000)

    def _save_metadata_to_file(self, file_path, title, artist, album, year, genre, track_num, art_data=None):
        """Helper function untuk menyimpan metadata langsung ke file secara programatik"""
        try:
            # 1. Update text tags
            audio = mutagen.File(file_path, easy=True)
            if audio is None: return
            if audio.tags is None: audio.add_tags()
            
            audio.tags['title'] = [title]
            audio.tags['artist'] = [artist]
            audio.tags['album'] = [album]
            audio.tags['date'] = [year]
            audio.tags['genre'] = [genre]
            audio.tags['tracknumber'] = [track_num]
            audio.save()

            # 2. Update cover art jika ditemukan
            if art_data:
                ext = file_path.lower().split('.')[-1]
                if ext == 'mp3':
                    audio_id3 = ID3(file_path)
                    audio_id3.delall("APIC") 
                    audio_id3.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=art_data))
                    audio_id3.save()
                elif ext == 'm4a':
                    audio_mp4 = MP4(file_path)
                    audio_mp4['covr'] = [MP4Cover(art_data, imageformat=MP4Cover.FORMAT_JPEG)]
                    audio_mp4.save()
                elif ext == 'flac':
                    audio_flac = FLAC(file_path)
                    pic = FLACPicture()
                    pic.type = 3
                    pic.mime = "image/jpeg"
                    pic.desc = "Front Cover"
                    pic.data = art_data
                    audio_flac.clear_pictures() 
                    audio_flac.add_picture(pic)
                    audio_flac.save()
        except Exception as e:
            print(f"Failed background save for {file_path}: {e}")

    def fetch_lyrics(self):
        title = self.field_title.text().strip()
        artist = self.field_artist.text().strip()
        album = self.field_album.text().strip()

        if not title or not artist:
            QMessageBox.warning(self, "Missing Info", "Title and Artist are required to search for lyrics.")
            return

        duration = getattr(self.audio_file.info, 'length', 0) if self.audio_file else 0

        self.btn_fetch_lyrics.setText("Searching LRCLIB...")
        self.btn_fetch_lyrics.setEnabled(False)
        QApplication.processEvents()

        lyrics = None

        try:
            if duration > 0:
                get_url = "https://lrclib.net/api/get"
                params = {
                    'track_name': title,
                    'artist_name': artist,
                    'album_name': album,
                    'duration': int(duration)
                }
                response = requests.get(get_url, params=params, timeout=7)
                
                if response.status_code == 200:
                    data = response.json()
                    lyrics = data.get('syncedLyrics') or data.get('plainLyrics')

            if not lyrics:
                search_url = "https://lrclib.net/api/search"
                params = {
                    'track_name': title,
                    'artist_name': artist
                }
                response = requests.get(search_url, params=params, timeout=7)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    lyrics = data[0].get('syncedLyrics') or data[0].get('plainLyrics')

            if lyrics:
                self.field_lyrics.setPlainText(lyrics)
                self.status_bar.showMessage("Lyrics successfully fetched from LRCLIB!", 5000)
                self.tabs.setCurrentIndex(1)
            else:
                QMessageBox.information(self, "Not Found", "No lyrics found on LRCLIB for this track.")
                
        except requests.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"Failed to connect to LRCLIB:\n{str(e)}")
        finally:
            self.btn_fetch_lyrics.setText("Fetch Lyrics from LRCLIB")
            self.btn_fetch_lyrics.setEnabled(True)

    def fetch_itunes_art(self):
        artist = self.field_artist.text()
        album = self.field_album.text()

        if not artist or not album:
            QMessageBox.warning(self, "Missing Info", "Provide Artist and Album to search.")
            return

        self.btn_fetch_art.setText("Searching...")
        self.btn_fetch_art.setEnabled(False)
        QApplication.processEvents()

        query = f"{artist} {album}"
        url = f"https://itunes.apple.com/search?term={query}&entity=album&limit=1"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data['resultCount'] > 0:
                art_url_100 = data['results'][0]['artworkUrl100']
                art_url_600 = art_url_100.replace('100x100bb', '600x600bb') 
                img_response = requests.get(art_url_600)
                img_response.raise_for_status()
                self.display_artwork(img_response.content)
            else:
                QMessageBox.information(self, "Not Found", "No album art found.")
        except requests.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"Failed to connect to iTunes API:\n{str(e)}")
        finally:
            self.btn_fetch_art.setText("Fetch Art (iTunes)")
            self.btn_fetch_art.setEnabled(True)

    def save_metadata(self):
        if not self.current_file_path or not self.audio_file:
            return

        try:
            tags = self.audio_file.tags
            if tags is not None:
                tags['title'] = [self.field_title.text()]
                tags['artist'] = [self.field_artist.text()]
                tags['album'] = [self.field_album.text()]
                tags['date'] = [self.field_year.text()]
                tags['genre'] = [self.field_genre.text()]
                tags['tracknumber'] = [self.field_track.text()]
                self.audio_file.save()

            ext = self.current_file_path.lower().split('.')[-1]
            lyrics_text = self.field_lyrics.toPlainText().strip()

            if ext == 'mp3':
                audio_id3 = ID3(self.current_file_path)
                
                if self.art_deleted:
                    audio_id3.delall("APIC")
                elif self.current_artwork_data:
                    audio_id3.delall("APIC") 
                    audio_id3.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=self.current_artwork_data))
                
                audio_id3.delall("USLT") 
                if lyrics_text:
                    audio_id3.add(USLT(encoding=3, lang='eng', desc='', text=lyrics_text))
                    
                audio_id3.save()

            elif ext == 'm4a':
                audio_mp4 = MP4(self.current_file_path)
                
                if self.art_deleted:
                    audio_mp4.pop('covr', None)
                elif self.current_artwork_data:
                    audio_mp4['covr'] = [MP4Cover(self.current_artwork_data, imageformat=MP4Cover.FORMAT_JPEG)]
                
                if lyrics_text:
                    audio_mp4['\xa9lyr'] = [lyrics_text]
                else:
                    audio_mp4.pop('\xa9lyr', None)
                    
                audio_mp4.save()

            elif ext == 'flac':
                audio_flac = FLAC(self.current_file_path)
                
                if self.art_deleted:
                    audio_flac.clear_pictures()
                elif self.current_artwork_data:
                    pic = FLACPicture()
                    pic.type = 3
                    pic.mime = "image/jpeg"
                    pic.desc = "Front Cover"
                    pic.data = self.current_artwork_data
                    audio_flac.clear_pictures() 
                    audio_flac.add_picture(pic)
                    
                if lyrics_text:
                    audio_flac['lyrics'] = [lyrics_text]
                else:
                    audio_flac.pop('lyrics', None)
                    audio_flac.pop('unsyncedlyrics', None)
                    
                audio_flac.save()

            selected = self.file_table.selectedItems()
            if selected:
                current_row = selected[0].row()
                self.file_table.setItem(current_row, 1, QTableWidgetItem(self.field_title.text()))
                self.file_table.setItem(current_row, 2, QTableWidgetItem(self.field_artist.text()))
                self.file_table.setItem(current_row, 3, QTableWidgetItem(self.field_album.text()))
                self.file_table.setItem(current_row, 4, QTableWidgetItem(self.field_year.text()))
                self.file_table.setItem(current_row, 5, QTableWidgetItem(self.field_genre.text()))

                self.status_bar.showMessage(f"✅ Saved successfully: {os.path.basename(self.current_file_path)}", 5000)

                next_row = current_row + 1
                if next_row < self.file_table.rowCount():
                    self.file_table.selectRow(next_row)
                    self.file_table.scrollToItem(self.file_table.item(next_row, 0))
                else:
                    self.status_bar.showMessage("✅ Reached the end of the list. All done!", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata:\n{str(e)}")

    def clear_fields(self):
        self.field_title.clear()
        self.field_artist.clear()
        self.field_album.clear()
        self.field_year.clear()
        self.field_genre.clear()
        self.field_track.clear()
        self.field_lyrics.clear()
        self.lbl_album_art.clear()
        self.lbl_album_art.setText("No Artwork")

    def show_about(self):
        about_html = """
        <div style="font-family: Arial, sans-serif; line-height: 1.5;">
            <h2 style="color: #2b5797;">Advanced Tag Editor</h2>
            <b>Enterprise Edition v2.5</b>
            <hr>
            <p>Welcome to a professional-grade, high-fidelity metadata management solution engineered specifically for audio professionals, archivists, and audiophiles.</p>
            <p><b>Core Enterprise Capabilities:</b></p>
            <ul>
                <li><b>Lossless Native Playback:</b> Integrated multimedia engine for instant audio verification.</li>
                <li><b>Intelligent Automation:</b> Rapidly fetch pixel-perfect metadata and high-resolution album art via the iTunes API.</li>
                <li><b>Dynamic Batch Processing:</b> Support multi-selection auto tagging for faster workflow.</li>
                <li><b>Dynamic Dual-Engine Lyrics:</b> Synchronized and plain-text lyrics retrieval powered by LRCLIB.</li>
                <li><b>Comprehensive Format Engineering:</b> Seamless read/write operations for ID3, MP4, and FLAC Vorbis frameworks.</li>
            </ul>
            <br>
            <div style="text-align: center; font-size: 11px; color: #666;">
                <i>&copy; Macan Angkasa All Rights Reserved.</i>
            </div>
        </div>
        """
        QMessageBox.about(self, "About Advanced Tag Editor", about_html)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = AdvancedTagEditor()
    window.show()
    sys.exit(app.exec())