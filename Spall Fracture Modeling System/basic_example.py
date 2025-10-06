# -*- coding: utf-8 -*-
"""
Базовый пример использования Spall Fracture System
Демонстрирует основные возможности системы
"""

import sys
import os

# Добавление пути к модулю
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spall_fracture_system import SpallFractureSystem, SpallFractureResults


def basic_example():
    """Базовый пример использования системы"""
    print("=== Базовый пример Spall Fracture System ===")
    
    # 1. Создание системы
    print("\n1. Создание системы...")
    
    # Свойства материалов
    material_properties = {
        "materials": {
            "PMMA": {
                "elastic_modulus": 2.5e9,      # Модуль упругости (Па)
                "poisson_ratio": 0.38,         # Коэффициент Пуассона
                "density": 1180.0,              # Плотность (кг/м³)
                "yield_strength": 6e7,          # Предел текучести (Па)
                "strain_rate": 1e-5             # Скорость деформации
            }
        }
    }
    
    system = SpallFractureSystem(
        geometry_file="data/sample_geometry.stp",
        material_properties=material_properties,
        work_dir="results/basic_example",
        model_name="BasicSpallModel"
    )
    
    # 2. Параметры анализа
    print("\n2. Настройка параметров анализа...")
    
    analysis_params = {
        "time_period": 0.0003,          # Период анализа (с)
        "element_size": 0.0005,         # Размер элемента (м)
        "contact_friction": 0.1,        # Коэффициент трения
        "symmetry_planes": ["X", "Z"],  # Плоскости симметрии
        "output_frequency": 100         # Частота вывода результатов
    }
    
    # 3. Запуск анализа
    print("\n3. Запуск анализа...")
    
    velocities = [100, 150, 200, 250, 300]  # Скорости для анализа (м/с)
    
    try:
        results = system.run_analysis(
            velocities=velocities,
            analysis_params=analysis_params
        )
        
        print("✅ Анализ завершен успешно")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении анализа: {e}")
        return
    
    # 4. Анализ результатов
    print("\n4. Анализ результатов...")
    
    analysis = results.analyze()
    
    print(f"Всего скоростей: {analysis['total_velocities']}")
    print(f"Успешных расчетов: {analysis['successful_calculations']}")
    print(f"Неудачных расчетов: {analysis['failed_calculations']}")
    
    if analysis.get('critical_velocity'):
        print(f"Критическая скорость откола: {analysis['critical_velocity']:.1f} м/с")
    else:
        print("Критическая скорость откола не определена")
    
    # 5. Вывод детальных результатов
    print("\n5. Детальные результаты:")
    print("-" * 60)
    print(f"{'Скорость (м/с)':<12} {'Статус':<10} {'Напряжение (МПа)':<15} {'Откол':<8}")
    print("-" * 60)
    
    for result in results.results:
        status = "✅ Успех" if result['status'] == 'completed' else "❌ Ошибка"
        stress = f"{result.get('max_stress', 0):.1f}" if result['status'] == 'completed' else "N/A"
        fracture = "Да" if result.get('fracture_occurred', False) else "Нет"
        
        print(f"{result['velocity']:<12.1f} {status:<10} {stress:<15} {fracture:<8}")
    
    # 6. Построение графиков
    print("\n6. Построение графиков...")
    
    try:
        results.plot_velocity_analysis(
            save_path=os.path.join(results.output_dir, 'velocity_analysis.png')
        )
        print("✅ Графики построены и сохранены")
    except Exception as e:
        print(f"⚠️ Ошибка при построении графиков: {e}")
    
    # 7. Экспорт результатов
    print("\n7. Экспорт результатов...")
    
    try:
        results.export_to_excel(
            filename=os.path.join(results.output_dir, 'results.xlsx')
        )
        print("✅ Результаты экспортированы в Excel")
    except Exception as e:
        print(f"⚠️ Ошибка при экспорте в Excel: {e}")
    
    # 8. Сводка
    print("\n" + "="*60)
    print("СВОДКА ВЫПОЛНЕНИЯ")
    print("="*60)
    print(f"Директория результатов: {results.output_dir}")
    print(f"Количество скоростей: {len(velocities)}")
    print(f"Успешных расчетов: {analysis['successful_calculations']}")
    print(f"Время выполнения: ~{len(velocities) * 2} минут")
    print("="*60)


def parametric_study_example():
    """Пример параметрического исследования"""
    print("\n=== Параметрическое исследование ===")
    
    # Создание системы
    system = SpallFractureSystem(
        geometry_file="data/sample_geometry.stp",
        material_properties={
            "materials": {
                "PMMA": {
                    "elastic_modulus": 2.5e9,
                    "poisson_ratio": 0.38,
                    "density": 1180.0,
                    "yield_strength": 6e7,
                    "strain_rate": 1e-5
                }
            }
        }
    )
    
    # Параметрическое исследование скоростей
    velocities = [50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350]
    
    print(f"Исследование {len(velocities)} скоростей от {min(velocities)} до {max(velocities)} м/с")
    
    try:
        results = system.run_analysis(velocities)
        
        # Анализ критической скорости
        analysis = results.analyze()
        
        if analysis.get('critical_velocity'):
            print(f"Критическая скорость откола: {analysis['critical_velocity']:.1f} м/с")
            
            # Анализ зон
            no_fracture = analysis['no_fracture_velocities']
            fracture = analysis['fracture_velocities']
            
            print(f"Без откола: {no_fracture}")
            print(f"С отколом: {fracture}")
            
            # Построение детального графика
            results.plot_velocity_analysis(
                save_path=os.path.join(results.output_dir, 'parametric_study.png')
            )
            
        else:
            print("Критическая скорость не определена в заданном диапазоне")
            
    except Exception as e:
        print(f"Ошибка параметрического исследования: {e}")


def batch_processing_example():
    """Пример пакетной обработки"""
    print("\n=== Пакетная обработка ===")
    
    # Создание системы
    system = SpallFractureSystem(
        geometry_file="data/sample_geometry.stp",
        material_properties={
            "materials": {
                "PMMA": {
                    "elastic_modulus": 2.5e9,
                    "poisson_ratio": 0.38,
                    "density": 1180.0,
                    "yield_strength": 6e7,
                    "strain_rate": 1e-5
                }
            }
        }
    )
    
    # Пакетные задания
    batch_jobs = [
        {
            "name": "Low_velocities",
            "velocities": [50, 75, 100, 125, 150],
            "description": "Низкие скорости"
        },
        {
            "name": "Medium_velocities", 
            "velocities": [175, 200, 225, 250],
            "description": "Средние скорости"
        },
        {
            "name": "High_velocities",
            "velocities": [275, 300, 325, 350],
            "description": "Высокие скорости"
        }
    ]
    
    all_results = []
    
    for job in batch_jobs:
        print(f"\nОбработка пакета: {job['name']}")
        print(f"Описание: {job['description']}")
        print(f"Скорости: {job['velocities']}")
        
        try:
            results = system.run_analysis(
                velocities=job['velocities'],
                output_dir=f"results/batch_{job['name']}"
            )
            
            all_results.append({
                "job_name": job['name'],
                "results": results
            })
            
            print(f"✅ Пакет {job['name']} завершен")
            
        except Exception as e:
            print(f"❌ Ошибка в пакете {job['name']}: {e}")
    
    # Сводный анализ всех пакетов
    print("\n=== Сводный анализ всех пакетов ===")
    
    all_velocities = []
    all_results_data = []
    
    for batch in all_results:
        for result in batch['results'].results:
            all_velocities.append(result['velocity'])
            all_results_data.append(result)
    
    if all_results_data:
        # Создание сводного объекта результатов
        summary_results = SpallFractureResults(
            velocities=all_velocities,
            results=all_results_data,
            output_dir="results/batch_summary",
            analysis_params={}
        )
        
        # Анализ
        summary_analysis = summary_results.analyze()
        
        print(f"Всего обработано скоростей: {len(all_velocities)}")
        print(f"Успешных расчетов: {summary_analysis['successful_calculations']}")
        
        if summary_analysis.get('critical_velocity'):
            print(f"Критическая скорость откола: {summary_analysis['critical_velocity']:.1f} м/с")
        
        # Сводный график
        summary_results.plot_velocity_analysis(
            save_path="results/batch_summary/summary_analysis.png"
        )
        
        # Сводный Excel
        summary_results.export_to_excel("results/batch_summary/summary_results.xlsx")


if __name__ == '__main__':
    """Запуск примеров"""
    
    print("🚀 Запуск примеров Spall Fracture System")
    print("="*60)
    
    try:
        # Базовый пример
        basic_example()
        
        # Параметрическое исследование
        parametric_study_example()
        
        # Пакетная обработка
        batch_processing_example()
        
        print("\n🎉 Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()
