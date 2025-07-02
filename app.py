"""
Приложение для обработки изображений (Вариант 29).

Это приложение позволяет загружать, обрабатывать и изменять изображения
с помощью различных операций: выбор цветового канала, регулировка яркости,
преобразование в оттенки серого и рисование линий.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2  # pylint: disable=import-error
import numpy as np
from PIL import Image, ImageTk


class ImageProcessingApp(tk.Tk):
    """Главный класс приложения для обработки изображений."""

    def __init__(self):
        """Инициализация приложения с настройками по умолчанию и интерфейсом"""
        super().__init__()
        self.title("Image Processor PRO - Вариант 29")
        self.geometry("1200x800")
        self.configure(bg="#f0f0f0")


        self.original_image = None  # Исходное изображение
        self.current_image = None   # Текущее обработанное изображение
        self.photo_image = None    # Изображение для отображения в Tkinter
        self.camera_available = False  # Доступность камеры
        self.camera_status = None  # Статус камеры в интерфейсе
        self.channel_var = None    # Переменная для выбора канала
        self.status_var = None     # Переменная для статусной строки
        self.canvas = None         # Холст для отображения изображения
        self.scroll_y = None       # Вертикальная прокрутка
        self.scroll_x = None       # Горизонтальная прокрутка
        self.camera_btn = None     # Кнопка для съемки с камеры

        self.setup_ui()  # Настройка интерфейса
        self.camera_available = self.check_camera()  # Проверка камеры
        self.update_camera_status()  # Обновление статуса камеры

    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background="#f0f0f0")
        self.style.configure('TLabel', background="#f0f0f0",
                             font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10),
                             padding=5)
        self.style.configure('Title.TLabel',
                             font=('Helvetica', 12, 'bold'))

        try:
            self.iconbitmap("icon.ico")
        except tk.TclError:
            pass

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_control_frame(main_frame)  # Панель управления
        self.create_image_frame(main_frame)    # Область изображения
        self.create_status_bar()               # Строка состояния

    def create_control_frame(self, parent):
        """Создание панели управления с кнопками и опциями."""
        control_frame = ttk.LabelFrame(parent, text="Управление",
                                       padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))

        self.create_load_frame(control_frame)
        self.create_channel_frame(control_frame)
        self.create_operation_frame(control_frame) 

    def create_load_frame(self, parent):
        """Создание фрейма с кнопками загрузки, сброса и съемки."""
        load_frame = ttk.Frame(parent)
        load_frame.pack(side=tk.LEFT, padx=10)

        # Кнопки управления
        ttk.Button(
            load_frame,
            text="Загрузить изображение",
            command=self.load_image,
            style='Accent.TButton'
        ).pack(pady=5)

        self.camera_btn = ttk.Button(
            load_frame,
            text="Сделать снимок",
            command=self.capture_from_camera
        )
        self.camera_btn.pack(pady=5)

        ttk.Button(
            load_frame,
            text="Сбросить изменения",
            command=self.reset_image
        ).pack(pady=5)

        # Статус камеры
        self.camera_status = ttk.Label(
            load_frame,
            text="Камера: проверка...",
            foreground="green"
        )
        self.camera_status.pack(pady=5)

    def create_channel_frame(self, parent):
        """Создание фрейма для выбора цветовых каналов."""
        channel_frame = ttk.LabelFrame(parent,
                                       text="Цветовые каналы",
                                       padding=10)
        channel_frame.pack(side=tk.LEFT, padx=10)

        # Переключатели цветовых каналов
        self.channel_var = tk.StringVar(value="Все")
        channels = ["Все", "Красный", "Зеленый", "Синий"]

        for channel in channels:
            ttk.Radiobutton(
                channel_frame,
                text=channel,
                variable=self.channel_var,
                value=channel,
                command=self.apply_channel
            ).pack(side=tk.LEFT, padx=5)

    def create_operation_frame(self, parent):
        """Создание фрейма с операциями над изображением."""
        operation_frame = ttk.LabelFrame(parent,
                                         text="Операции",
                                         padding=10)
        operation_frame.pack(side=tk.LEFT, padx=10)

        # Кнопки операций
        ttk.Button(
            operation_frame,
            text="Повысить яркость",
            command=self.adjust_brightness_dialog
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            operation_frame,
            text="Оттенки серого",
            command=self.convert_to_grayscale
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            operation_frame,
            text="Нарисовать линию",
            command=self.draw_line_dialog
        ).pack(side=tk.LEFT, padx=5)

    def create_image_frame(self, parent):
        """Создание фрейма для отображения изображения."""
        img_frame = ttk.LabelFrame(parent, text="Изображение",
                                   padding=10)
        img_frame.pack(fill=tk.BOTH, expand=True)

        # Настройка холста и прокрутки
        self.canvas = tk.Canvas(img_frame, bg='#333333',
                                highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(img_frame, orient="vertical",
                                      command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(img_frame, orient="horizontal",
                                      command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set,
                              xscrollcommand=self.scroll_x.set)

        # Размещение элементов
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        """Создание строки состояния внизу окна."""
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def check_camera(self):
        """Проверка доступности камеры."""
        cap = cv2.VideoCapture(0)  # pylint: disable=no-member
        if cap is None or not cap.isOpened():
            return False
        cap.release()
        return True

    def update_camera_status(self):
        """Обновление статуса камеры в интерфейсе."""
        status = "Доступна" if self.camera_available else "Недоступна"
        color = "green" if self.camera_available else "red"
        self.camera_status.config(text=f"Камера: {status}",
                                  foreground=color)
        self.camera_btn.config(
            state=tk.NORMAL if self.camera_available else tk.DISABLED)

    def load_image(self):
        """Загрузка изображения из файла."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.jpg *.jpeg *.png")]
        )

        if not file_path:
            return

        try:
            # Загрузка и конвертация изображения
            image = cv2.imread(file_path)  # pylint: disable=no-member
            if image is None:
                raise ValueError("Не удалось загрузить изображение")

            self.original_image = cv2.cvtColor(  # pylint: disable=no-member
                image, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
            self.current_image = self.original_image.copy()
            self.channel_var.set("Все")
            self.show_image()
            self.status_var.set(f"Изображение загружено: {file_path}")

        except Exception as e:
            messagebox.showerror(
                "Ошибка загрузки",
                f"Не удалось загрузить изображение:\n{str(e)}"
            )

    def capture_from_camera(self):
        """Захват изображения с камеры."""
        if not self.camera_available:
            messagebox.showerror(
                "Ошибка камеры",
                "Веб-камера недоступна"
            )
            return

        # Захват кадра с камеры
        cap = cv2.VideoCapture(0)  # pylint: disable=no-member
        ret, frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror(
                "Ошибка",
                "Не удалось получить изображение с камеры"
            )
            return

        # Обработка и отображение кадра
        self.original_image = cv2.cvtColor(  # pylint: disable=no-member
            frame, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
        self.current_image = self.original_image.copy()
        self.channel_var.set("Все")
        self.show_image()
        self.status_var.set("Изображение с камеры захвачено")

    def show_image(self):
        """Отображение текущего изображения на холсте."""
        if self.current_image is None:
            return

        # Масштабирование изображения при необходимости
        img = self.current_image.copy()
        height, width = img.shape[:2]
        max_size = 800

        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_w, new_h = int(width * scale), int(height * scale)
            img = cv2.resize(  # pylint: disable=no-member
                img, (new_w, new_h),
                interpolation=cv2.INTER_AREA  # pylint: disable=no-member
            )

        # Конвертация для Tkinter и отображение
        img_pil = Image.fromarray(img)
        self.photo_image = ImageTk.PhotoImage(img_pil)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw",
                                 image=self.photo_image)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def reset_image(self):
        """Сброс изображения к исходному состоянию."""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.channel_var.set("Все")
            self.show_image()
            self.status_var.set("Изображение сброшено к оригиналу")

    def apply_channel(self):
        """Применение выбранного цветового канала."""
        if self.original_image is None:
            return

        channel = self.channel_var.get()

        if channel == "Все":
            self.current_image = self.original_image.copy()
        else:
            # Разделение на каналы
            b, g, r = cv2.split(  # pylint: disable=no-member
                cv2.cvtColor(  # pylint: disable=no-member
                    self.original_image,
                    cv2.COLOR_RGB2BGR  # pylint: disable=no-member
                )
            )
            zeros = np.zeros_like(b)

            # Выбор нужного канала
            if channel == "Красный":
                self.current_image = cv2.merge(  # pylint: disable=no-member
                    [zeros, zeros, r])
            elif channel == "Зеленый":
                self.current_image = cv2.merge(  # pylint: disable=no-member
                    [zeros, g, zeros])
            elif channel == "Синий":
                self.current_image = cv2.merge(  # pylint: disable=no-member
                    [b, zeros, zeros])

            # Обратная конвертация
            self.current_image = cv2.cvtColor(  # pylint: disable=no-member
                self.current_image,
                cv2.COLOR_BGR2RGB  # pylint: disable=no-member
            )

        self.show_image()
        self.status_var.set(f"Применен канал: {channel}")

    def adjust_brightness_dialog(self):
        """Диалог настройки яркости."""
        if self.current_image is None:
            messagebox.showerror(
                "Ошибка",
                "Сначала загрузите изображение"
            )
            return

        # Создание диалогового окна
        dialog = tk.Toplevel(self)
        dialog.title("Настройка яркости")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Элементы диалога
        ttk.Label(
            dialog,
            text="Значение увеличения яркости (0-100):"
        ).pack(pady=5)

        value_var = tk.StringVar(value="30")
        ttk.Entry(dialog, textvariable=value_var, width=10).pack(pady=5)

        def apply():
            """Обработка нажатия кнопки Применить."""
            try:
                value = int(value_var.get())
                if not 0 <= value <= 100:
                    raise ValueError
                self.adjust_brightness(value)
                dialog.destroy()
            except ValueError:
                messagebox.showerror(
                    "Ошибка",
                    "Введите целое число от 0 до 100"
                )

        ttk.Button(dialog, text="Применить", command=apply).pack(pady=10)

    def adjust_brightness(self, value):
        """Регулировка яркости изображения."""
        # Конвертация в HSV и работа с каналом яркости
        hsv = cv2.cvtColor(  # pylint: disable=no-member
            self.current_image,
            cv2.COLOR_RGB2HSV  # pylint: disable=no-member
        )
        hue, sat, val = cv2.split(hsv)  # pylint: disable=no-member

        # Увеличение яркости
        lim = 255 - value
        val[val > lim] = 255
        val[val <= lim] += value

        # Обратная конвертация
        final_hsv = cv2.merge((hue, sat, val))  # pylint: disable=no-member
        self.current_image = cv2.cvtColor(  # pylint: disable=no-member
            final_hsv,
            cv2.COLOR_HSV2RGB  # pylint: disable=no-member
        )
        self.show_image()
        self.status_var.set(f"Яркость увеличена на {value}")

    def convert_to_grayscale(self):
        """Преобразование изображения в оттенки серого."""
        if self.current_image is None:
            messagebox.showerror(
                "Ошибка",
                "Сначала загрузите изображение"
            )
            return

        # Преобразование в градации серого
        gray = cv2.cvtColor(  # pylint: disable=no-member
            self.current_image,
            cv2.COLOR_RGB2GRAY  # pylint: disable=no-member
        )
        # Обратная конвертация в RGB для отображения
        self.current_image = cv2.cvtColor(  # pylint: disable=no-member
            gray,
            cv2.COLOR_GRAY2RGB  # pylint: disable=no-member
        )
        self.show_image()
        self.status_var.set("Изображение преобразовано в оттенки серого")

    def draw_line_dialog(self):
        """Диалог для задания параметров линии."""
        if self.current_image is None:
            messagebox.showerror(
                "Ошибка",
                "Сначала загрузите изображение"
            )
            return

        # Создание диалогового окна
        dialog = tk.Toplevel(self)
        dialog.title("Параметры линии")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Получение размеров изображения
        width = self.current_image.shape[1]
        height = self.current_image.shape[0]

        # Поля ввода координат и толщины
        ttk.Label(
            dialog,
            text=f"X начальной точки (0-{width - 1})"
        ).grid(row=0, column=0)
        x1_entry = ttk.Entry(dialog, width=8)
        x1_entry.grid(row=0, column=1)

        ttk.Label(
            dialog,
            text=f"Y начальной точки (0-{height - 1})"
        ).grid(row=1, column=0)
        y1_entry = ttk.Entry(dialog, width=8)
        y1_entry.grid(row=1, column=1)

        ttk.Label(
            dialog,
            text=f"X конечной точки (0-{width - 1})"
        ).grid(row=2, column=0)
        x2_entry = ttk.Entry(dialog, width=8)
        x2_entry.grid(row=2, column=1)

        ttk.Label(
            dialog,
            text=f"Y конечной точки (0-{height - 1})"
        ).grid(row=3, column=0)
        y2_entry = ttk.Entry(dialog, width=8)
        y2_entry.grid(row=3, column=1)

        ttk.Label(
            dialog,
            text="Толщина линии (1-20)"
        ).grid(row=4, column=0)
        thickness_entry = ttk.Entry(dialog, width=8)
        thickness_entry.grid(row=4, column=1)

        def apply():
            """Обработка нажатия кнопки Нарисовать."""
            try:
                # Получение параметров линии
                x1 = int(x1_entry.get())
                y1 = int(y1_entry.get())
                x2 = int(x2_entry.get())
                y2 = int(y2_entry.get())
                thickness = int(thickness_entry.get())

                # Проверка корректности параметров
                if not (0 <= x1 < width and 0 <= y1 < height and
                        0 <= x2 < width and 0 <= y2 < height and
                        1 <= thickness <= 20):
                    raise ValueError

                self.draw_line(x1, y1, x2, y2, thickness)
                dialog.destroy()
            except ValueError:
                messagebox.showerror(
                    "Ошибка",
                    "Некорректные параметры линии"
                )

        ttk.Button(
            dialog,
            text="Нарисовать",
            command=apply
        ).grid(row=5, columnspan=2)

    def draw_line(self, start_x, start_y, end_x, end_y, thickness):
        """
        Рисование линии на изображении.

        Аргументы:
            start_x (int): Начальная координата X
            start_y (int): Начальная координата Y
            end_x (int): Конечная координата X
            end_y (int): Конечная координата Y
            thickness (int): Толщина линии
        """
        img = self.current_image.copy()
        # Рисование зеленой линии
        cv2.line(  # pylint: disable=no-member
            img,
            (start_x, start_y),
            (end_x, end_y),
            (0, 255, 0),
            thickness
        )
        self.current_image = img
        self.show_image()
        self.status_var.set(
            f"Нарисована линия: ({start_x},{start_y})-({end_x},{end_y})"
        )


if __name__ == "__main__":
    app = ImageProcessingApp()
    app.mainloop()
