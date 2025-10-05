# -*- coding: utf-8 -*-
"""
Базовый пример использования Post-Processing System
Демонстрирует основные возможности системы постобработки
"""

import sys
import os

# Добавление пути к модулю
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postprocessing_system import PostProcessingSystem, PostProcessingResults


def basic_postprocessing_example():
    """Базовый пример постобработки"""
    print("=== Базовый пример Post-Processing System ===")
    
    # 1. Создание системы
    print("\n1. Создание системы постобработки...")
    
    config = {
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
        "coordinate_system": "GLOBAL"
    }
    
    system = PostProcessingSystem(
        config=config,
        output_dir="results/basic_postprocessing"
    )
    
    # 2. Обработка ODB файла
    print("\n2. Обработка ODB файла...")
    
    odb_file = "data/sample_results.odb"
    
    try:
        results = system.process_odb_file(odb_file)
        print("✅ ODB файл обработан успешно")
        
    except FileNotFoundError:
        print("⚠️ ODB файл не найден. Создание демонстрационных данных...")
        results = create_demo_results()
        
    except Exception as e:
        print(f"❌ Ошибка при обработке ODB файла: {e}")
        return
    
    # 3. Анализ результатов
    print("\n3. Анализ результатов...")
    
    stats = results.get_summary_statistics()
    
    print(f"Количество шагов: {stats['num_steps']}")
    print(f"Общее количество кадров: {stats['total_frames']}")
    print(f"Максимальное напряжение: {stats['max_stress']:.2f} МПа")
    print(f"Максимальная деформация: {stats['max_strain']:.4f}")
    print(f"Время обработки: {stats['processing_time']:.2f} секунд")
    
    # 4. Генерация отчета
    print("\n4. Генерация HTML отчета...")
    
    try:
        system.generate_report(results)
        print("✅ HTML отчет создан")
    except Exception as e:
        print(f"⚠️ Ошибка при создании отчета: {e}")
    
    # 5. Вывод детальной информации
    print("\n5. Детальная информация:")
    print("-" * 60)
    
    for step_name, step_data in results.field_data.items():
        print(f"Шаг: {step_name}")
        print(f"  Кадров: {len(step_data)}")
        
        # Анализ напряжений
        if step_data:
            first_frame = next(iter(step_data.values()))
            if first_frame and 'stress' in first_frame:
                stress_components = first_frame['stress'].keys()
                print(f"  Компоненты напряжений: {list(stress_components)}")
                
                # Максимальные значения по компонентам
                for component in ['S11', 'S22', 'S33']:
                    if component in first_frame['stress']:
                        max_val = first_frame['stress'][component]['max']
                        print(f"    {component}: {max_val:.2f} МПа")
    
    print("-" * 60)


def batch_processing_example():
    """Пример пакетной обработки"""
    print("\n=== Пакетная обработка ===")
    
    # Создание системы
    system = PostProcessingSystem(output_dir="results/batch_processing")
    
    # Список ODB файлов для обработки
    odb_files = [
        "data/job1.odb",
        "data/job2.odb", 
        "data/job3.odb"
    ]
    
    print(f"Обработка {len(odb_files)} файлов...")
    
    try:
        # Пакетная обработка
        batch_results = system.batch_process(odb_files)
        
        # Анализ результатов
        successful_results = [r for r in batch_results if r is not None]
        failed_count = len(batch_results) - len(successful_results)
        
        print(f"\nРезультаты пакетной обработки:")
        print(f"Успешно обработано: {len(successful_results)}")
        print(f"Ошибок: {failed_count}")
        
        if successful_results:
            # Сравнительный анализ
            print("\nСравнительный анализ:")
            print("-" * 40)
            
            for i, result in enumerate(successful_results, 1):
                stats = result.get_summary_statistics()
                print(f"Файл {i}: {os.path.basename(result.odb_file)}")
                print(f"  Макс. напряжение: {stats['max_stress']:.2f} МПа")
                print(f"  Макс. деформация: {stats['max_strain']:.4f}")
                print(f"  Шагов: {stats['num_steps']}")
                print()
        
    except Exception as e:
        print(f"❌ Ошибка при пакетной обработке: {e}")


def report_generation_example():
    """Пример генерации отчетов"""
    print("\n=== Генерация отчетов ===")
    
    # Создание системы
    system = PostProcessingSystem(output_dir="results/report_generation")
    
    # Создание демонстрационных результатов
    results = create_demo_results()
    
    # Генерация различных типов отчетов
    print("Генерация HTML отчета...")
    try:
        system.generate_report(results, "results/report_generation/analysis_report.html")
        print("✅ HTML отчет создан")
    except Exception as e:
        print(f"⚠️ Ошибка HTML отчета: {e}")
    
    # Создание сводного отчета
    print("Создание сводного отчета...")
    create_summary_report(results)


def create_demo_results():
    """Создание демонстрационных результатов для тестирования"""
    print("Создание демонстрационных данных...")
    
    import numpy as np
    from datetime import datetime
    
    # Демонстрационные полевые данные
    field_data = {
        "Step-1": {
            0.0: {
                "stress": {
                    "S11": {"values": [0, 0, 0], "max": 0, "min": 0, "mean": 0},
                    "S22": {"values": [0, 0, 0], "max": 0, "min": 0, "mean": 0},
                    "S33": {"values": [0, 0, 0], "max": 0, "min": 0, "mean": 0}
                },
                "strain": {
                    "E11": {"values": [0, 0, 0], "max": 0, "min": 0, "mean": 0},
                    "E22": {"values": [0, 0, 0], "max": 0, "min": 0, "mean": 0}
                },
                "time": 0.0
            },
            0.001: {
                "stress": {
                    "S11": {"values": [45.2, 67.8, 89.4], "max": 89.4, "min": 45.2, "mean": 67.5},
                    "S22": {"values": [23.1, 34.5, 45.7], "max": 45.7, "min": 23.1, "mean": 34.4},
                    "S33": {"values": [12.3, 18.7, 24.1], "max": 24.1, "min": 12.3, "mean": 18.4}
                },
                "strain": {
                    "E11": {"values": [0.002, 0.003, 0.004], "max": 0.004, "min": 0.002, "mean": 0.003},
                    "E22": {"values": [0.001, 0.0015, 0.002], "max": 0.002, "min": 0.001, "mean": 0.0015}
                },
                "time": 0.001
            },
            0.002: {
                "stress": {
                    "S11": {"values": [78.9, 95.2, 112.6], "max": 112.6, "min": 78.9, "mean": 95.6},
                    "S22": {"values": [39.4, 47.6, 56.3], "max": 56.3, "min": 39.4, "mean": 47.8},
                    "S33": {"values": [20.1, 24.3, 28.7], "max": 28.7, "min": 20.1, "mean": 24.4}
                },
                "strain": {
                    "E11": {"values": [0.004, 0.005, 0.006], "max": 0.006, "min": 0.004, "mean": 0.005},
                    "E22": {"values": [0.002, 0.0025, 0.003], "max": 0.003, "min": 0.002, "mean": 0.0025}
                },
                "time": 0.002
            }
        }
    }
    
    # Демонстрационные исторические данные
    history_data = {
        "Step-1": {
            "kinetic_energy": {
                "times": [0.0, 0.001, 0.002],
                "values": [0.0, 1250.5, 2100.3],
                "max": 2100.3,
                "min": 0.0,
                "mean": 1116.9
            },
            "internal_energy": {
                "times": [0.0, 0.001, 0.002],
                "values": [0.0, 850.2, 1650.7],
                "max": 1650.7,
                "min": 0.0,
                "mean": 833.6
            }
        }
    }
    
    # Создание объекта результатов
    results = PostProcessingResults(
        odb_file="demo_results.odb",
        field_data=field_data,
        history_data=history_data,
        output_dir="results/demo",
        config={}
    )
    
    results.processing_time = 2.5  # Демонстрационное время обработки
    
    return results


def create_summary_report(results):
    """Создание сводного отчета"""
    report_file = "results/report_generation/summary_report.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=== СВОДНЫЙ ОТЧЕТ ПО ПОСТОБРАБОТКЕ ===\n\n")
        f.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Файл: {results.odb_file}\n")
        f.write(f"Время обработки: {results.processing_time:.2f} секунд\n\n")
        
        f.write("СТАТИСТИКА:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Количество шагов: {len(results.field_data)}\n")
        f.write(f"Общее количество кадров: {sum(len(step_data) for step_data in results.field_data.values())}\n")
        f.write(f"Максимальное напряжение: {results.get_max_stress():.2f} МПа\n")
        f.write(f"Максимальная деформация: {results.get_max_strain():.4f}\n\n")
        
        f.write("ДЕТАЛЬНЫЕ ДАННЫЕ:\n")
        f.write("-" * 30 + "\n")
        
        for step_name, step_data in results.field_data.items():
            f.write(f"Шаг: {step_name}\n")
            f.write(f"  Кадров: {len(step_data)}\n")
            
            if step_data:
                first_frame = next(iter(step_data.values()))
                if first_frame and 'stress' in first_frame:
                    f.write("  Компоненты напряжений:\n")
                    for component, data in first_frame['stress'].items():
                        f.write(f"    {component}: max={data['max']:.2f} МПа, min={data['min']:.2f} МПа\n")
            
            f.write("\n")
    
    print(f"✅ Сводный отчет создан: {report_file}")


def interactive_plots_example():
    """Пример создания интерактивных графиков"""
    print("\n=== Интерактивные графики ===")
    
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Создание демонстрационных данных
        results = create_demo_results()
        
        # Создание интерактивного графика
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Напряжения S11', 'Напряжения S22', 'Деформации E11', 'Энергия'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        # Данные для графиков
        times = [0.0, 0.001, 0.002]
        
        # График напряжений S11
        s11_max = [0, 89.4, 112.6]
        fig.add_trace(
            go.Scatter(x=times, y=s11_max, mode='lines+markers', name='S11 Max'),
            row=1, col=1
        )
        
        # График напряжений S22
        s22_max = [0, 45.7, 56.3]
        fig.add_trace(
            go.Scatter(x=times, y=s22_max, mode='lines+markers', name='S22 Max'),
            row=1, col=2
        )
        
        # График деформаций E11
        e11_max = [0, 0.004, 0.006]
        fig.add_trace(
            go.Scatter(x=times, y=e11_max, mode='lines+markers', name='E11 Max'),
            row=2, col=1
        )
        
        # График энергии
        ke_values = [0.0, 1250.5, 2100.3]
        ie_values = [0.0, 850.2, 1650.7]
        
        fig.add_trace(
            go.Scatter(x=times, y=ke_values, mode='lines+markers', name='Кинетическая энергия'),
            row=2, col=2, secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(x=times, y=ie_values, mode='lines+markers', name='Внутренняя энергия'),
            row=2, col=2, secondary_y=True
        )
        
        # Настройка осей
        fig.update_xaxes(title_text="Время (с)", row=2, col=1)
        fig.update_xaxes(title_text="Время (с)", row=2, col=2)
        fig.update_yaxes(title_text="Напряжение (МПа)", row=1, col=1)
        fig.update_yaxes(title_text="Напряжение (МПа)", row=1, col=2)
        fig.update_yaxes(title_text="Деформация", row=2, col=1)
        fig.update_yaxes(title_text="Кинетическая энергия (Дж)", row=2, col=2, secondary_y=False)
        fig.update_yaxes(title_text="Внутренняя энергия (Дж)", row=2, col=2, secondary_y=True)
        
        # Настройка макета
        fig.update_layout(
            title_text="Интерактивный анализ результатов FEA",
            showlegend=True,
            height=800
        )
        
        # Сохранение графика
        output_file = "results/interactive_plots/interactive_analysis.html"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        fig.write_html(output_file)
        
        print(f"✅ Интерактивный график создан: {output_file}")
        
    except ImportError:
        print("⚠️ Plotly не установлен. Невозможно создать интерактивные графики.")
    except Exception as e:
        print(f"❌ Ошибка при создании интерактивных графиков: {e}")


if __name__ == '__main__':
    """Запуск примеров"""
    
    print("🚀 Запуск примеров Post-Processing System")
    print("="*60)
    
    try:
        # Базовый пример
        basic_postprocessing_example()
        
        # Пакетная обработка
        batch_processing_example()
        
        # Генерация отчетов
        report_generation_example()
        
        # Интерактивные графики
        interactive_plots_example()
        
        print("\n🎉 Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()
