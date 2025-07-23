# Импортируем необходимые библиотеки
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CryptoEDAApp:
    def __init__(self, root):
        # Инициализация главного окна
        self.root = root
        self.root.title("Аналитика криптовалют")
        self.root.geometry("1200x800")
        self.root.configure(bg="#e6f3fa")

        # Инициализация переменных
        self.df = None
        self.filtered_df = None
        self.sort_column_name = None
        self.sort_ascending = True
        self.table_cache = []  # Кэш для данных таблицы

        # Создание основного фрейма
        self.main_frame = ttk.Frame(self.root, padding="10", style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Настройка стилей
        self.setup_styles()

        # Создание элементов интерфейса
        self.create_widgets()

    def setup_styles(self):
        # Настройка стилей для компактного и современного вида
        style = ttk.Style()
        style.theme_use("clam")

        # Стиль основного фрейма
        style.configure("Main.TFrame", background="#e6f3fa")

        # Стиль кнопок (компактные)
        style.configure("TButton",
                       font=("Helvetica", 9, "bold"),
                       padding=5,
                       background="#4CAF50",
                       foreground="#ffffff")
        style.map("TButton",
                 background=[("active", "#45a049")])

        # Стиль меток (компактные)
        style.configure("TLabel",
                       font=("Helvetica", 9),
                       background="#e6f3fa",
                       foreground="#333333")

        # Стиль Combobox
        style.configure("TCombobox",
                       font=("Helvetica", 9),
                       padding=4)

        # Стиль для LabelFrame
        style.configure("TLabelFrame",
                       background="#e6f3fa",
                       foreground="#333333",
                       font=("Helvetica", 10, "bold"))

        # Стиль для Treeview
        style.configure("Treeview",
                       font=("Helvetica", 9),
                       rowheight=22,
                       background="#ffffff",
                       foreground="#333333",
                       fieldbackground="#ffffff")
        style.configure("Treeview.Heading",
                       font=("Helvetica", 10, "bold"),
                       background="#4CAF50",
                       foreground="#ffffff")
        style.map("Treeview.Heading",
                 background=[("active", "#45a049")])

    def create_widgets(self):
        # Кнопка загрузки CSV
        self.load_button = ttk.Button(self.main_frame, text="Загрузить CSV", command=self.load_csv)
        self.load_button.grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky="ew")
        self.add_tooltip(self.load_button, "Выберите CSV-файл с данными")

        # Метка для информации о датасете
        self.info_label = ttk.Label(self.main_frame, text="Информация о датасете: не загружен")
        self.info_label.grid(row=1, column=0, columnspan=4, pady=5, padx=5, sticky="w")

        # Фрейм для фильтров
        filter_frame = ttk.LabelFrame(self.main_frame, text="Фильтры", padding="5")
        filter_frame.grid(row=2, column=0, columnspan=4, pady=5, padx=5, sticky="ew")

        # Выбор валюты
        ttk.Label(filter_frame, text="Валюта:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.currency_var = tk.StringVar()
        self.currency_combo = ttk.Combobox(filter_frame, textvariable=self.currency_var, state="readonly", width=15)
        self.currency_combo.grid(row=0, column=1, padx=5, pady=2)
        self.currency_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        self.add_tooltip(self.currency_combo, "Выберите валюту для фильтрации")

        # Выбор года
        ttk.Label(filter_frame, text="Год:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(filter_frame, textvariable=self.year_var, state="readonly", width=15)
        self.year_combo.grid(row=0, column=3, padx=5, pady=2)
        self.year_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        self.add_tooltip(self.year_combo, "Выберите год для фильтрации")

        # Кнопка для вывода рекомендаций
        self.recommend_button = ttk.Button(self.main_frame, text="Рекомендации", command=self.show_recommendations)
        self.recommend_button.grid(row=3, column=0, pady=5, padx=5, sticky="ew")
        self.add_tooltip(self.recommend_button, "Показать рекомендации для бизнеса")

        # Кнопка для экспорта данных
        self.export_button = ttk.Button(self.main_frame, text="Экспорт в CSV", command=self.export_to_csv)
        self.export_button.grid(row=3, column=1, pady=5, padx=5, sticky="ew")
        self.add_tooltip(self.export_button, "Сохранить отфильтрованные данные в CSV")

        # Таблица для отображения данных
        self.tree_frame = ttk.LabelFrame(self.main_frame, text="Данные", padding="5")
        self.tree_frame.grid(row=4, column=0, columnspan=4, pady=5, padx=5, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=5)

        self.tree = ttk.Treeview(self.tree_frame, show="headings", height=25)
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)

        # Привязка сортировки к заголовкам столбцов
        self.tree.bind("<Button-1>", self.handle_click)

        # График для визуализации цен
        self.plot_frame = ttk.LabelFrame(self.main_frame, text="График цен", padding="5")
        self.plot_frame.grid(row=5, column=0, columnspan=4, pady=5, padx=5, sticky="nsew")
        self.main_frame.rowconfigure(5, weight=1)
        self.fig, self.ax = plt.subplots(figsize=(6, 2.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.plot_frame.columnconfigure(0, weight=1)
        self.plot_frame.rowconfigure(0, weight=1)

    def add_tooltip(self, widget, text):
        # Добавление всплывающих подсказок
        def show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Helvetica", 8))
            label.pack()

        def hide_tooltip(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def handle_click(self, event):
        # Обработка клика по заголовку столбца
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            column_name = self.tree["columns"][int(column[1:]) - 1]
            self.sort_column(column_name)

    def sort_column(self, column):
        # Сортировка данных по столбцу
        if self.filtered_df is None:
            return

        if self.sort_column_name == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_ascending = True
            self.sort_column_name = column

        self.filtered_df = self.filtered_df.sort_values(by=column, ascending=self.sort_ascending)
        self.update_table()

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        arrow = " ↑" if self.sort_ascending else " ↓"
        self.tree.heading(column, text=column + arrow)

    def load_csv(self):
        # Загрузка CSV-файла
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path)
            # Удаление дубликатов и создание индекса
            self.df = self.df.drop_duplicates()
            self.df.set_index(['currency_name', 'date'], inplace=True)
            self.filtered_df = self.df

            required_columns = ["date", "price", "currency_name"]
            if not all(col in self.df.columns for col in required_columns if col != 'date' and col != 'currency_name'):
                messagebox.showerror("Ошибка", "CSV-файл должен содержать столбцы: date, price, currency_name")
                return

            self.df.index = self.df.index.set_levels([self.df.index.levels[0], pd.to_datetime(self.df.index.levels[1])])
            info = f"Размер датасета: {self.df.shape[0]} строк, {self.df.shape[1]} столбцов\n"
            info += f"Диапазон дат: {self.df.index.get_level_values('date').min().strftime('%Y-%m-%d')} - {self.df.index.get_level_values('date').max().strftime('%Y-%m-%d')}\n"
            info += f"Валюты: {', '.join(self.df.index.get_level_values('currency_name').unique())}"
            self.info_label.config(text=info)

            self.currency_combo["values"] = ["Все"] + list(self.df.index.get_level_values('currency_name').unique())
            self.currency_var.set("Все")
            years = sorted(self.df.index.get_level_values('date').year.unique())
            self.year_combo["values"] = ["Все"] + list(map(str, years))
            self.year_var.set("Все")

            self.sort_column_name = None
            self.sort_ascending = True

            self.update_table()
            self.update_plot()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def apply_filters(self, event=None):
        # Применение фильтров
        if self.df is None:
            return

        self.filtered_df = self.df

        currency = self.currency_var.get()
        year = self.year_var.get()

        if currency != "Все":
            self.filtered_df = self.filtered_df.loc[self.filtered_df.index.get_level_values('currency_name') == currency]
        if year != "Все":
            self.filtered_df = self.filtered_df.loc[self.filtered_df.index.get_level_values('date').year == int(year)]

        self.sort_column_name = None
        self.sort_ascending = True

        self.update_table()
        self.update_plot()

    def update_table(self):
        # Обновление таблицы с кэшированием
        self.tree.delete(*self.tree.get_children())
        columns = ["date", "price", "volume", "change%", "currency_name", "daily_volatility"]
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160, anchor="center")

        self.table_cache = []
        for (currency, date), row in self.filtered_df.iterrows():
            values = [date.strftime("%Y-%m-%d")] + [row[col] for col in columns[1:-1] if col in row] + [currency] + ([row["daily_volatility"]] if "daily_volatility" in row else ["N/A"])
            self.table_cache.append(values)

        for values in self.table_cache:
            self.tree.insert("", "end", values=values)

    def update_plot(self):
        # Обновление графика цен
        self.ax.clear()
        if self.filtered_df is not None and not self.filtered_df.empty:
            for currency in self.filtered_df.index.get_level_values('currency_name').unique():
                df_currency = self.filtered_df.loc[currency]
                self.ax.plot(df_currency.index.get_level_values('date'), df_currency["price"], label=currency, linewidth=1.5)
            self.ax.set_title("Динамика цен", fontsize=10, pad=5)
            self.ax.set_xlabel("Дата", fontsize=8)
            self.ax.set_ylabel("Цена (USD)", fontsize=8)
            self.ax.legend(fontsize=8)
            self.ax.grid(True, linestyle="--", alpha=0.7)
            self.ax.set_facecolor("#f8f9fa")
            self.fig.patch.set_facecolor("#e6f3fa")
        self.canvas.draw_idle()

    def export_to_csv(self):
        # Экспорт отфильтрованных данных в CSV
        if self.filtered_df is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите датасет")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.filtered_df.reset_index().to_csv(file_path, index=False)
                messagebox.showinfo("Успех", "Данные успешно экспортированы")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать файл: {str(e)}")

    def show_recommendations(self):
        # Создание окна с рекомендациями
        if self.df is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите датасет")
            return

        recommendations_window = tk.Toplevel(self.root)
        recommendations_window.title("Рекомендации для бизнеса")
        recommendations_window.geometry("600x400")
        recommendations_window.configure(bg="#e6f3fa")

        text_frame = ttk.Frame(recommendations_window, style="Main.TFrame")
        text_frame.pack(padx=10, pady=10, fill="both", expand=True)

        text = tk.Text(text_frame, wrap="word", font=("Helvetica", 9), bg="#ffffff", fg="#333333")
        text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        recommendations = self.generate_recommendations()
        text.insert("end", recommendations)
        text.config(state="disabled")

    def generate_recommendations(self):
        # Генерация рекомендаций с анализом корреляции
        recommendations = "Рекомендации для бизнеса:\n\n"

        for currency in self.df.index.get_level_values('currency_name').unique():
            df_currency = self.df.loc[currency]
            mean_price = df_currency["price"].mean()
            max_volatility = df_currency["daily_volatility"].max() if "daily_volatility" in df_currency else 0
            mean_volume = df_currency["volume"].mean() if "volume" in df_currency else 0
            trend = "рост" if df_currency["price"].iloc[-1] > df_currency["price"].iloc[0] else "падение"

            correlation_text = ""
            if "volume" in df_currency.columns:
                correlation = df_currency[["price", "volume"]].corr().iloc[0, 1]
                correlation_text = f"- Корреляция цены и объема: {correlation:.2f}\n"
                if correlation > 0.5:
                    correlation_text += "  (Сильная положительная корреляция: рост цены связан с увеличением объема торгов)\n"
                elif correlation < -0.5:
                    correlation_text += "  (Сильная отрицательная корреляция: рост цены связан с уменьшением объема торгов)\n"
                else:
                    correlation_text += "  (Слабая корреляция: цена и объем торгов слабо связаны)\n"

            recommendations += f"Валюта: {currency}\n"
            recommendations += f"- Средняя цена: ${mean_price:.4f}\n"
            recommendations += f"- Максимальная волатильность: {max_volatility:.2f}%\n"
            recommendations += f"- Средний объем торгов: {mean_volume:.2f}\n"
            recommendations += f"- Тренд: {trend}\n"
            recommendations += correlation_text
            if max_volatility > 10:
                recommendations += f"- Высокая волатильность указывает на рискованные инвестиции. Рекомендуется осторожный подход.\n"
            else:
                recommendations += f"- Низкая волатильность делает {currency} более стабильной для долгосрочных вложений.\n"
            recommendations += "\n"

        recommendations += "Интересный факт: DAI стремится поддерживать стабильную цену около $1, что делает его подходящим для хеджирования рисков.\n"
        return recommendations

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoEDAApp(root)
    root.mainloop()