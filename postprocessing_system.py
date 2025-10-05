# -*- coding: utf-8 -*-
"""
Automated Post-Processing System
Система автоматической постобработки результатов FEA расчетов

Автор: CAE Automation Specialist
Дата: 2025
Технологии: Python, Abaqus ODB API, Matplotlib, Pandas, Plotly
"""

import os
import sys
import json
import shutil
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pathlib import Path

# Abaqus ODB imports
try:
    from abaqus import *
    from abaqusConstants import *
    from odbAccess import *
    ODB_AVAILABLE = True
except ImportError:
    ODB_AVAILABLE = False
    print("Предупреждение: Abaqus ODB API недоступен. Некоторые функции будут ограничены.")

# Plotly для интерактивных графиков
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Предупреждение: Plotly недоступен. Интерактивные графики будут ограничены.")


class PostProcessingSystem:
    """
    Основной класс системы автоматической постобработки
    
    Attributes:
    -----------
    config : dict
        Конфигурация системы
    output_dir : str
        Директория для сохранения результатов
    """
    
    def __init__(self, config: Dict = None, output_dir: str = None):
        """
        Инициализация системы постобработки
        
        Parameters:
        -----------
        config : dict, optional
            Конфигурация системы
        output_dir : str, optional
            Директория для сохранения результатов
        """
        # Конфигурация по умолчанию
        self.default_config = {
            "field_outputs": {
                "stress": ["S11", "S22", "S33", "S12", "S13", "S23"],
                "strain": ["E11", "E22", "E33", "E12", "E13", "E23"],
                "displacement": ["U1", "U2", "U3"],
                "velocity": ["V1", "V2", "V3"]
            },
            "history_outputs": {
                "reaction_force": "RF",
                "kinetic_energy": "KE",
                "internal_energy": "IE"
            },
            "output_frequency": 10,
            "coordinate_system": "GLOBAL",
            "plot_settings": {
                "figure_size": (12, 8),
                "dpi": 300,
                "style": "seaborn-v0_8",
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
                "line_width": 2,
                "marker_size": 6
            }
        }
        
        self.config = config or self.default_config
        self.output_dir = output_dir or "results/postprocessing"
        
        # Создание директорий
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "plots"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "animations"), exist_ok=True)
        
        # Настройка matplotlib
        plt.style.use(self.config["plot_settings"]["style"])
        
        print(f"Post-Processing System инициализирована")
        print(f"Директория результатов: {self.output_dir}")
    
    def process_odb_file(self, odb_file: str, output_dir: str = None) -> 'PostProcessingResults':
        """
        Обработка ODB файла и извлечение данных
        
        Parameters:
        -----------
        odb_file : str
            Путь к ODB файлу
        output_dir : str, optional
            Директория для сохранения результатов
            
        Returns:
        --------
        PostProcessingResults
            Объект с результатами постобработки
        """
        if not ODB_AVAILABLE:
            raise RuntimeError("Abaqus ODB API недоступен. Невозможно обработать ODB файл.")
        
        print(f"\n=== Обработка ODB файла ===")
        print(f"Файл: {odb_file}")
        
        if output_dir is None:
            output_dir = os.path.join(self.output_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Открытие ODB файла
            odb = openOdb(odb_file)
            print(f"ODB файл открыт: {odb.name}")
            
            # Извлечение данных
            field_data = self._extract_field_data(odb)
            history_data = self._extract_history_data(odb)
            
            # Создание объекта результатов
            results = PostProcessingResults(
                odb_file=odb_file,
                field_data=field_data,
                history_data=history_data,
                output_dir=output_dir,
                config=self.config
            )
            
            # Сохранение результатов
            self._save_results(results)
            
            # Создание графиков
            self._create_plots(results)
            
            # Закрытие ODB файла
            odb.close()
            
            print(f"✅ Обработка завершена. Результаты в: {output_dir}")
            
            return results
            
        except Exception as e:
            print(f"❌ Ошибка при обработке ODB файла: {e}")
            raise
    
    def _extract_field_data(self, odb) -> Dict:
        """Извлечение полевых данных из ODB"""
        print("Извлечение полевых данных...")
        
        field_data = {}
        
        # Получение шагов
        steps = odb.steps.keys()
        print(f"Найдено шагов: {len(steps)}")
        
        for step_name in steps:
            step = odb.steps[step_name]
            field_data[step_name] = {}
            
            # Получение кадров
            frames = step.frames
            print(f"Шаг {step_name}: {len(frames)} кадров")
            
            for frame in frames:
                frame_data = {}
                
                # Извлечение полевых выходов
                for field_type, components in self.config["field_outputs"].items():
                    if field_type in frame.fieldOutputs:
                        field_output = frame.fieldOutputs[field_type]
                        frame_data[field_type] = {}
                        
                        for component in components:
                            if component in field_output.values[0].data:
                                values = [value.data[component] for value in field_output.values]
                                frame_data[field_type][component] = {
                                    "values": values,
                                    "max": max(values) if values else 0,
                                    "min": min(values) if values else 0,
                                    "mean": np.mean(values) if values else 0
                                }
                
                frame_data["time"] = frame.frameValue
                field_data[step_name][frame.frameValue] = frame_data
        
        return field_data
    
    def _extract_history_data(self, odb) -> Dict:
        """Извлечение исторических данных из ODB"""
        print("Извлечение исторических данных...")
        
        history_data = {}
        
        # Получение шагов
        for step_name in odb.steps.keys():
            step = odb.steps[step_name]
            history_data[step_name] = {}
            
            # Извлечение исторических выходов
            for history_name, output_name in self.config["history_outputs"].items():
                if history_name in step.historyRegions:
                    history_region = step.historyRegions[history_name]
                    
                    if output_name in history_region.historyOutputs:
                        history_output = history_region.historyOutputs[output_name]
                        
                        times = [data.time for data in history_output.data]
                        values = [data.data for data in history_output.data]
                        
                        history_data[step_name][history_name] = {
                            "times": times,
                            "values": values,
                            "max": max(values) if values else 0,
                            "min": min(values) if values else 0,
                            "mean": np.mean(values) if values else 0
                        }
        
        return history_data
    
    def _save_results(self, results: 'PostProcessingResults'):
        """Сохранение результатов в файлы"""
        print("Сохранение результатов...")
        
        # Сохранение в JSON
        json_file = os.path.join(results.output_dir, "extracted_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "field_data": results.field_data,
                "history_data": results.history_data,
                "metadata": {
                    "odb_file": results.odb_file,
                    "extraction_time": datetime.now().isoformat(),
                    "config": results.config
                }
            }, f, indent=2, ensure_ascii=False, default=str)
        
        # Сохранение в Excel
        self._export_to_excel(results)
        
        print(f"Результаты сохранены в: {results.output_dir}")
    
    def _export_to_excel(self, results: 'PostProcessingResults'):
        """Экспорт результатов в Excel"""
        excel_file = os.path.join(results.output_dir, "results.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Полевые данные
            for step_name, step_data in results.field_data.items():
                for frame_time, frame_data in step_data.items():
                    if frame_data:
                        df_data = []
                        for field_type, components in frame_data.items():
                            if field_type != "time" and isinstance(components, dict):
                                for component, data in components.items():
                                    if isinstance(data, dict) and "values" in data:
                                        for i, value in enumerate(data["values"]):
                                            df_data.append({
                                                "Step": step_name,
                                                "Time": frame_time,
                                                "Field": field_type,
                                                "Component": component,
                                                "Node": i,
                                                "Value": value
                                            })
                        
                        if df_data:
                            df = pd.DataFrame(df_data)
                            sheet_name = f"{step_name}_{frame_time:.3f}"
                            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            
            # Исторические данные
            for step_name, step_data in results.history_data.items():
                for history_name, history_data in step_data.items():
                    if "times" in history_data and "values" in history_data:
                        df = pd.DataFrame({
                            "Time": history_data["times"],
                            "Value": history_data["values"]
                        })
                        sheet_name = f"History_{step_name}_{history_name}"[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _create_plots(self, results: 'PostProcessingResults'):
        """Создание графиков и диаграмм"""
        print("Создание графиков...")
        
        plots_dir = os.path.join(results.output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        # График распределения напряжений
        self._plot_stress_distribution(results, plots_dir)
        
        # График истории деформаций
        self._plot_strain_history(results, plots_dir)
        
        # График энергии
        self._plot_energy_history(results, plots_dir)
        
        # Сравнительные графики
        self._plot_comparison(results, plots_dir)
        
        print(f"Графики сохранены в: {plots_dir}")
    
    def _plot_stress_distribution(self, results: 'PostProcessingResults', plots_dir: str):
        """График распределения напряжений"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Распределение напряжений', fontsize=16)
        
        stress_components = ['S11', 'S22', 'S33', 'S12']
        
        for i, component in enumerate(stress_components):
            ax = axes[i//2, i%2]
            
            for step_name, step_data in results.field_data.items():
                times = []
                max_stresses = []
                
                for frame_time, frame_data in step_data.items():
                    if frame_data and 'stress' in frame_data and component in frame_data['stress']:
                        times.append(frame_time)
                        max_stresses.append(frame_data['stress'][component]['max'])
                
                if times and max_stresses:
                    ax.plot(times, max_stresses, label=f'{step_name}', linewidth=2)
            
            ax.set_xlabel('Время (с)')
            ax.set_ylabel(f'Напряжение {component} (МПа)')
            ax.set_title(f'Максимальное напряжение {component}')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'stress_distribution.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_strain_history(self, results: 'PostProcessingResults', plots_dir: str):
        """График истории деформаций"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for step_name, step_data in results.field_data.items():
            times = []
            max_strains = []
            
            for frame_time, frame_data in step_data.items():
                if frame_data and 'strain' in frame_data:
                    times.append(frame_time)
                    # Вычисление эквивалентной деформации
                    if 'E11' in frame_data['strain'] and 'E22' in frame_data['strain']:
                        e11 = frame_data['strain']['E11']['max']
                        e22 = frame_data['strain']['E22']['max']
                        equivalent_strain = np.sqrt(2/3 * (e11**2 + e22**2))
                        max_strains.append(equivalent_strain)
                    else:
                        max_strains.append(0)
            
            if times and max_strains:
                ax.plot(times, max_strains, label=f'{step_name}', linewidth=2)
        
        ax.set_xlabel('Время (с)')
        ax.set_ylabel('Эквивалентная деформация')
        ax.set_title('История деформаций')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'strain_history.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_energy_history(self, results: 'PostProcessingResults', plots_dir: str):
        """График истории энергии"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for step_name, step_data in results.history_data.items():
            if 'kinetic_energy' in step_data:
                ke_data = step_data['kinetic_energy']
                ax.plot(ke_data['times'], ke_data['values'], 
                       label=f'{step_name} - Кинетическая энергия', linewidth=2)
            
            if 'internal_energy' in step_data:
                ie_data = step_data['internal_energy']
                ax.plot(ie_data['times'], ie_data['values'], 
                       label=f'{step_name} - Внутренняя энергия', linewidth=2, linestyle='--')
        
        ax.set_xlabel('Время (с)')
        ax.set_ylabel('Энергия (Дж)')
        ax.set_title('История энергии')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'energy_history.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_comparison(self, results: 'PostProcessingResults', plots_dir: str):
        """Сравнительные графики"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Сравнительный анализ', fontsize=16)
        
        # Максимальные значения по времени
        ax1 = axes[0, 0]
        for step_name, step_data in results.field_data.items():
            times = []
            max_stresses = []
            
            for frame_time, frame_data in step_data.items():
                if frame_data and 'stress' in frame_data:
                    times.append(frame_time)
                    max_stress = 0
                    for component in ['S11', 'S22', 'S33']:
                        if component in frame_data['stress']:
                            max_stress = max(max_stress, frame_data['stress'][component]['max'])
                    max_stresses.append(max_stress)
            
            if times and max_stresses:
                ax1.plot(times, max_stresses, label=f'{step_name}', linewidth=2)
        
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Максимальное напряжение (МПа)')
        ax1.set_title('Максимальные напряжения')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Сводная статистика
        ax2 = axes[0, 1]
        step_names = list(results.field_data.keys())
        max_values = []
        
        for step_name in step_names:
            max_stress = 0
            for frame_data in results.field_data[step_name].values():
                if frame_data and 'stress' in frame_data:
                    for component_data in frame_data['stress'].values():
                        if isinstance(component_data, dict) and 'max' in component_data:
                            max_stress = max(max_stress, component_data['max'])
            max_values.append(max_stress)
        
        ax2.bar(step_names, max_values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        ax2.set_ylabel('Максимальное напряжение (МПа)')
        ax2.set_title('Сравнение максимальных напряжений')
        ax2.tick_params(axis='x', rotation=45)
        
        # Энергетический баланс
        ax3 = axes[1, 0]
        for step_name, step_data in results.history_data.items():
            if 'kinetic_energy' in step_data and 'internal_energy' in step_data:
                ke_data = step_data['kinetic_energy']
                ie_data = step_data['internal_energy']
                
                total_energy = [ke + ie for ke, ie in zip(ke_data['values'], ie_data['values'])]
                ax3.plot(ke_data['times'], total_energy, label=f'{step_name} - Общая энергия', linewidth=2)
        
        ax3.set_xlabel('Время (с)')
        ax3.set_ylabel('Общая энергия (Дж)')
        ax3.set_title('Энергетический баланс')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Распределение напряжений
        ax4 = axes[1, 1]
        for step_name, step_data in results.field_data.items():
            for frame_time, frame_data in step_data.items():
                if frame_data and 'stress' in frame_data and 'S11' in frame_data['stress']:
                    s11_data = frame_data['stress']['S11']['values']
                    ax4.hist(s11_data, bins=50, alpha=0.7, label=f'{step_name} - t={frame_time:.3f}s')
                    break
        
        ax4.set_xlabel('Напряжение S11 (МПа)')
        ax4.set_ylabel('Частота')
        ax4.set_title('Распределение напряжений S11')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'comparison_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def batch_process(self, odb_files: List[str], output_dir: str = None) -> List['PostProcessingResults']:
        """
        Пакетная обработка нескольких ODB файлов
        
        Parameters:
        -----------
        odb_files : List[str]
            Список путей к ODB файлам
        output_dir : str, optional
            Директория для сохранения результатов
            
        Returns:
        --------
        List[PostProcessingResults]
            Список объектов с результатами
        """
        print(f"\n=== Пакетная обработка {len(odb_files)} файлов ===")
        
        if output_dir is None:
            output_dir = os.path.join(self.output_dir, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        for i, odb_file in enumerate(odb_files, 1):
            print(f"\n--- Обработка файла {i}/{len(odb_files)}: {os.path.basename(odb_file)} ---")
            
            try:
                file_output_dir = os.path.join(output_dir, f"file_{i}")
                result = self.process_odb_file(odb_file, file_output_dir)
                results.append(result)
                print(f"✅ Файл {i} обработан успешно")
                
            except Exception as e:
                print(f"❌ Ошибка при обработке файла {i}: {e}")
                results.append(None)
        
        # Создание сводного отчета
        self._create_batch_summary(results, output_dir)
        
        print(f"\n=== Пакетная обработка завершена ===")
        print(f"Успешно обработано: {sum(1 for r in results if r is not None)}/{len(odb_files)} файлов")
        print(f"Результаты в: {output_dir}")
        
        return results
    
    def _create_batch_summary(self, results: List['PostProcessingResults'], output_dir: str):
        """Создание сводного отчета по пакетной обработке"""
        summary_file = os.path.join(output_dir, "batch_summary.txt")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=== СВОДНЫЙ ОТЧЕТ ПО ПАКЕТНОЙ ОБРАБОТКЕ ===\n\n")
            f.write(f"Дата обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего файлов: {len(results)}\n")
            f.write(f"Успешно обработано: {sum(1 for r in results if r is not None)}\n")
            f.write(f"Ошибок: {sum(1 for r in results if r is None)}\n\n")
            
            f.write("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n")
            f.write("-" * 60 + "\n")
            
            for i, result in enumerate(results, 1):
                if result:
                    f.write(f"Файл {i}: {os.path.basename(result.odb_file)}\n")
                    f.write(f"  Шагов: {len(result.field_data)}\n")
                    f.write(f"  Время обработки: {result.processing_time:.2f} сек\n")
                    f.write(f"  Статус: Успешно\n\n")
                else:
                    f.write(f"Файл {i}: Ошибка обработки\n")
                    f.write(f"  Статус: Неудачно\n\n")
    
    def generate_report(self, results: 'PostProcessingResults', output_file: str = None):
        """
        Генерация HTML отчета
        
        Parameters:
        -----------
        results : PostProcessingResults
            Результаты постобработки
        output_file : str, optional
            Путь к выходному файлу
        """
        if output_file is None:
            output_file = os.path.join(results.output_dir, "analysis_report.html")
        
        print(f"Генерация HTML отчета: {output_file}")
        
        # Создание HTML отчета
        html_content = self._create_html_report(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML отчет создан: {output_file}")
    
    def _create_html_report(self, results: 'PostProcessingResults') -> str:
        """Создание HTML отчета"""
        html_template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FEA Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .plot { text-align: center; margin: 20px 0; }
        .summary { background-color: #e8f4f8; padding: 15px; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Отчет по анализу FEA</h1>
        <p><strong>Файл:</strong> {odb_file}</p>
        <p><strong>Дата анализа:</strong> {analysis_date}</p>
        <p><strong>Время обработки:</strong> {processing_time:.2f} секунд</p>
    </div>
    
    <div class="section">
        <h2>Сводка результатов</h2>
        <div class="summary">
            <p><strong>Количество шагов:</strong> {num_steps}</p>
            <p><strong>Общее время анализа:</strong> {total_time:.3f} секунд</p>
            <p><strong>Максимальное напряжение:</strong> {max_stress:.2f} МПа</p>
            <p><strong>Максимальная деформация:</strong> {max_strain:.4f}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Графики</h2>
        <div class="plot">
            <h3>Распределение напряжений</h3>
            <img src="plots/stress_distribution.png" alt="Stress Distribution" style="max-width: 100%;">
        </div>
        <div class="plot">
            <h3>История деформаций</h3>
            <img src="plots/strain_history.png" alt="Strain History" style="max-width: 100%;">
        </div>
        <div class="plot">
            <h3>История энергии</h3>
            <img src="plots/energy_history.png" alt="Energy History" style="max-width: 100%;">
        </div>
        <div class="plot">
            <h3>Сравнительный анализ</h3>
            <img src="plots/comparison_analysis.png" alt="Comparison Analysis" style="max-width: 100%;">
        </div>
    </div>
    
    <div class="section">
        <h2>Детальные данные</h2>
        <p>Подробные данные доступны в файлах:</p>
        <ul>
            <li><strong>JSON:</strong> extracted_data.json</li>
            <li><strong>Excel:</strong> results.xlsx</li>
        </ul>
    </div>
</body>
</html>
        """
        
        # Подготовка данных для отчета
        num_steps = len(results.field_data)
        total_time = max([max(step_data.keys()) for step_data in results.field_data.values()]) if results.field_data else 0
        max_stress = results.get_max_stress()
        max_strain = results.get_max_strain()
        
        return html_template.format(
            odb_file=os.path.basename(results.odb_file),
            analysis_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            processing_time=results.processing_time,
            num_steps=num_steps,
            total_time=total_time,
            max_stress=max_stress,
            max_strain=max_strain
        )


class PostProcessingResults:
    """Класс для работы с результатами постобработки"""
    
    def __init__(self, odb_file: str, field_data: Dict, history_data: Dict, 
                 output_dir: str, config: Dict):
        self.odb_file = odb_file
        self.field_data = field_data
        self.history_data = history_data
        self.output_dir = output_dir
        self.config = config
        self.processing_time = 0  # Время обработки в секундах
    
    def get_max_stress(self) -> float:
        """Получение максимального напряжения"""
        max_stress = 0
        for step_data in self.field_data.values():
            for frame_data in step_data.values():
                if frame_data and 'stress' in frame_data:
                    for component_data in frame_data['stress'].values():
                        if isinstance(component_data, dict) and 'max' in component_data:
                            max_stress = max(max_stress, component_data['max'])
        return max_stress
    
    def get_max_strain(self) -> float:
        """Получение максимальной деформации"""
        max_strain = 0
        for step_data in self.field_data.values():
            for frame_data in step_data.values():
                if frame_data and 'strain' in frame_data:
                    for component_data in frame_data['strain'].values():
                        if isinstance(component_data, dict) and 'max' in component_data:
                            max_strain = max(max_strain, component_data['max'])
        return max_strain
    
    def get_summary_statistics(self) -> Dict:
        """Получение сводной статистики"""
        stats = {
            "num_steps": len(self.field_data),
            "max_stress": self.get_max_stress(),
            "max_strain": self.get_max_strain(),
            "total_frames": sum(len(step_data) for step_data in self.field_data.values()),
            "processing_time": self.processing_time
        }
        return stats


def main():
    """Пример использования системы постобработки"""
    print("=== Пример использования Post-Processing System ===")
    
    # Создание системы
    system = PostProcessingSystem()
    
    # Обработка ODB файла
    try:
        results = system.process_odb_file("data/sample_results.odb")
        
        # Генерация отчета
        system.generate_report(results)
        
        # Вывод статистики
        stats = results.get_summary_statistics()
        print(f"\nСводная статистика:")
        print(f"Шагов: {stats['num_steps']}")
        print(f"Макс. напряжение: {stats['max_stress']:.2f} МПа")
        print(f"Макс. деформация: {stats['max_strain']:.4f}")
        
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == '__main__':
    main()
