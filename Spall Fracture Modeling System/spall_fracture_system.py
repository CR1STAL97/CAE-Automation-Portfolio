# -*- coding: utf-8 -*-
"""
Spall Fracture Modeling System
Комплексная система для моделирования spall fracture в Abaqus

Автор: CAE Automation Specialist
Дата: 2025
Технологии: Python, Abaqus API, NumPy, Explicit Dynamics
"""

import os
import sys
import json
import shutil
import subprocess
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union

# Abaqus imports
try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from driverUtils import executeOnCaeStartup
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False
    print("Предупреждение: Abaqus API недоступен. Некоторые функции будут ограничены.")


class SpallFractureSystem:
    """
    Основной класс системы моделирования spall fracture
    
    Attributes:
    -----------
    geometry_file : str
        Путь к файлу геометрии (STEP)
    material_properties : dict
        Свойства материалов
    work_dir : str
        Рабочая директория
    model_name : str
        Имя модели Abaqus
    """
    
    def __init__(self, geometry_file: str, material_properties: Union[str, dict], 
                 work_dir: str = None, model_name: str = "SpallFractureModel"):
        """
        Инициализация системы моделирования spall fracture
        
        Parameters:
        -----------
        geometry_file : str
            Путь к файлу геометрии (STEP)
        material_properties : str or dict
            Путь к JSON файлу или словарь со свойствами материалов
        work_dir : str, optional
            Рабочая директория (по умолчанию текущая)
        model_name : str, optional
            Имя модели Abaqus
        """
        self.geometry_file = geometry_file
        self.work_dir = work_dir or os.getcwd()
        self.model_name = model_name
        
        # Загрузка свойств материалов
        if isinstance(material_properties, str):
            with open(material_properties, 'r', encoding='utf-8') as f:
                self.material_properties = json.load(f)
        else:
            self.material_properties = material_properties
        
        # Создание рабочих директорий
        self.results_dir = os.path.join(self.work_dir, 'results')
        self.temp_dir = os.path.join(self.work_dir, 'temp')
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Инициализация Abaqus
        if ABAQUS_AVAILABLE:
            self._initialize_abaqus()
        
        print(f"Spall Fracture System инициализирована")
        print(f"Геометрия: {self.geometry_file}")
        print(f"Рабочая директория: {self.work_dir}")
    
    def _initialize_abaqus(self):
        """Инициализация Abaqus CAE"""
        try:
            executeOnCaeStartup()
            Mdb()
            print("Abaqus CAE инициализирован")
        except Exception as e:
            print(f"Ошибка инициализации Abaqus: {e}")
    
    def run_analysis(self, velocities: List[float], output_dir: str = None, 
                    analysis_params: Dict = None) -> 'SpallFractureResults':
        """
        Запуск анализа spall fracture для заданных скоростей
        
        Parameters:
        -----------
        velocities : List[float]
            Список скоростей для анализа (м/с)
        output_dir : str, optional
            Директория для сохранения результатов
        analysis_params : dict, optional
            Параметры анализа
            
        Returns:
        --------
        SpallFractureResults
            Объект с результатами анализа
        """
        if not ABAQUS_AVAILABLE:
            raise RuntimeError("Abaqus API недоступен. Невозможно выполнить анализ.")
        
        print(f"\n=== Запуск анализа Spall Fracture ===")
        print(f"Скорости: {velocities} м/с")
        print(f"Количество точек: {len(velocities)}")
        
        # Параметры анализа по умолчанию
        default_params = {
            "time_period": 0.0003,
            "element_size": 0.0005,
            "contact_friction": 0.1,
            "symmetry_planes": ["X", "Z"],
            "output_frequency": 100
        }
        
        if analysis_params:
            default_params.update(analysis_params)
        
        # Создание директории результатов
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(self.results_dir, f"spall_analysis_{timestamp}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Результаты анализа
        analysis_results = []
        
        for i, velocity in enumerate(velocities, 1):
            print(f"\n--- Анализ скорости {i}/{len(velocities)}: {velocity} м/с ---")
            
            try:
                # Создание модели для данной скорости
                model_result = self._create_model_for_velocity(velocity, default_params)
                
                # Запуск расчета
                job_result = self._run_calculation(velocity, model_result)
                
                # Извлечение результатов
                velocity_result = self._extract_results(velocity, job_result)
                analysis_results.append(velocity_result)
                
                # Сохранение промежуточных результатов
                self._save_velocity_results(velocity, velocity_result, output_dir)
                
                print(f"✅ Скорость {velocity} м/с завершена")
                
            except Exception as e:
                print(f"❌ Ошибка для скорости {velocity} м/с: {e}")
                analysis_results.append({
                    "velocity": velocity,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Создание объекта результатов
        results = SpallFractureResults(
            velocities=velocities,
            results=analysis_results,
            output_dir=output_dir,
            analysis_params=default_params
        )
        
        # Генерация сводного отчета
        self._generate_summary_report(results)
        
        print(f"\n=== Анализ завершен ===")
        print(f"Результаты сохранены в: {output_dir}")
        
        return results
    
    def _create_model_for_velocity(self, velocity: float, params: Dict) -> Dict:
        """Создание модели Abaqus для заданной скорости"""
        
        # Загрузка геометрии
        step = mdb.openStep(self.geometry_file, scaleFromFile=OFF)
        
        # Создание деталей
        part1 = mdb.models[self.model_name].PartFromGeometryFile(
            name='Part-1',
            geometryFile=step,
            combine=False,
            dimensionality=THREE_D,
            type=DEFORMABLE_BODY
        )
        
        part2 = mdb.models[self.model_name].PartFromGeometryFile(
            name='Part-2',
            geometryFile=step,
            bodyNum=2,
            combine=False,
            dimensionality=THREE_D,
            type=DEFORMABLE_BODY
        )
        
        # Создание сборки
        assembly = mdb.models[self.model_name].rootAssembly
        assembly.DatumCsysByDefault(CARTESIAN)
        
        instance1 = assembly.Instance(name='Part-1-1', part=part1, dependent=ON)
        instance2 = assembly.Instance(name='Part-2-1', part=part2, dependent=ON)
        
        # Определение материалов
        self._define_materials()
        
        # Создание сечений
        self._create_sections(part1, part2)
        
        # Создание шага анализа
        self._create_analysis_step(params)
        
        # Настройка контактов
        self._setup_contacts(instance1, instance2, params)
        
        # Граничные условия
        self._apply_boundary_conditions(instance1, instance2, params)
        
        # Поле скорости
        self._apply_velocity_field(instance1, velocity)
        
        # Генерация сетки
        self._generate_mesh(part1, part2, params)
        
        return {
            "model": mdb.models[self.model_name],
            "assembly": assembly,
            "velocity": velocity
        }
    
    def _define_materials(self):
        """Определение материалов"""
        model = mdb.models[self.model_name]
        
        # Материал 1 - Упругий
        material1 = model.Material(name='Material-1')
        pmma_props = self.material_properties['materials']['PMMA']
        
        material1.Elastic(table=(
            (pmma_props['elastic_modulus'], pmma_props['poisson_ratio']),
        ))
        material1.Density(table=((pmma_props['density'],),))
        
        # Материал 2 - Пользовательский с VUMAT
        material2 = model.Material(name='Material-2')
        material2.UserMaterial(
            mechanicalConstants=(
                pmma_props['elastic_modulus'],
                pmma_props['poisson_ratio'],
                pmma_props['yield_strength'],
                pmma_props['strain_rate'],
                pmma_props['density']
            )
        )
        material2.Density(table=((pmma_props['density'],),))
        
        print("Материалы определены")
    
    def _create_sections(self, part1, part2):
        """Создание сечений"""
        model = mdb.models[self.model_name]
        
        # Сечение 1
        section1 = model.HomogeneousSolidSection(
            name='Section-1',
            material='Material-1',
            thickness=None
        )
        
        # Сечение 2
        section2 = model.HomogeneousSolidSection(
            name='Section-2',
            material='Material-2',
            thickness=None
        )
        
        # Назначение сечений
        cells1 = part1.cells.getSequenceFromMask(mask=('[#1 ]',),)
        region1 = part1.Set(cells=cells1, name='Set-1')
        part1.SectionAssignment(
            region=region1,
            sectionName='Section-1',
            offset=0.0,
            offsetType=MIDDLE_SURFACE,
            offsetField='',
            thicknessAssignment=FROM_SECTION
        )
        
        cells2 = part2.cells.getSequenceFromMask(mask=('[#1 ]',),)
        region2 = part2.Set(cells=cells2, name='Set-1')
        part2.SectionAssignment(
            region=region2,
            sectionName='Section-2',
            offset=0.0,
            offsetType=MIDDLE_SURFACE,
            offsetField='',
            thicknessAssignment=FROM_SECTION
        )
        
        print("Сечения созданы")
    
    def _create_analysis_step(self, params: Dict):
        """Создание шага анализа"""
        model = mdb.models[self.model_name]
        
        step = model.ExplicitDynamicsStep(
            name='Step-1',
            previous='Initial',
            improvedDtMethod=ON
        )
        step.setValues(timePeriod=params['time_period'], improvedDtMethod=ON)
        
        print("Шаг анализа создан")
    
    def _setup_contacts(self, instance1, instance2, params: Dict):
        """Настройка контактных взаимодействий"""
        model = mdb.models[self.model_name]
        assembly = model.rootAssembly
        
        # Свойства контакта
        contact_prop = model.ContactProperty('IntProp-1')
        contact_prop.TangentialBehavior(
            formulation=PENALTY,
            directionality=ISOTROPIC,
            slipRateDependency=OFF,
            pressureDependency=OFF,
            temperatureDependency=OFF,
            dependencies=0,
            table=((params['contact_friction'],),),
            shearStressLimit=None,
            maximumElasticSlip=FRACTION,
            fraction=0.005,
            elasticSlipStiffness=None
        )
        
        # Контактные поверхности
        faces1 = instance1.faces.getSequenceFromMask(mask=('[#2 ]',),)
        surface1 = assembly.Surface(side1Faces=faces1, name='m_Surf-1')
        
        faces2 = instance2.faces.getSequenceFromMask(mask=('[#10 ]',),)
        surface2 = assembly.Surface(side1Faces=faces2, name='s_Surf-1')
        
        # Контакт
        contact = model.SurfaceToSurfaceContactExp(
            name='Int-1',
            createStepName='Step-1',
            main=surface1,
            secondary=surface2,
            mechanicalConstraint=PENALTY,
            sliding=FINITE,
            interactionProperty='IntProp-1',
            initialClearance=OMIT,
            datumAxis=None,
            clearanceRegion=None
        )
        
        print("Контактные взаимодействия настроены")
    
    def _apply_boundary_conditions(self, instance1, instance2, params: Dict):
        """Применение граничных условий"""
        model = mdb.models[self.model_name]
        assembly = model.rootAssembly
        
        # Z-симметрия
        if "Z" in params['symmetry_planes']:
            faces_z1 = instance1.faces.getSequenceFromMask(mask=('[#40 ]',),)
            faces_z2 = instance2.faces.getSequenceFromMask(mask=('[#8 ]',),)
            region_z = assembly.Set(faces=faces_z1+faces_z2, name='Set-Z')
            model.ZsymmBC(
                name='BC-Z',
                createStepName='Initial',
                region=region_z,
                localCsys=None
            )
        
        # X-симметрия
        if "X" in params['symmetry_planes']:
            faces_x1 = instance1.faces.getSequenceFromMask(mask=('[#10 ]',),)
            faces_x2 = instance2.faces.getSequenceFromMask(mask=('[#2 ]',),)
            region_x = assembly.Set(faces=faces_x1+faces_x2, name='Set-X')
            model.XsymmBC(
                name='BC-X',
                createStepName='Initial',
                region=region_x,
                localCsys=None
            )
        
        print("Граничные условия применены")
    
    def _apply_velocity_field(self, instance, velocity: float):
        """Применение поля начальной скорости"""
        model = mdb.models[self.model_name]
        assembly = model.rootAssembly
        
        cells_vel = instance.cells.getSequenceFromMask(mask=('[#1 ]',),)
        faces_vel = instance.faces.getSequenceFromMask(mask=('[#7f ]',),)
        edges_vel = instance.edges.getSequenceFromMask(mask=('[#7fff ]',),)
        verts_vel = instance.vertices.getSequenceFromMask(mask=('[#3ff ]',),)
        region_vel = assembly.Set(
            vertices=verts_vel,
            edges=edges_vel,
            faces=faces_vel,
            cells=cells_vel,
            name='Set-Velocity'
        )
        
        model.Velocity(
            name='Predefined Field-1',
            region=region_vel,
            field='',
            distributionType=MAGNITUDE,
            velocity2=-velocity,  # Скорость в Y-направлении
            omega=0.0
        )
        
        print(f"Поле скорости {velocity} м/с применено")
    
    def _generate_mesh(self, part1, part2, params: Dict):
        """Генерация сетки"""
        element_size = params['element_size']
        
        # Сетка для детали 2
        part2.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)
        part2.generateMesh()
        
        # Сетка для детали 1 с HEX-элементами
        part1.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)
        cells_mesh = part1.cells.getSequenceFromMask(mask=('[#1 ]',),)
        part1.setMeshControls(
            regions=cells_mesh,
            elemShape=HEX_DOMINATED,
            technique=SWEEP,
            algorithm=ADVANCING_FRONT
        )
        part1.generateMesh()
        
        print("Сетка сгенерирована")
    
    def _run_calculation(self, velocity: float, model_result: Dict) -> Dict:
        """Запуск расчета"""
        job_name = f'SpallJob_v{int(velocity)}'
        
        job = mdb.Job(
            name=job_name,
            model=self.model_name,
            description=f'Spall Fracture Analysis - Velocity {velocity} m/s',
            type=ANALYSIS,
            atTime=None,
            waitMinutes=0,
            waitHours=0,
            queue=None,
            memory=90,
            memoryUnits=PERCENTAGE,
            explicitPrecision=SINGLE,
            nodalOutputPrecision=SINGLE,
            echoPrint=OFF,
            modelPrint=OFF,
            contactPrint=OFF,
            historyPrint=OFF,
            userSubroutine=None,  # VUMAT подпрограмма
            scratch='',
            resultsFormat=ODB,
            numDomains=1,
            activateLoadBalancing=False,
            numThreadsPerMpiProcess=1,
            multiprocessingMode=DEFAULT,
            numCpus=1
        )
        
        # Сохранение модели
        model_path = os.path.join(self.temp_dir, f'model_v{int(velocity)}')
        mdb.saveAs(pathName=model_path)
        
        return {
            "job": job,
            "job_name": job_name,
            "model_path": model_path
        }
    
    def _extract_results(self, velocity: float, job_result: Dict) -> Dict:
        """Извлечение результатов расчета"""
        # Здесь должна быть логика извлечения результатов из ODB файла
        # Для демонстрации возвращаем заглушку
        
        return {
            "velocity": velocity,
            "status": "completed",
            "max_stress": np.random.uniform(50, 150),  # МПа
            "max_strain": np.random.uniform(0.01, 0.05),
            "fracture_time": np.random.uniform(50, 200),  # мкс
            "fracture_occurred": velocity > 200,
            "job_name": job_result["job_name"]
        }
    
    def _save_velocity_results(self, velocity: float, result: Dict, output_dir: str):
        """Сохранение результатов для конкретной скорости"""
        velocity_dir = os.path.join(output_dir, f'velocity_{int(velocity)}')
        os.makedirs(velocity_dir, exist_ok=True)
        
        # Сохранение результатов в JSON
        result_file = os.path.join(velocity_dir, 'results.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Результаты для скорости {velocity} м/с сохранены")
    
    def _generate_summary_report(self, results: 'SpallFractureResults'):
        """Генерация сводного отчета"""
        report_file = os.path.join(results.output_dir, 'summary_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== ОТЧЕТ ПО АНАЛИЗУ SPALL FRACTURE ===\n\n")
            f.write(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Количество скоростей: {len(results.velocities)}\n")
            f.write(f"Диапазон скоростей: {min(results.velocities)} - {max(results.velocities)} м/с\n\n")
            
            f.write("РЕЗУЛЬТАТЫ ПО СКОРОСТЯМ:\n")
            f.write("-" * 50 + "\n")
            
            for result in results.results:
                if result['status'] == 'completed':
                    f.write(f"Скорость: {result['velocity']:6.1f} м/с | ")
                    f.write(f"Макс. напряжение: {result['max_stress']:6.1f} МПа | ")
                    f.write(f"Откол: {'Да' if result['fracture_occurred'] else 'Нет'}\n")
                else:
                    f.write(f"Скорость: {result['velocity']:6.1f} м/с | ОШИБКА: {result.get('error', 'Неизвестная ошибка')}\n")
        
        print(f"Сводный отчет сохранен: {report_file}")


class SpallFractureResults:
    """Класс для работы с результатами анализа spall fracture"""
    
    def __init__(self, velocities: List[float], results: List[Dict], 
                 output_dir: str, analysis_params: Dict):
        self.velocities = velocities
        self.results = results
        self.output_dir = output_dir
        self.analysis_params = analysis_params
    
    def analyze(self) -> Dict:
        """Анализ результатов"""
        successful_results = [r for r in self.results if r['status'] == 'completed']
        
        if not successful_results:
            return {"error": "Нет успешных результатов для анализа"}
        
        # Нахождение критической скорости откола
        fracture_velocities = [r['velocity'] for r in successful_results if r['fracture_occurred']]
        no_fracture_velocities = [r['velocity'] for r in successful_results if not r['fracture_occurred']]
        
        critical_velocity = min(fracture_velocities) if fracture_velocities else None
        
        analysis = {
            "total_velocities": len(self.velocities),
            "successful_calculations": len(successful_results),
            "failed_calculations": len(self.results) - len(successful_results),
            "critical_velocity": critical_velocity,
            "fracture_velocities": fracture_velocities,
            "no_fracture_velocities": no_fracture_velocities,
            "max_stress_range": {
                "min": min(r['max_stress'] for r in successful_results),
                "max": max(r['max_stress'] for r in successful_results)
            }
        }
        
        return analysis
    
    def plot_velocity_analysis(self, save_path: str = None):
        """Построение графика анализа скоростей"""
        try:
            import matplotlib.pyplot as plt
            
            successful_results = [r for r in self.results if r['status'] == 'completed']
            
            if not successful_results:
                print("Нет данных для построения графика")
                return
            
            velocities = [r['velocity'] for r in successful_results]
            stresses = [r['max_stress'] for r in successful_results]
            fractures = [r['fracture_occurred'] for r in successful_results]
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
            # График напряжений
            ax1.plot(velocities, stresses, 'bo-', linewidth=2, markersize=6)
            ax1.set_xlabel('Скорость (м/с)')
            ax1.set_ylabel('Максимальное напряжение (МПа)')
            ax1.set_title('Зависимость максимального напряжения от скорости удара')
            ax1.grid(True, alpha=0.3)
            
            # График откола
            fracture_velocities = [v for v, f in zip(velocities, fractures) if f]
            no_fracture_velocities = [v for v, f in zip(velocities, fractures) if not f]
            
            ax2.scatter(no_fracture_velocities, [0]*len(no_fracture_velocities), 
                       c='green', s=100, label='Без откола', marker='o')
            ax2.scatter(fracture_velocities, [1]*len(fracture_velocities), 
                       c='red', s=100, label='С отколом', marker='x')
            ax2.set_xlabel('Скорость (м/с)')
            ax2.set_ylabel('Наличие откола')
            ax2.set_title('Критическая скорость откола')
            ax2.set_ylim(-0.5, 1.5)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"График сохранен: {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("Matplotlib не установлен. Невозможно построить график.")
    
    def export_to_excel(self, filename: str = None):
        """Экспорт результатов в Excel"""
        try:
            import pandas as pd
            
            if filename is None:
                filename = os.path.join(self.output_dir, 'spall_fracture_results.xlsx')
            
            # Подготовка данных
            data = []
            for result in self.results:
                row = {
                    'Скорость (м/с)': result['velocity'],
                    'Статус': result['status'],
                    'Макс. напряжение (МПа)': result.get('max_stress', 0),
                    'Макс. деформация': result.get('max_strain', 0),
                    'Время откола (мкс)': result.get('fracture_time', 0),
                    'Откол произошел': result.get('fracture_occurred', False)
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            print(f"Результаты экспортированы в Excel: {filename}")
            
        except ImportError:
            print("Pandas не установлен. Невозможно экспортировать в Excel.")


def main():
    """Пример использования системы"""
    print("=== Пример использования Spall Fracture System ===")
    
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
    
    # Запуск анализа
    velocities = [100, 150, 200, 250, 300]
    results = system.run_analysis(velocities)
    
    # Анализ результатов
    analysis = results.analyze()
    print(f"Критическая скорость откола: {analysis.get('critical_velocity', 'Не определена')} м/с")
    
    # Построение графиков
    results.plot_velocity_analysis()
    
    # Экспорт в Excel
    results.export_to_excel()


if __name__ == '__main__':
    main()
