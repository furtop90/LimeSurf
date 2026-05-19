import sys
import os
import psutil
import json
import traceback
import qtawesome as qta
from PyQt5.QtCore import QUrl, QStringListModel, Qt, QTimer, QPoint, QThread, pyqtSignal, QRect
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLineEdit, QVBoxLayout,
                             QHBoxLayout, QWidget, QTabBar, QPushButton,
                             QStyleFactory, QCompleter, QLabel, QStackedWidget,
                             QMenu, QAction, QDialog, QListWidget, QMessageBox,
                             QWidgetAction, QFileDialog, QProgressBar, QListWidgetItem,
                             QCheckBox, QComboBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
import yt_dlp

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes


# ──────────────────────────────────────────────────────────────────────
# COMPONENTE: Ventana de Ajustes (Settings)
# ──────────────────────────────────────────────────────────────────────
class VentanaAjustes(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de LimeSurf")
        self.setFixedSize(500, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.browser_ref = parent

        self.setStyleSheet("""
            QDialog { background-color: #202124; border: 1px solid #A4DB00; }
            QLabel { color: #e8eaed; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
            QLineEdit { background-color: #292a2d; color: white; border: 1px solid #3c4043; border-radius: 4px; padding: 6px; }
            QComboBox { background-color: #292a2d; color: white; border: 1px solid #3c4043; border-radius: 4px; padding: 5px; min-width: 150px; }
            QComboBox QAbstractItemView { background-color: #292a2d; color: white; selection-background-color: #A4DB00; selection-color: #121212; }
            QPushButton { 
                background-color: #3c4043; color: white; border: 1px solid #5f6368; 
                border-radius: 4px; padding: 6px 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #A4DB00; color: #121212; border: 1px solid #A4DB00; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(18)

        lbl_titulo = QLabel("Preferencias del Navegador")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #A4DB00; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        layout_descargas = QVBoxLayout()
        layout_descargas.setSpacing(6)
        lbl_descargas = QLabel("Carpeta de descargas predeterminada:")
        lbl_descargas.setStyleSheet("font-weight: bold;")

        layout_busqueda_ruta = QHBoxLayout()
        self.txt_ruta_descargas = QLineEdit()
        self.txt_ruta_descargas.setReadOnly(True)
        self.txt_ruta_descargas.setText(self.browser_ref.configuracion.get("ruta_descargas", ""))

        btn_examinar = QPushButton("Examinar...")
        btn_examinar.setCursor(Qt.PointingHandCursor)
        btn_examinar.clicked.connect(self.examinar_carpeta)

        layout_busqueda_ruta.addWidget(self.txt_ruta_descargas)
        layout_busqueda_ruta.addWidget(btn_examinar)
        layout_descargas.addWidget(lbl_descargas)
        layout_descargas.addLayout(layout_busqueda_ruta)
        layout.addLayout(layout_descargas)

        layout_motor = QVBoxLayout()
        layout_motor.setSpacing(6)
        lbl_motor = QLabel("Motor de búsqueda predeterminado (Omnibox):")
        lbl_motor.setStyleSheet("font-weight: bold;")

        self.combo_motor = QComboBox()
        self.combo_motor.addItems(["Google", "Bing", "DuckDuckGo", "Yahoo"])

        motor_actual = self.browser_ref.configuracion.get("motor_busqueda", "Google")
        index_motor = self.combo_motor.findText(motor_actual)
        if index_motor >= 0:
            self.combo_motor.setCurrentIndex(index_motor)

        layout_motor.addWidget(lbl_motor)
        layout_motor.addWidget(self.combo_motor)
        layout.addLayout(layout_motor)

        layout.addStretch()

        layout_acciones = QHBoxLayout()
        layout_acciones.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setStyleSheet("background-color: #A4DB00; color: #121212; border: 1px solid #A4DB00;")
        btn_guardar.clicked.connect(self.guardar_ajustes)

        layout_acciones.addWidget(btn_cancelar)
        layout_acciones.addWidget(btn_guardar)
        layout.addLayout(layout_acciones)

    def examinar_carpeta(self):
        ruta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Descargas",
                                                self.txt_ruta_descargas.text())
        if ruta:
            self.txt_ruta_descargas.setText(os.path.normpath(ruta))

    def guardar_ajustes(self):
        self.browser_ref.configuracion["ruta_descargas"] = self.txt_ruta_descargas.text()
        self.browser_ref.configuracion["motor_busqueda"] = self.combo_motor.currentText()
        self.browser_ref.guardar_configuracion_global()
        self.accept()


# ──────────────────────────────────────────────────────────────────────
# COMPONENTE: Ventana "Acerca de" SoftFit Software
# ──────────────────────────────────────────────────────────────────────
class VentanaAcercaDe(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de LimeSurf")
        self.setFixedSize(460, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setStyleSheet("""
            QDialog { background-color: #202124; border: 1px solid #A4DB00; }
            QLabel { color: #e8eaed; font-family: 'Segoe UI', sans-serif; }
            QPushButton { 
                background-color: #3c4043; color: white; border: 1px solid #5f6368; 
                border-radius: 4px; padding: 6px 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #A4DB00; color: #121212; border: 1px solid #A4DB00; }
        """)

        layout = QVBoxLayout(self)
        self.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(12)

        lbl_logo = QLabel("LimeSurf")
        lbl_logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #A4DB00;")
        lbl_logo.setAlignment(Qt.AlignCenter)

        lbl_version = QLabel("Versión 1.0.0 (Build Estable 2026)")
        lbl_version.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        lbl_version.setAlignment(Qt.AlignCenter)

        lbl_info = QLabel(
            "Un navegador web portátil, rápido y eficiente diseñado bajo la arquitectura "
            "de componentes modulares de SoftFit Software.\n\n"
            "Desarrollado por: furtop90\n"
            "Core Engine: Chromium via QtWebEngine 5.15\n"
            "Estado del Entorno: Portable Studio Mode"
        )
        lbl_info.setStyleSheet("font-size: 13px; line-height: 1.4; color: #e8eaed;")
        lbl_info.setWordWrap(True)

        lbl_copy = QLabel("© 2026 SoftFit Software. Todos los derechos reservados.")
        lbl_copy.setStyleSheet("font-size: 11px; color: #5f6368;")
        lbl_copy.setAlignment(Qt.AlignCenter)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        layout.addWidget(lbl_logo)
        layout.addWidget(lbl_version)
        layout.addWidget(lbl_info)
        layout.addStretch()
        layout.addWidget(lbl_copy)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignCenter)


# ──────────────────────────────────────────────────────────────────────
# COMPONENTE: Notificación Flotante de Pantalla Completa
# ──────────────────────────────────────────────────────────────────────
class OverlayNotificacionFullScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)

        self.lbl_mensaje = QLabel("LimeSurf está en pantalla completa\nPresiona ESC para salir")
        self.lbl_mensaje.setAlignment(Qt.AlignCenter)
        self.lbl_mensaje.setStyleSheet("color: #ffffff; font-family: 'Segoe UI'; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.lbl_mensaje)

        self.setStyleSheet("""
            QWidget { background-color: rgba(32, 33, 36, 0.95); border-radius: 8px; border: 1px solid #A4DB00; }
        """)

        self.timer_cierre = QTimer(self)
        self.timer_cierre.setSingleShot(True)
        self.timer_cierre.timeout.connect(self.hide)

    def mostrar_notificacion(self, geometria_padre):
        self.adjustSize()
        x = geometria_padre.x() + (geometria_padre.width() - self.width()) // 2
        y = geometria_padre.y() + 40
        self.move(x, y)
        self.show()
        self.timer_cierre.start(3500)


# ──────────────────────────────────────────────────────────────────────
# COMPONENTE: Diálogo de Progreso de Descarga (yt-dlp)
# ──────────────────────────────────────────────────────────────────────
class DialogoProgresoDescarga(QDialog):
    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedSize(380, 130)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background-color: #292a2d; border: 1px solid #3c4043; }
            QLabel { color: #e8eaed; font-family: 'Segoe UI'; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        self.lbl_estado = QLabel("Analizando enlace y descargando flujo...")
        self.lbl_estado.setStyleSheet("font-size: 12px;")

        self.barra = QProgressBar()
        self.barra.setRange(0, 0)
        self.barra.setTextVisible(False)
        self.barra.setStyleSheet("""
            QProgressBar { border: 1px solid #3c4043; border-radius: 4px; background-color: #202124; height: 8px; }
            QProgressBar::chunk { background-color: #A4DB00; border-radius: 4px; }
        """)

        self.lbl_advertencia = QLabel("Por favor, no cierres el navegador.")
        self.lbl_advertencia.setStyleSheet("font-size: 11px; color: #9aa0a6;")

        layout.addWidget(self.lbl_estado)
        layout.addWidget(self.barra)
        layout.addWidget(self.lbl_advertencia)


# ──────────────────────────────────────────────────────────────────────
# COMPONENTE: Panel del Gestor de Descargas Nativo
# ──────────────────────────────────────────────────────────────────────
class VentanaGestorDescargas(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor de Descargas")
        self.resize(550, 400)
        self.browser_ref = parent

        self.setStyleSheet("""
            QDialog { background-color: #202124; }
            QLabel { color: #e8eaed; font-family: 'Segoe UI'; }
            QListWidget { background-color: #292a2d; border: 1px solid #3c4043; border-radius: 6px; }
            QPushButton { 
                background-color: #3c4043; color: white; border: 1px solid #5f6368; 
                border-radius: 4px; padding: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #A4DB00; color: #121212; }
        """)

        layout = QVBoxLayout(self)
        self.lbl_info = QLabel("Descargas de la sesión actual:")
        self.lbl_info.setStyleSheet("font-weight: bold; color: #A4DB00;")
        layout.addWidget(self.lbl_info)

        self.lista_widget = QListWidget()
        self.lista_widget.setSpacing(5)
        layout.addWidget(self.lista_widget)

        self.btn_cerrar = QPushButton("Cerrar Panel")
        self.btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(self.btn_cerrar)

        self.actualizar_lista()

    def actualizar_lista(self):
        self.lista_widget.clear()
        for item_descarga in self.browser_ref.descargas_activas:
            item_lista = QListWidgetItem()
            widget_celda = QWidget()
            widget_celda.setStyleSheet("background-color: #2d2e31; border: 1px solid #3c4043; border-radius: 6px;")

            layout_celda = QVBoxLayout(widget_celda)
            layout_celda.setContentsMargins(10, 8, 10, 8)

            nombre_archivo = os.path.basename(item_descarga.path())
            lbl_nombre = QLabel(nombre_archivo)
            lbl_nombre.setStyleSheet("font-weight: bold; font-size: 12px; color: #e8eaed;")

            layout_progreso = QHBoxLayout()
            barra = QProgressBar()
            barra.setStyleSheet("""
                QProgressBar { border: 1px solid #3c4043; border-radius: 4px; background-color: #202124; height: 10px; text-align: center; }
                QProgressBar::chunk { background-color: #A4DB00; border-radius: 4px; }
            """)

            total = item_descarga.totalBytes()
            recibido = item_descarga.receivedBytes()
            porcentaje = int((recibido / total) * 100) if total > 0 else 0

            barra.setValue(porcentaje)

            lbl_estado = QLabel()
            if item_descarga.isFinished():
                lbl_estado.setText("Completado")
                lbl_estado.setStyleSheet("color: #A4DB00; font-weight: bold; font-size: 11px;")
            else:
                lbl_estado.setText(f"{porcentaje}%")
                lbl_estado.setStyleSheet("color: #9aa0a6; font-weight: bold; font-size: 11px;")

            layout_progreso.addWidget(barra)
            layout_progreso.addWidget(lbl_estado)

            layout_celda.addWidget(lbl_nombre)
            layout_celda.addLayout(layout_progreso)

            item_lista.setSizeHint(widget_celda.sizeHint())
            self.lista_widget.addItem(item_lista)
            self.lista_widget.setItemWidget(item_lista, widget_celda)


# ──────────────────────────────────────────────────────────────────────
# GESTOR DE RED: Bloqueador de Anuncios Interceptable
# ──────────────────────────────────────────────────────────────────────
class AdBlockerInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.activo = True
        self.lista_negra = [
            "googlesyndication.com", "googleads", "doubleclick.net", "adservice",
            "pagead2", "adnxs.com", "adtech", "popads.net", "analytics",
            "telemetry", "scorecardresearch", "amazon-adsystem", "taboola.com",
            "outbrain.com", "adroll.com", "flurry.com", "hotjar", "smartadserver"
        ]
        self.filtros_extensiones = []

    def interceptRequest(self, info):
        if not self.activo:
            return

        url_peticion = info.requestUrl().toString().lower()

        for patron in self.lista_negra:
            if patron in url_peticion:
                info.block(True)
                return

        for patron_ext in self.filtros_extensiones:
            if patron_ext in url_peticion:
                info.block(True)
                return


# ──────────────────────────────────────────────────────────────────────
# EXTENSIÓN: Hilo secundario para yt-dlp
# ──────────────────────────────────────────────────────────────────────
class HiloDescargaYTDLP(QThread):
    senal_resultado = pyqtSignal(bool, str)

    def __init__(self, url, ruta_guardado, solo_audio=False):
        super().__init__()
        self.url = url
        self.ruta_guardado = ruta_guardado
        self.solo_audio = solo_audio

    def run(self):
        try:
            opciones = {
                'outtmpl': os.path.join(self.ruta_guardado, '%(title)s.%(ext)s'),
                'quiet': True, 'no_warnings': True
            }
            if self.solo_audio:
                opciones.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192',
                    }],
                })
            else:
                opciones.update({'format': 'bestvideo+bestaudio/best'})

            with yt_dlp.YoutubeDL(opciones) as ydl:
                ydl.download([self.url])
            self.senal_resultado.emit(True, "¡Proceso completado con éxito!")
        except Exception as e:
            self.senal_resultado.emit(False, f"Error en yt-dlp: {str(e)}")


# ──────────────────────────────────────────────────────────────────────
# COMPONENTE: Ventana de Control y Gestión de Extensiones
# ──────────────────────────────────────────────────────────────────────
class VentanaExtensiones(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor Avanzado de Componentes SoftFit")
        self.resize(600, 500)
        self.browser_ref = parent

        self.setStyleSheet("""
            QDialog { background-color: #202124; }
            QLabel { color: #e8eaed; font-family: 'Segoe UI'; }
            QListWidget { background-color: #292a2d; border: 1px solid #3c4043; border-radius: 6px; }
            QCheckBox { color: #e8eaed; }
            QCheckBox::indicator:checked { background-color: #A4DB00; border: 1px solid #A4DB00; }
        """)

        layout_principal = QVBoxLayout(self)

        self.lbl_info = QLabel("Extensiones (*add.txt) y Temas (*theme.txt) detectados:")
        self.lbl_info.setStyleSheet("font-weight: bold; color: #A4DB00;")
        layout_principal.addWidget(self.lbl_info)

        self.lista_widget = QListWidget()
        self.lista_widget.setSpacing(5)
        layout_principal.addWidget(self.lista_widget)

        layout_botones = QHBoxLayout()
        self.btn_importar = QPushButton("Importar desde .txt")
        self.btn_importar.setIcon(qta.icon('fa5s.file-import', color='#121212'))
        self.btn_importar.setStyleSheet(
            "background-color: #A4DB00; color: #121212; padding: 8px; font-weight: bold; border-radius: 4px; border: none;")
        self.btn_importar.clicked.connect(self.importar_desde_archivo)

        self.btn_eliminar = QPushButton("Eliminar Seleccionada")
        self.btn_eliminar.setStyleSheet(
            "background-color: #3c4043; color: #ff6b6b; padding: 8px; font-weight: bold; border-radius: 4px; border: 1px solid #5f6368;")
        self.btn_eliminar.clicked.connect(self.eliminar_extension)

        layout_botones.addWidget(self.btn_importar)
        layout_botones.addWidget(self.btn_eliminar)
        layout_principal.addLayout(layout_botones)

        self.cargar_lista_extensiones()

    def cargar_lista_extensiones(self):
        self.lista_widget.clear()
        for id_ext, datos in self.browser_ref.extensiones_registradas.items():
            meta = datos.get("metadata", {})

            item = QListWidgetItem()
            widget_celda = QWidget()
            widget_celda.setStyleSheet("background-color: #2d2e31; border: 1px solid #3c4043; border-radius: 6px;")

            layout_celda = QHBoxLayout(widget_celda)
            layout_celda.setContentsMargins(10, 8, 10, 8)

            str_icono = meta.get("icono", "fa5s.puzzle-piece")
            lbl_icono = QLabel()
            try:
                lbl_icono.setPixmap(qta.icon(str_icono, color='#A4DB00').pixmap(32, 32))
            except:
                lbl_icono.setPixmap(qta.icon('fa5s.puzzle-piece', color='#A4DB00').pixmap(32, 32))
            layout_celda.addWidget(lbl_icono)

            layout_txt = QVBoxLayout()
            layout_txt.setSpacing(2)

            tipo_label = "[TEMA]" if datos.get("tipo") == "theme" else "[EXT]"
            lbl_titulo = QLabel(f"{tipo_label} {meta.get('nombre', id_ext)}")
            lbl_titulo.setStyleSheet("font-weight: bold; font-size: 13px; color: #e8eaed;")

            lbl_autor = QLabel(f"Por: {meta.get('desarrollador', 'Desconocido')}")
            lbl_autor.setStyleSheet("font-size: 11px; color: #A4DB00;")

            lbl_desc = QLabel(meta.get('descripcion', 'Sin descripción proporcionada.'))
            lbl_desc.setStyleSheet("font-size: 11px; color: #9aa0a6;")
            lbl_desc.setWordWrap(True)

            layout_txt.addWidget(lbl_titulo)
            layout_txt.addWidget(lbl_autor)
            layout_txt.addWidget(lbl_desc)

            layout_celda.addLayout(layout_txt)
            layout_celda.addStretch()

            checkbox = QCheckBox()
            checkbox.setChecked(datos["activa"])
            checkbox.setCursor(Qt.PointingHandCursor)
            checkbox.stateChanged.connect(lambda estado, i=id_ext: self.alternar_estado_extension(i, estado))
            layout_celda.addWidget(checkbox)

            widget_celda.setLayout(layout_celda)
            item.setSizeHint(widget_celda.sizeHint())

            self.lista_widget.addItem(item)
            self.lista_widget.setItemWidget(item, widget_celda)

    def importar_desde_archivo(self):
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Extensión (*add.txt) o Tema (*theme.txt)", "",
            "Archivos SoftFit (*add.txt *theme.txt);;Todos los archivos (*.txt)"
        )
        if ruta_archivo:
            nombre_archivo = os.path.basename(ruta_archivo)

            if nombre_archivo.lower().endswith("theme.txt"):
                tipo = "theme"
            elif nombre_archivo.lower().endswith("add.txt"):
                tipo = "extension"
            else:
                QMessageBox.warning(self, "Formato Incorrecto",
                                    "El archivo debe terminar estrictamente en 'theme.txt' o 'add.txt'.")
                return

            try:
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    contenido_completo = f.read()

                metadata = {}
                codigo_puro = contenido_completo

                if "---METADATA---" in contenido_completo:
                    partes = contenido_completo.split("---METADATA---")
                    if len(partes) >= 3:
                        json_str = partes[1].strip()
                        metadata = json.loads(json_str)
                        codigo_puro = partes[2].strip()

                self.browser_ref.extensiones_registradas[nombre_archivo] = {
                    "tipo": tipo, "metadata": metadata, "codigo": codigo_puro, "activa": True
                }

                self.browser_ref.reiniciar_entorno_extensiones()
                self.cargar_lista_extensiones()
            except Exception as e:
                QMessageBox.critical(self, "Error de Parseo", f"Error procesando estructura:\n{str(e)}")

    def alternar_estado_extension(self, id_ext, estado):
        es_activa = (estado == Qt.Checked)
        self.browser_ref.extensiones_registradas[id_ext]["activa"] = es_activa
        self.browser_ref.reiniciar_entorno_extensiones()

    def eliminar_extension(self):
        item_seleccionado = self.lista_widget.currentItem()
        if item_seleccionado:
            widget = self.lista_widget.itemWidget(item_seleccionado)
            labels = widget.findChildren(QLabel)
            if labels:
                texto_item = labels[1].text()
                if "AdBlocker" in texto_item or "yt-dlp" in texto_item:
                    QMessageBox.warning(self, "Acción Protegida", "No se pueden borrar las extensiones del núcleo.")
                    return

                for id_ext in list(self.browser_ref.extensiones_registradas.keys()):
                    if id_ext in texto_item or self.browser_ref.extensiones_registradas[id_ext]["metadata"].get(
                            "nombre") in texto_item:
                        del self.browser_ref.extensiones_registradas[id_ext]
                        break
                self.browser_ref.reiniciar_entorno_extensiones()
                self.cargar_lista_extensiones()


# ──────────────────────────────────────────────────────────────────────
# VENTANAS AUXILIARES (Historial y Cookies)
# ──────────────────────────────────────────────────────────────────────
class VentanaHistorial(QDialog):
    def __init__(self, lista_historial, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Navegación")
        self.resize(500, 400)

        self.setStyleSheet("""
            QDialog { background-color: #202124; }
            QLabel { color: #A4DB00; font-family: 'Segoe UI'; font-weight: bold; }
            QListWidget { background-color: #292a2d; color: #e8eaed; border: 1px solid #3c4043; }
        """)

        layout = QVBoxLayout(self)
        self.lbl = QLabel("Enlaces visitados recientemente:")
        self.lista_widget = QListWidget()

        for url in reversed(list(dict.fromkeys(lista_historial))):
            self.lista_widget.addItem(url)

        self.btn_limpiar = QPushButton("Limpiar Historial")
        self.btn_limpiar.setStyleSheet(
            "background-color: #ff6b6b; color: white; border: none; padding: 6px; font-weight: bold; border-radius: 4px;")
        self.btn_limpiar.clicked.connect(self.limpiar_todo)

        layout.addWidget(self.lbl)
        layout.addWidget(self.lista_widget)
        layout.addWidget(self.btn_limpiar)
        self.lista_widget.itemDoubleClicked.connect(self.abrir_enlace)

    def abrir_enlace(self, item):
        self.parent().barra_url.setText(item.text())
        self.parent().procesar_omnibox()
        self.accept()

    def limpiar_todo(self):
        self.parent().historial_busquedas = ["https://softfitsoftware.blogspot.com"]
        self.parent().modelo_historial.setStringList(self.parent().historial_busquedas)
        self.lista_widget.clear()


class VentanaCookies(QDialog):
    def __init__(self, perfil_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrador de Cookies")
        self.resize(450, 350)
        self.store = perfil_actual.cookieStore()

        self.setStyleSheet("""
            QDialog { background-color: #202124; }
            QLabel { color: #A4DB00; font-family: 'Segoe UI'; }
            QListWidget { background-color: #292a2d; color: #e8eaed; border: 1px solid #3c4043; }
            QPushButton { background-color: #3c4043; color: white; border: 1px solid #5f6368; padding: 5px; }
            QPushButton:hover { background-color: #ff6b6b; }
        """)

        layout = QVBoxLayout(self)
        self.lbl = QLabel("Cookies detectadas en sesión activa:")
        self.lista_cookies = QListWidget()
        self.cookies_lista_interna = []

        self.store.cookieAdded.connect(self.al_agregar_cookie)

        self.btn_borrar_sel = QPushButton("Eliminar Cookie Seleccionada")
        self.btn_borrar_todo = QPushButton("Eliminar TODAS las Cookies")
        self.btn_borrar_todo.clicked.connect(self.borrar_todas)
        self.btn_borrar_sel.clicked.connect(self.borrar_seleccionada)

        layout.addWidget(self.lbl)
        layout.addWidget(self.lista_cookies)
        layout.addWidget(self.btn_borrar_sel)
        layout.addWidget(self.btn_borrar_todo)

    def al_agregar_cookie(self, cookie):
        nombre = cookie.name().data().decode('utf-8', errors='ignore')
        dominio = cookie.domain()
        identificador = f"{dominio} -> {nombre}"
        if identificador not in [self.lista_cookies.item(i).text() for i in range(self.lista_cookies.count())]:
            self.lista_cookies.addItem(identificador)
            self.cookies_lista_interna.append(cookie)

    def borrar_seleccionada(self):
        fila = self.lista_cookies.currentRow()
        if fila >= 0:
            cookie_a_borrar = self.cookies_lista_interna[fila]
            self.store.deleteCookie(cookie_a_borrar)
            self.lista_cookies.takeItem(fila)
            self.cookies_lista_interna.pop(fila)

    def borrar_todas(self):
        self.store.deleteAllCookies()
        self.lista_cookies.clear()
        self.cookies_lista_interna.clear()


# ──────────────────────────────────────────────────────────────────────
# NAVEGADOR PRINCIPAL (LimeSurf)
# ──────────────────────────────────────────────────────────────────────
class SoftFitChromeFrameless(QMainWindow):
    def __init__(self, nombre_app, url_inicio):
        super().__init__()
        self.setWindowTitle(nombre_app)
        self.setGeometry(100, 100, 1280, 720)
        self.url_predeterminada = url_inicio
        self.old_pos = QPoint()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)

        self.ruta_datos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SoftFit_UserData")
        if not os.path.exists(self.ruta_datos):
            os.makedirs(self.ruta_datos)

        self.ruta_json_extensiones = os.path.join(self.ruta_datos, "extensiones_v3.json")
        self.ruta_json_config = os.path.join(self.ruta_datos, "config.json")

        self.historial_busquedas = [self.url_predeterminada, "https://youtube.com"]

        self.bloqueador_anuncios = AdBlockerInterceptor()
        self.ytdlp_activo = True
        self.descargas_activas = []

        self.configuracion = self.cargar_configuracion_global()
        self.marcadores = self.configuracion.get("marcadores", [])

        self.extensiones_registradas = self.cargar_extensiones_persistidas()
        self.inicializar_extensiones_por_defecto()

        self.notificacion_fs = OverlayNotificacionFullScreen(self)

        # INTERFAZ BASE
        self.contenedor_superior = QWidget()
        self.contenedor_superior.setObjectName("contenedor_superior")

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.tabCloseRequested.connect(self.cerrar_pestana)
        self.tab_bar.currentChanged.connect(self.cambio_de_pestana)

        self.btn_nueva_pestana = QPushButton()
        self.btn_nueva_pestana.setIcon(qta.icon('fa5s.plus', color='#A4DB00'))
        self.btn_nueva_pestana.setFlat(True)
        self.btn_nueva_pestana.setFixedSize(28, 28)
        self.btn_nueva_pestana.setCursor(Qt.PointingHandCursor)
        self.btn_nueva_pestana.clicked.connect(lambda: self.agregar_nueva_pestaña())

        self.contenedor_botones_ventana = QWidget()
        self.crear_botones_control_ventana()

        layout_superior = QHBoxLayout(self.contenedor_superior)
        layout_superior.setContentsMargins(10, 0, 0, 0)
        layout_superior.setSpacing(4)
        layout_superior.addWidget(self.tab_bar)
        layout_superior.addWidget(self.btn_nueva_pestana)
        layout_superior.addStretch()
        layout_superior.addWidget(self.contenedor_botones_ventana)

        self.barra_navegacion = QWidget()
        self.barra_navegacion.setObjectName("barra_navegacion")
        self.crear_barra_navegacion()

        # COMPONENTE: Barra de Marcadores Física
        self.barra_marcadores = QWidget()
        self.barra_marcadores.setObjectName("barra_marcadores")
        self.layout_marcadores = QHBoxLayout(self.barra_marcadores)
        self.layout_marcadores.setContentsMargins(10, 2, 10, 2)
        self.layout_marcadores.setSpacing(6)
        self.layout_marcadores.addStretch()
        self.reconstruir_barra_marcadores_ui()

        self.paginas_stack = QStackedWidget()

        self.aplicar_estilos_base()

        layout_final = QVBoxLayout()
        layout_final.setContentsMargins(0, 0, 0, 0)
        layout_final.setSpacing(0)
        layout_final.addWidget(self.contenedor_superior)
        layout_final.addWidget(self.barra_navegacion)
        layout_final.addWidget(self.barra_marcadores)
        layout_final.addWidget(self.paginas_stack)

        contenedor_maestro = QWidget()
        contenedor_maestro.setLayout(layout_final)
        self.setCentralWidget(contenedor_maestro)

        self.optimizador_timer = QTimer()
        self.optimizador_timer.timeout.connect(self.ejecutar_optimizacion_ram)
        self.optimizador_timer.start(5000)

        self.reiniciar_entorno_extensiones()

        self.agregar_nueva_pestaña(self.url_predeterminada, "SoftFit Blog")
        self.centrar_ventana()

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:
                x = msg.lParam & 0xFFFF
                y = (msg.lParam >> 16) & 0xFFFF
                pos = self.mapFromGlobal(QPoint(x, y))
                borde = 6
                w = self.width()
                h = self.height()
                en_izq = pos.x() < borde
                en_der = pos.x() > w - borde
                en_sup = pos.y() < borde
                en_inf = pos.y() > h - borde
                if en_izq and en_sup: return True, 13
                if en_der and en_sup: return True, 14
                if en_izq and en_inf: return True, 16
                if en_der and en_inf: return True, 17
                if en_izq: return True, 10
                if en_der: return True, 11
                if en_sup: return True, 12
                if en_inf: return True, 15
        return super().nativeEvent(eventType, message)

    def cargar_configuracion_global(self):
        ruta_defecto = os.path.normpath(os.path.join(os.path.expanduser("~"), "Downloads"))
        estructura_base = {"ruta_descargas": ruta_defecto, "motor_busqueda": "Google", "marcadores": []}
        if os.path.exists(self.ruta_json_config):
            try:
                with open(self.ruta_json_config, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "marcadores" not in data:
                        data["marcadores"] = []
                    return data
            except:
                return structure_base
        return estructura_base

    def guardar_configuracion_global(self):
        try:
            self.configuracion["marcadores"] = self.marcadores
            with open(self.ruta_json_config, "w", encoding="utf-8") as f:
                json.dump(self.configuracion, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración global: {e}")

    def inicializar_extensiones_por_defecto(self):
        if "adblocker_core.add.txt" not in self.extensiones_registradas:
            self.extensiones_registradas["adblocker_core.add.txt"] = {
                "tipo": "extension",
                "metadata": {"nombre": "AdBlocker Core", "desarrollador": "SoftFit Native",
                             "descripcion": "Bloqueador de anuncios integrado.", "icono": "fa5s.shield-alt"},
                "codigo": "# Modulo controlado nativamente", "activa": True
            }
        if "ytdlp_core.add.txt" not in self.extensiones_registradas:
            self.extensiones_registradas["ytdlp_core.add.txt"] = {
                "tipo": "extension",
                "metadata": {"nombre": "yt-dlp Media Downloader", "desarrollador": "SoftFit Native",
                             "descripcion": "Extracción de contenido multimedia.", "icono": "fa5s.download"},
                "codigo": "# Modulo controlado nativamente", "activa": True
            }

    def crear_botones_control_ventana(self):
        layout_botones = QHBoxLayout(self.contenedor_botones_ventana)
        layout_botones.setContentsMargins(0, 0, 0, 0)
        layout_botones.setSpacing(0)

        btn_min = QPushButton()
        btn_min.setIcon(qta.icon('fa5s.window-minimize', color='#9aa0a6'))
        btn_min.setObjectName("btn_control_ventana")
        btn_min.clicked.connect(self.showMinimized)

        self.btn_max = QPushButton()
        self.btn_max.setIcon(qta.icon('fa5s.square', color='#9aa0a6'))
        self.btn_max.setObjectName("btn_control_ventana")
        self.btn_max.clicked.connect(self.alternar_maximizacion)

        btn_close = QPushButton()
        btn_close.setIcon(qta.icon('fa5s.times', color='#9aa0a6'))
        btn_close.setObjectName("btn_control_cerrar")
        btn_close.clicked.connect(self.close)

        layout_botones.addWidget(btn_min)
        layout_botones.addWidget(self.btn_max)
        layout_botones.addWidget(btn_close)

    def alternar_maximizacion(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setIcon(qta.icon('fa5s.square', color='#9aa0a6'))
        else:
            self.showMaximized()
            self.btn_max.setIcon(qta.icon('fa5s.copy', color='#9aa0a6'))

    def crear_barra_navegacion(self):
        layout_barra = QHBoxLayout(self.barra_navegacion)
        layout_barra.setContentsMargins(8, 5, 8, 5)
        layout_barra.setSpacing(6)

        self.btn_atras = QPushButton()
        self.btn_atras.setIcon(qta.icon('fa5s.arrow-left', color='#e8eaed'))
        self.btn_atras.setObjectName("btn_nav")
        self.btn_atras.clicked.connect(lambda: self.obtener_navegador_actual().back())

        self.btn_adelante = QPushButton()
        self.btn_adelante.setIcon(qta.icon('fa5s.arrow-right', color='#e8eaed'))
        self.btn_adelante.setObjectName("btn_nav")
        self.btn_adelante.clicked.connect(lambda: self.obtener_navegador_actual().forward())

        self.btn_recargar = QPushButton()
        self.btn_recargar.setIcon(qta.icon('fa5s.redo', color='#e8eaed'))
        self.btn_recargar.setObjectName("btn_nav")
        self.btn_recargar.clicked.connect(lambda: self.obtener_navegador_actual().reload())

        self.barra_url = QLineEdit()
        self.barra_url.setPlaceholderText("Escribe un término o dirección...")
        self.barra_url.returnPressed.connect(self.procesar_omnibox)

        # Botón marcador integrado corregido con fa5s.star (Solución al fallo fa5r)
        self.btn_marcador_estrella = QPushButton(self.barra_url)
        self.btn_marcador_estrella.setIcon(qta.icon('fa5s.star', color='#5f6368'))
        self.btn_marcador_estrella.setStyleSheet("background: transparent; border: none; padding-right: 5px;")
        self.btn_marcador_estrella.setCursor(Qt.PointingHandCursor)
        self.btn_marcador_estrella.setToolTip("Añadir esta página a marcadores")
        self.btn_marcador_estrella.clicked.connect(self.alternar_marcador_actual)

        self.barra_url.setTextMargins(0, 0, 30, 0)
        layout_interno_url = QHBoxLayout(self.barra_url)
        layout_interno_url.setContentsMargins(0, 0, 5, 0)
        layout_interno_url.addStretch()
        layout_interno_url.addWidget(self.btn_marcador_estrella)

        self.modelo_historial = QStringListModel(self.historial_busquedas)
        self.completer = QCompleter(self.modelo_historial, self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.barra_url.setCompleter(self.completer)

        self.btn_menu = QPushButton()
        self.btn_menu.setIcon(qta.icon('fa5s.ellipsis-v', color='#e8eaed'))
        self.btn_menu.setObjectName("btn_nav")
        self.btn_menu.clicked.connect(self.desplegar_menu_herramientas)

        self.lbl_ram = QLabel(" RAM: ... ")
        self.lbl_ram.setStyleSheet("color: #A4DB00; font-weight: bold; font-family: 'Segoe UI'; font-size: 11px;")

        layout_barra.addWidget(self.btn_atras)
        layout_barra.addWidget(self.btn_adelante)
        layout_barra.addWidget(self.btn_recargar)
        layout_barra.addWidget(self.barra_url)
        layout_barra.addWidget(self.lbl_ram)
        layout_barra.addWidget(self.btn_menu)

    # ──────────────────────────────────────────────────────────────────────
    # NÚCLEO LOGICO: Gestión Funcional de Marcadores
    # ──────────────────────────────────────────────────────────────────────
    def reconstruir_barra_marcadores_ui(self):
        while self.layout_marcadores.count() > 1:
            item = self.layout_marcadores.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for marcador in self.marcadores:
            btn = QPushButton(marcador["titulo"])
            btn.setIcon(qta.icon('fa5s.bookmark', color='#A4DB00'))
            btn.setObjectName("btn_marcador_item")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, url=marcador["url"]: self.cargar_url_directa(url))

            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, m=marcador: self.abrir_menu_marcador(pos, m))

            self.layout_marcadores.insertWidget(self.layout_marcadores.count() - 1, btn)

    def alternar_marcador_actual(self):
        nav = self.obtener_navegador_actual()
        if not nav: return

        url_actual = nav.url().toString()
        titulo_actual = nav.title() if nav.title().strip() else url_actual
        if len(titulo_actual) > 20: titulo_actual = titulo_actual[:17] + "..."

        existe = False
        for m in self.marcadores:
            if m["url"] == url_actual:
                existe = True
                self.marcadores.remove(m)
                break

        if not existe:
            self.marcadores.append({"titulo": titulo_actual, "url": url_actual})
            self.btn_marcador_estrella.setIcon(qta.icon('fa5s.star', color='#A4DB00'))
        else:
            self.btn_marcador_estrella.setIcon(qta.icon('fa5s.star', color='#5f6368'))

        self.guardar_configuracion_global()
        self.reconstruir_barra_marcadores_ui()

    def verificar_estado_estrella_marcador(self, url_str):
        if any(m["url"] == url_str for m in self.marcadores):
            self.btn_marcador_estrella.setIcon(qta.icon('fa5s.star', color='#A4DB00'))
        else:
            self.btn_marcador_estrella.setIcon(qta.icon('fa5s.star', color='#5f6368'))

    def abrir_menu_marcador(self, pos, marcador):
        menu = QMenu(self)
        act_eliminar = QAction("Eliminar marcador", self)
        act_eliminar.triggered.connect(lambda: self.eliminar_marcador_especifico(marcador))
        menu.addAction(act_eliminar)
        menu.exec_(self.sender().mapToGlobal(pos))

    def eliminar_marcador_especifico(self, marcador):
        if marcador in self.marcadores:
            self.marcadores.remove(marcador)
            self.guardar_configuracion_global()
            self.reconstruir_barra_marcadores_ui()
            nav = self.obtener_navegador_actual()
            if nav: self.verificar_estado_estrella_marcador(nav.url().toString())

    def cargar_url_directa(self, url):
        nav = self.obtener_navegador_actual()
        if nav: nav.setUrl(QUrl(url))

    def desplegar_menu_herramientas(self):
        menu = QMenu(self)

        widget_zoom = QWidget()
        layout_zoom = QHBoxLayout(widget_zoom)
        layout_zoom.setContentsMargins(12, 4, 12, 4)
        layout_zoom.setSpacing(10)
        lbl_zoom_txt = QLabel("Zoom")
        lbl_zoom_txt.setStyleSheet("font-family: 'Segoe UI'; color: #e8eaed; font-size: 13px; min-width: 60px;")
        btn_menos = QPushButton("-")
        btn_menos.setFixedSize(26, 26)
        btn_menos.setStyleSheet(
            "font-weight: bold; font-size: 14px; background-color: #3c4043; color: white; border: 1px solid #5f6368; border-radius: 4px;")
        nav_actual = self.obtener_navegador_actual()
        factor_actual = int(nav_actual.zoomFactor() * 100) if nav_actual else 100
        self.lbl_porcentaje = QLabel(f"{factor_actual}%")
        self.lbl_porcentaje.setAlignment(Qt.AlignCenter)
        self.lbl_porcentaje.setStyleSheet("font-family: 'Segoe UI'; color: #e8eaed; font-size: 12px; min-width: 40px;")
        btn_mas = QPushButton("+")
        btn_mas.setFixedSize(26, 26)
        btn_mas.setStyleSheet(
            "font-weight: bold; font-size: 14px; background-color: #3c4043; color: white; border: 1px solid #5f6368; border-radius: 4px;")
        btn_menos.clicked.connect(self.ejecutar_zoom_out_menu)
        btn_mas.clicked.connect(self.ejecutar_zoom_in_menu)
        layout_zoom.addWidget(lbl_zoom_txt)
        layout_zoom.addWidget(btn_menos)
        layout_zoom.addWidget(self.lbl_porcentaje)
        layout_zoom.addWidget(btn_mas)
        layout_zoom.addStretch()
        accion_zoom_render = QWidgetAction(menu)
        accion_zoom_render.setDefaultWidget(widget_zoom)
        menu.addAction(accion_zoom_render)
        menu.addSeparator()

        url_actual = nav_actual.url().toString() if nav_actual else ""
        es_youtube = "youtube.com/watch" in url_actual or "youtu.be/" in url_actual

        act_descargar_video = QAction(qta.icon('fa5s.video', color='#A4DB00'), "Descargar Video MP4", self)
        act_descargar_video.setEnabled(es_youtube and self.ytdlp_activo)
        act_descargar_video.triggered.connect(lambda: self.iniciar_captura_ytdlp(url_actual, solo_audio=False))

        act_descargar_audio = QAction(qta.icon('fa5s.music', color='#A4DB00'), "Convertir a Audio MP3", self)
        act_descargar_audio.setEnabled(es_youtube and self.ytdlp_activo)
        act_descargar_audio.triggered.connect(lambda: self.iniciar_captura_ytdlp(url_actual, solo_audio=True))

        menu.addAction(act_descargar_video)
        menu.addAction(act_descargar_audio)
        menu.addSeparator()

        act_gestor_descargas = QAction(qta.icon('fa5s.download', color='#e8eaed'), "Gestor de Descargas", self)
        act_gestor_descargas.triggered.connect(self.abrir_ventana_descargas)
        menu.addAction(act_gestor_descargas)

        act_extensiones = QAction(qta.icon('fa5s.puzzle-piece', color='#e8eaed'), "Extensiones y Temas", self)
        act_extensiones.triggered.connect(self.abrir_ventana_extensiones)
        menu.addAction(act_extensiones)

        act_ajustes = QAction(qta.icon('fa5s.cog', color='#e8eaed'), "Configuración (Ajustes)", self)
        act_ajustes.triggered.connect(self.abrir_ventana_ajustes)
        menu.addAction(act_ajustes)
        menu.addSeparator()

        act_historial = QAction(qta.icon('fa5s.history', color='#e8eaed'), "Historial", self)
        act_historial.triggered.connect(self.abrir_ventana_historial)
        act_cookies = QAction(qta.icon('fa5s.cookie', color='#e8eaed'), "Cookies y Privacidad", self)
        act_cookies.triggered.connect(self.abrir_ventana_cookies)
        menu.addAction(act_historial)
        menu.addAction(act_cookies)
        menu.addSeparator()

        act_acerca = QAction(qta.icon('fa5s.info-circle', color='#A4DB00'), "Acerca de LimeSurf", self)
        act_acerca.triggered.connect(self.abrir_ventana_acerca_de)
        menu.addAction(act_acerca)

        menu.exec_(self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height())))

    def cargar_extensiones_persistidas(self):
        if os.path.exists(self.ruta_json_extensiones):
            try:
                with open(self.ruta_json_extensiones, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def guardar_extensiones_persistadas(self):
        try:
            with open(self.ruta_json_extensiones, "w", encoding="utf-8") as f:
                json.dump(self.extensiones_registradas, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando extensiones: {e}")

    def reiniciar_entorno_extensiones(self):
        self.bloqueador_anuncios.filtros_extensiones.clear()
        self.aplicar_estilos_base()

        self.bloqueador_anuncios.activo = self.extensiones_registradas.get("adblocker_core.add.txt", {}).get("activa",
                                                                                                             True)
        self.ytdlp_activo = self.extensiones_registradas.get("ytdlp_core.add.txt", {}).get("activa", True)

        for id_ext, datos in self.extensiones_registradas.items():
            if not datos.get("activa") or id_ext in ["adblocker_core.add.txt", "ytdlp_core.add.txt"]:
                continue
            if datos.get("tipo") == "theme":
                self.setStyleSheet(datos.get("codigo", ""))
            else:
                try:
                    contexto = {"browser": self, "interceptor": self.bloqueador_anuncios, "Qt": Qt}
                    exec(datos.get("codigo", ""), contexto)
                except:
                    pass
        self.guardar_extensiones_persistadas()

    def abrir_ventana_extensiones(self):
        VentanaExtensiones(self).exec_()

    def abrir_ventana_descargas(self):
        VentanaGestorDescargas(self).exec_()

    def abrir_ventana_acerca_de(self):
        VentanaAcercaDe(self).exec_()

    def abrir_ventana_ajustes(self):
        VentanaAjustes(self).exec_()

    def procesar_intercepcion_descarga(self, item_descarga):
        directorio_ajustado = self.configuracion.get("ruta_descargas", "")
        nombre_base = os.path.basename(item_descarga.path())
        ruta_sugerida_completa = os.path.join(directorio_ajustado, nombre_base)

        ruta_final, _ = QFileDialog.getSaveFileName(self, "Confirmar descarga...", ruta_sugerida_completa,
                                                    "Todos los archivos (*.*)")
        if ruta_final:
            item_descarga.setPath(ruta_final)
            item_descarga.accept()
            self.descargas_activas.append(item_descarga)
        else:
            item_descarga.cancel()

    def gestionar_permisos_multimedia(self, url, feature):
        origen = url.toString()
        if feature in [QWebEnginePage.MediaAudioCapture, QWebEnginePage.MediaVideoCapture,
                       QWebEnginePage.MediaAudioVideoCapture]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Permisos SoftFit")
            msg_box.setText(f"El sitio web <b>{origen}</b> solicita acceso a hardware multimedia.")
            msg_box.setStyleSheet(
                "QMessageBox { background-color: #202124; color: white; } QPushButton { background-color: #3c4043; color: white; }")
            btn_p = msg_box.addButton("Permitir", QMessageBox.YesRole)
            msg_box.addButton("Denegar", QMessageBox.NoRole)
            msg_box.exec_()
            if msg_box.clickedButton() == btn_p:
                self.obtener_navegador_actual().page().setFeaturePermission(url, feature,
                                                                            QWebEnginePage.PermissionGrantedByUser)
            else:
                self.obtener_navegador_actual().page().setFeaturePermission(url, feature,
                                                                            QWebEnginePage.PermissionDeniedByUser)

    def iniciar_captura_ytdlp(self, url, solo_audio):
        ruta_por_defecto = self.configuracion.get("ruta_descargas", "")
        ruta = QFileDialog.getExistingDirectory(self, "Seleccionar destino para multimedia", ruta_por_defecto)
        if not ruta: return
        self.dialogo_espera = DialogoProgresoDescarga("Conversión Multimedia", self)
        self.hilo_ytdlp = HiloDescargaYTDLP(url, ruta, solo_audio)
        self.hilo_ytdlp.senal_resultado.connect(self.finalizar_captura_ytdlp)
        self.hilo_ytdlp.start()
        self.dialogo_espera.exec_()

    def finalizar_captura_ytdlp(self, exito, mensaje):
        if hasattr(self, 'dialogo_espera') and self.dialogo_espera.isVisible():
            self.dialogo_espera.accept()
        QMessageBox.information(self, "SoftFit Converter", mensaje)

    def ejecutar_zoom_in_menu(self):
        nav = self.obtener_navegador_actual()
        if nav:
            f = nav.zoomFactor() + 0.1
            if f <= 3.0: nav.setZoomFactor(f); self.lbl_porcentaje.setText(f"{int(f * 100)}%")

    def ejecutar_zoom_out_menu(self):
        nav = self.obtener_navegador_actual()
        if nav:
            f = nav.zoomFactor() - 0.1
            if f >= 0.3: nav.setZoomFactor(f); self.lbl_porcentaje.setText(f"{int(f * 100)}%")

    def abrir_ventana_historial(self):
        VentanaHistorial(self.historial_busquedas, self).exec_()

    def abrir_ventana_cookies(self):
        nav = self.obtener_navegador_actual()
        if nav: VentanaCookies(nav.page().profile(), self).exec_()

    def aplicar_estilos_base(self):
        css_moderno = """
            QMainWindow { background-color: #202124; }
            QWidget#contenedor_superior { background-color: #202124; border-bottom: 1px solid #292a2d; }
            QTabBar { background-color: #202124; border: none; }
            QTabBar::tab {
                background-color: #292a2d; color: #9aa0a6;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                padding: 7px 16px; min-width: 130px; max-width: 180px;
                margin-top: 6px; margin-right: 2px;
                font-family: 'Segoe UI', sans-serif; font-size: 12px;
                border: 1px solid #202124;
            }
            QTabBar::tab:selected { 
                background-color: #35363a; color: #A4DB00; 
                font-weight: bold; border-bottom: 2px solid #A4DB00; 
            }
            QTabBar::tab:hover:!selected { background-color: #3c4043; color: #e8eaed; }
            QWidget#barra_navegacion { background-color: #292a2d; border-bottom: 1px solid #202124; }

            QWidget#barra_marcadores { background-color: #202124; border-bottom: 1px solid #292a2d; min-height: 28px; }
            QPushButton#btn_marcador_item {
                background-color: transparent; color: #e8eaed; border: none;
                font-family: 'Segoe UI'; font-size: 12px; padding: 2px 8px; border-radius: 4px;
            }
            QPushButton#btn_marcador_item:hover { background-color: #292a2d; color: #A4DB00; }

            QPushButton#btn_nav { background-color: transparent; border: none; border-radius: 4px; width: 28px; height: 28px; }
            QPushButton#btn_nav:hover { background-color: #3c4043; border: 1px solid #5f6368; }
            QLineEdit {
                background-color: #202124; color: #e8eaed; border: 1px solid #3c4043; border-radius: 14px;
                padding: 5px 14px; font-family: 'Segoe UI', sans-serif; font-size: 13px;
            }
            QLineEdit:focus { background-color: #202124; border: 1px solid #A4DB00; }
            QPushButton#btn_control_ventana { background-color: transparent; border: none; width: 45px; height: 32px; }
            QPushButton#btn_control_ventana:hover { background-color: #3c4043; }
            QPushButton#btn_control_cerrar { background-color: transparent; border: none; width: 45px; height: 32px; }
            QPushButton#btn_control_cerrar:hover { background-color: #e81123; }
            QMenu { background-color: #292a2d; border: 1px solid #A4DB00; padding: 4px 0px; }
            QMenu::item { font-family: 'Segoe UI'; padding: 6px 30px 6px 14px; color: #e8eaed; }
            QMenu::item:selected { background-color: #3c4043; color: #A4DB00; }
            QMenu::separator { height: 1px; background-color: #3c4043; margin: 4px 0px; }
            QWidget { color: #e8eaed; }
        """
        self.setStyleSheet(css_moderno)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() < 38 and not self.isFullScreen():
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.old_pos.isNull() and not self.isMaximized() and not self.isFullScreen():
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = QPoint()

    def mouseDoubleClickEvent(self, event):
        if event.y() < 38 and not self.isFullScreen(): self.alternar_maximizacion()

    def agregar_nueva_pestaña(self, url=None, titulo="Nueva pestaña"):
        if url is None: url = self.url_predeterminada
        id_pestana = self.tab_bar.count()
        nombre_perfil = f"PerfilPersistente_{id_pestana}"
        perfil = QWebEngineProfile(nombre_perfil, self)
        perfil.setUrlRequestInterceptor(self.bloqueador_anuncios)
        perfil.downloadRequested.connect(self.procesar_intercepcion_descarga)

        pagina = QWebEnginePage(perfil, self)
        pagina.settings().setAttribute(pagina.settings().WebAttribute.FullScreenSupportEnabled, True)
        pagina.featurePermissionRequested.connect(self.gestionar_permisos_multimedia)

        browser = QWebEngineView()
        browser.setPage(pagina)
        pagina.fullScreenRequested.connect(self.gestionar_pantalla_completa_solicitada)
        browser.setUrl(QUrl(url))

        self.paginas_stack.addWidget(browser)
        index = self.tab_bar.addTab(titulo)
        self.tab_bar.setTabData(index, browser)
        self.tab_bar.setCurrentIndex(index)

        browser.urlChanged.connect(lambda qurl, b=browser: self.actualizar_url_en_interfaz(qurl, b))
        browser.titleChanged.connect(lambda text, b=browser: self.actualizar_titulo_pestana(text, b))

    def gestionar_pantalla_completa_solicitada(self, request):
        if request.toggleOn():
            self.contenedor_superior.setVisible(False)
            self.barra_navegacion.setVisible(False)
            self.barra_marcadores.setVisible(False)
            request.accept()
            self.showFullScreen()
            QTimer.singleShot(100, lambda: self.notificacion_fs.mostrar_notificacion(self.geometry()))
        else:
            self.notificacion_fs.hide()
            self.contenedor_superior.setVisible(True)
            self.barra_navegacion.setVisible(True)
            self.barra_marcadores.setVisible(True)
            request.accept()
            if self.isMaximized():
                self.showMaximized()
            else:
                self.showNormal()

    def cambio_de_pestana(self, index):
        if index == -1: return
        browser = self.tab_bar.tabData(index)
        if browser:
            self.paginas_stack.setCurrentWidget(browser)
            url_str = browser.url().toString()
            self.barra_url.setText(url_str)
            self.verificar_estado_estrella_marcador(url_str)

    def cerrar_pestana(self, index):
        if self.tab_bar.count() > 1:
            browser = self.tab_bar.tabData(index)
            if browser:
                self.paginas_stack.removeWidget(browser)
                browser.deleteLater()
            self.tab_bar.removeTab(index)

    def ejecutar_optimizacion_ram(self):
        proceso_actual = psutil.Process(os.getpid())
        ram_megas = proceso_actual.memory_info().rss / (1024 * 1024)
        self.lbl_ram.setText(f" RAM: {ram_megas:.1f} MB ")

    def procesar_omnibox(self):
        entrada = self.barra_url.text().strip()
        if not entrada: return

        if entrada not in self.historial_busquedas:
            self.historial_busquedas.append(entrada)
            self.modelo_historial.setStringList(self.historial_busquedas)

        es_url = False
        if entrada.startswith("http://") or entrada.startswith("https://") or entrada.startswith("localhost:"):
            es_url = True
        elif "." in entrada and " " not in entrada:
            entrada = "https://" + entrada
            es_url = True

        if not es_url:
            busqueda_limpia = entrada.replace(" ", "+")
            motor = self.configuracion.get("motor_busqueda", "Google")
            if motor == "Bing":
                entrada = f"https://www.bing.com/search?q={busqueda_limpia}"
            elif motor == "DuckDuckGo":
                entrada = f"https://duckduckgo.com/?q={busqueda_limpia}"
            elif motor == "Yahoo":
                entrada = f"https://search.yahoo.com/search?p={busqueda_limpia}"
            else:
                entrada = f"https://www.google.com/search?q={busqueda_limpia}"

        navegador = self.obtener_navegador_actual()
        if navegador: navegador.setUrl(QUrl(entrada))

    def obtener_navegador_actual(self):
        index = self.tab_bar.currentIndex()
        return self.tab_bar.tabData(index) if index != -1 else None

    def actualizar_url_en_interfaz(self, qurl, navegador_emisor):
        url_texto = qurl.toString()
        if navegador_emisor == self.obtener_navegador_actual():
            self.barra_url.setText(url_texto)
            self.verificar_estado_estrella_marcador(url_texto)
        if url_texto and url_texto not in self.historial_busquedas and "search?q=" not in url_texto and "search?p=" not in url_texto:
            self.historial_busquedas.append(url_texto)
            self.modelo_historial.setStringList(self.historial_busquedas)

    def actualizar_titulo_pestana(self, texto, navegador_emisor):
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == navegador_emisor:
                titulo_corto = texto[:12] + "..." if len(texto) > 12 else texto
                self.tab_bar.setTabText(i, titulo_corto)
                break

    def centrar_ventana(self):
        qt_rectangle = self.frameGeometry()
        desktop = QApplication.desktop()
        center_point = desktop.availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))

    # Iniciando oficialmente como LimeSurf apuntando al Blog de SoftFit Software
    ventana = SoftFitChromeFrameless("LimeSurf", "https://softfitsoftware.blogspot.com")

    ventana.show()
    sys.exit(app.exec())