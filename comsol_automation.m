%% COMSOL LiveLink Automation - Профессиональная автоматизация
% Система автоматизации мультифизических расчетов в COMSOL через MATLAB LiveLink
%
% Автор: CAE Automation Specialist
% Дата: 2025
% Технологии: MATLAB, COMSOL LiveLink, Optimization Toolbox

classdef COMSOLAutomation < handle
    properties
        model
        results
        parameters
        config
        output_dir
    end
    
    methods
        function obj = COMSOLAutomation(config, output_dir)
            % Инициализация класса автоматизации COMSOL
            fprintf('=== Инициализация COMSOL LiveLink ===\n');
            
            % Проверка доступности COMSOL
            if ~exist('mphstart', 'file')
                error('COMSOL LiveLink не установлен или не настроен');
            end
            
            % Запуск COMSOL
            mphstart();
            obj.model = mphload('empty_model.mph'); % Загрузка пустой модели
            
            % Конфигурация по умолчанию
            obj.default_config = struct(...
                'materials', struct(), ...
                'physics', struct(), ...
                'mesh_settings', struct(), ...
                'solver_settings', struct(), ...
                'optimization', struct() ...
            );
            
            obj.config = config;
            if isempty(obj.config)
                obj.config = obj.default_config;
            end
            
            obj.output_dir = output_dir;
            if isempty(obj.output_dir)
                obj.output_dir = 'results/comsol_automation';
            end
            
            % Создание директорий
            if ~exist(obj.output_dir, 'dir')
                mkdir(obj.output_dir);
            end
            
            fprintf('COMSOL LiveLink инициализирован успешно\n');
        end
        
        function obj = create_thermal_analysis(obj, geometry_params)
            % Создание теплового анализа
            % geometry_params: структура с параметрами геометрии
            
            fprintf('=== Создание теплового анализа ===\n');
            
            % Создание геометрии
            obj = obj.create_geometry(geometry_params);
            
            % Определение материалов
            obj = obj.define_materials();
            
            % Настройка физики
            obj = obj.setup_thermal_physics();
            
            % Создание сетки
            obj = obj.generate_mesh();
            
            % Настройка решателя
            obj = obj.setup_solver();
            
            fprintf('Тепловой анализ создан успешно\n');
        end
        
        function obj = create_structural_analysis(obj, geometry_params)
            % Создание структурного анализа
            
            fprintf('=== Создание структурного анализа ===\n');
            
            % Создание геометрии
            obj = obj.create_geometry(geometry_params);
            
            % Определение материалов
            obj = obj.define_materials();
            
            % Настройка физики
            obj = obj.setup_structural_physics();
            
            % Создание сетки
            obj = obj.generate_mesh();
            
            % Настройка решателя
            obj = obj.setup_solver();
            
            fprintf('Структурный анализ создан успешно\n');
        end
        
        function obj = create_multiphysics_analysis(obj, geometry_params)
            % Создание мультифизического анализа
            
            fprintf('=== Создание мультифизического анализа ===\n');
            
            % Создание геометрии
            obj = obj.create_geometry(geometry_params);
            
            % Определение материалов
            obj = obj.define_materials();
            
            % Настройка физики
            obj = obj.setup_multiphysics();
            
            % Создание сетки
            obj = obj.generate_mesh();
            
            % Настройка решателя
            obj = obj.setup_solver();
            
            fprintf('Мультифизический анализ создан успешно\n');
        end
        
        function obj = create_geometry(obj, params)
            % Создание геометрии
            fprintf('Создание геометрии...\n');
            
            % Параметры геометрии
            obj.model.param.set('L', params.length);
            obj.model.param.set('W', params.width);
            obj.model.param.set('H', params.height);
            
            % Создание блока
            obj.model.geom.create('blk1', 'Block');
            obj.model.geom('blk1').set('size', {'L' 'W' 'H'});
            obj.model.geom('blk1').set('pos', {'0' '0' '0'});
            
            % Построение геометрии
            obj.model.geom.run();
            
            fprintf('Геометрия создана: %.2f x %.2f x %.2f м\n', ...
                params.length, params.width, params.height);
        end
        
        function obj = define_materials(obj)
            % Определение материалов
            fprintf('Определение материалов...\n');
            
            % Материал 1 - Алюминий
            obj.model.material.create('mat1', 'Aluminum');
            obj.model.material('mat1').propertyGroup('def').set('thermalconductivity', 205); % W/(m·K)
            obj.model.material('mat1').propertyGroup('def').set('density', 2700); % kg/m³
            obj.model.material('mat1').propertyGroup('def').set('heatcapacity', 900); % J/(kg·K)
            
            % Материал 2 - Сталь
            obj.model.material.create('mat2', 'Steel');
            obj.model.material('mat2').propertyGroup('def').set('thermalconductivity', 50); % W/(m·K)
            obj.model.material('mat2').propertyGroup('def').set('density', 7850); % kg/m³
            obj.model.material('mat2').propertyGroup('def').set('heatcapacity', 460); % J/(kg·K)
            
            fprintf('Материалы определены\n');
        end
        
        function obj = setup_thermal_physics(obj)
            % Настройка физики - теплопередача
            fprintf('Настройка тепловой физики...\n');
            
            % Активация теплопередачи
            obj.model.physics.create('ht', 'HeatTransfer');
            obj.model.physics('ht').create('init1', 'Initial');
            obj.model.physics('ht').create('temp1', 'Temperature');
            obj.model.physics('ht').create('flux1', 'HeatFlux');
            
            % Начальная температура
            obj.model.physics('ht').feature('init1').set('T0', '293.15'); % 20°C
            
            % Граничные условия
            % Температура на нижней грани
            obj.model.physics('ht').create('temp2', 'Temperature');
            obj.model.physics('ht').feature('temp2').selection.set([1]);
            obj.model.physics('ht').feature('temp2').set('T0', '373.15'); % 100°C
            
            % Тепловой поток на верхней грани
            obj.model.physics('ht').create('flux2', 'HeatFlux');
            obj.model.physics('ht').feature('flux2').selection.set([2]);
            obj.model.physics('ht').feature('flux2').set('q0', '1000'); % 1000 W/m²
            
            fprintf('Тепловая физика настроена\n');
        end
        
        function obj = setup_structural_physics(obj)
            % Настройка физики - структурный анализ
            fprintf('Настройка структурной физики...\n');
            
            % Активация структурной механики
            obj.model.physics.create('solid', 'SolidMechanics');
            obj.model.physics('solid').create('init1', 'Initial');
            obj.model.physics('solid').create('fix1', 'Fixed');
            obj.model.physics('solid').create('load1', 'BoundaryLoad');
            
            % Граничные условия
            % Защемление нижней грани
            obj.model.physics('solid').feature('fix1').selection.set([1]);
            
            % Нагрузка на верхней грани
            obj.model.physics('solid').feature('load1').selection.set([2]);
            obj.model.physics('solid').feature('load1').set('F', '1000'); % 1000 N/m²
            
            fprintf('Структурная физика настроена\n');
        end
        
        function obj = setup_multiphysics(obj)
            % Настройка мультифизической связи
            fprintf('Настройка мультифизики...\n');
            
            % Тепловая физика
            obj = obj.setup_thermal_physics();
            
            % Структурная физика
            obj = obj.setup_structural_physics();
            
            % Связь температура-деформация
            obj.model.physics.create('temp', 'Temperature');
            obj.model.physics('temp').create('temp1', 'Temperature');
            obj.model.physics('temp').feature('temp1').set('T', 'ht.T');
            
            fprintf('Мультифизика настроена\n');
        end
        
        function obj = generate_mesh(obj)
            % Генерация сетки
            fprintf('Генерация сетки...\n');
            
            % Настройка сетки
            obj.model.mesh.create('mesh1');
            obj.model.mesh('mesh1').create('size1', 'Size');
            obj.model.mesh('mesh1').feature('size1').set('hmax', '0.01'); % Максимальный размер элемента
            obj.model.mesh('mesh1').feature('size1').set('hmin', '0.001'); % Минимальный размер элемента
            
            % Генерация сетки
            obj.model.mesh('mesh1').run();
            
            fprintf('Сетка сгенерирована\n');
        end
        
        function obj = setup_solver(obj)
            % Настройка решателя
            fprintf('Настройка решателя...\n');
            
            % Стационарный решатель
            obj.model.study.create('std1');
            obj.model.study('std1').create('stat', 'Stationary');
            obj.model.study('std1').feature('stat').set('activate', {'ht'});
            
            fprintf('Решатель настроен\n');
        end
        
        function obj = run_analysis(obj)
            % Запуск анализа
            fprintf('=== Запуск анализа ===\n');
            
            % Решение
            obj.model.study('std1').run();
            
            fprintf('Анализ завершен успешно\n');
        end
        
        function results = extract_results(obj)
            % Извлечение результатов
            fprintf('Извлечение результатов...\n');
            
            results = struct();
            
            % Максимальная температура
            results.max_temp = mphmax(obj.model, 'T', 'unit', 'K');
            results.max_temp_celsius = results.max_temp - 273.15;
            
            % Минимальная температура
            results.min_temp = mphmin(obj.model, 'T', 'unit', 'K');
            results.min_temp_celsius = results.min_temp - 273.15;
            
            % Средняя температура
            results.avg_temp = mphint2(obj.model, 'T', 'unit', 'K') / mphint2(obj.model, '1', 'unit', '1');
            results.avg_temp_celsius = results.avg_temp - 273.15;
            
            % Тепловой поток
            results.heat_flux = mphint2(obj.model, 'ht.flux_magnitude', 'unit', 'W/m^2');
            
            fprintf('Результаты извлечены:\n');
            fprintf('  Макс. температура: %.2f°C\n', results.max_temp_celsius);
            fprintf('  Мин. температура: %.2f°C\n', results.min_temp_celsius);
            fprintf('  Средняя температура: %.2f°C\n', results.avg_temp_celsius);
            fprintf('  Тепловой поток: %.2f W/m²\n', results.heat_flux);
            
            obj.results = results;
        end
        
        function obj = parametric_study(obj, param_ranges)
            % Параметрическое исследование
            % param_ranges: структура с диапазонами параметров
            
            fprintf('=== Параметрическое исследование ===\n');
            
            % Извлечение параметров
            param_names = fieldnames(param_ranges);
            param_values = struct2cell(param_ranges);
            
            % Создание сетки параметров
            [param_grids{1:length(param_names)}] = ndgrid(param_values{:});
            
            % Результаты
            results = [];
            
            % Цикл по всем комбинациям параметров
            total_combinations = numel(param_grids{1});
            fprintf('Всего комбинаций: %d\n', total_combinations);
            
            for i = 1:total_combinations
                fprintf('Комбинация %d/%d\n', i, total_combinations);
                
                % Установка параметров
                for j = 1:length(param_names)
                    param_value = param_grids{j}(i);
                    obj.model.param.set(param_names{j}, num2str(param_value));
                end
                
                % Обновление геометрии
                obj.model.geom.run();
                
                % Запуск анализа
                obj.run_analysis();
                
                % Извлечение результатов
                current_results = obj.extract_results();
                
                % Сохранение параметров и результатов
                result_entry = struct();
                for j = 1:length(param_names)
                    result_entry.(param_names{j}) = param_grids{j}(i);
                end
                result_entry.max_temp = current_results.max_temp_celsius;
                result_entry.min_temp = current_results.min_temp_celsius;
                result_entry.avg_temp = current_results.avg_temp_celsius;
                result_entry.heat_flux = current_results.heat_flux;
                
                results = [results; result_entry];
            end
            
            obj.results = results;
            fprintf('Параметрическое исследование завершено\n');
        end
        
        function obj = optimize_geometry(obj, objective_function, constraints)
            % Оптимизация геометрии
            % objective_function: функция цели
            % constraints: ограничения
            
            fprintf('=== Оптимизация геометрии ===\n');
            
            % Начальные значения параметров
            x0 = [obj.model.param.get('L'), obj.model.param.get('W'), obj.model.param.get('H')];
            
            % Ограничения
            lb = constraints.lower_bounds;
            ub = constraints.upper_bounds;
            
            % Настройки оптимизации
            options = optimoptions('fmincon', ...
                'Display', 'iter', ...
                'MaxIterations', 50, ...
                'OptimalityTolerance', 1e-6);
            
            % Запуск оптимизации
            [x_opt, fval, exitflag] = fmincon(...
                @(x) obj.objective_wrapper(x, objective_function), ...
                x0, [], [], [], [], lb, ub, [], options);
            
            % Установка оптимальных параметров
            obj.model.param.set('L', num2str(x_opt(1)));
            obj.model.param.set('W', num2str(x_opt(2)));
            obj.model.param.set('H', num2str(x_opt(3)));
            
            % Обновление геометрии
            obj.model.geom.run();
            
            % Финальный анализ
            obj.run_analysis();
            final_results = obj.extract_results();
            
            fprintf('Оптимизация завершена\n');
            fprintf('Оптимальные параметры: L=%.3f, W=%.3f, H=%.3f\n', x_opt(1), x_opt(2), x_opt(3));
            fprintf('Значение функции цели: %.3f\n', fval);
            
            obj.results = final_results;
        end
        
        function fval = objective_wrapper(obj, x, objective_function)
            % Обертка для функции цели
            
            % Установка параметров
            obj.model.param.set('L', num2str(x(1)));
            obj.model.param.set('W', num2str(x(2)));
            obj.model.param.set('H', num2str(x(3)));
            
            % Обновление геометрии
            obj.model.geom.run();
            
            % Запуск анализа
            obj.run_analysis();
            
            % Извлечение результатов
            results = obj.extract_results();
            
            % Вычисление функции цели
            fval = objective_function(results);
        end
        
        function obj = save_results(obj, filename)
            % Сохранение результатов
            if ~isempty(obj.results)
                save(filename, 'obj');
                fprintf('Результаты сохранены в файл: %s\n', filename);
            else
                fprintf('Нет результатов для сохранения\n');
            end
        end
        
        function obj = plot_results(obj)
            % Построение графиков результатов
            if isempty(obj.results)
                fprintf('Нет результатов для построения графиков\n');
                return;
            end
            
            fprintf('Построение графиков...\n');
            
            % Создание фигуры
            figure('Name', 'COMSOL Analysis Results', 'Position', [100, 100, 1200, 800]);
            
            % График 1: Распределение температур
            subplot(2, 2, 1);
            if isstruct(obj.results) && isfield(obj.results, 'max_temp_celsius')
                bar([obj.results.max_temp_celsius, obj.results.min_temp_celsius, obj.results.avg_temp_celsius]);
                title('Распределение температур');
                xlabel('Тип температуры');
                ylabel('Температура (°C)');
                set(gca, 'XTickLabel', {'Максимальная', 'Минимальная', 'Средняя'});
            end
            
            % График 2: Тепловой поток
            subplot(2, 2, 2);
            if isstruct(obj.results) && isfield(obj.results, 'heat_flux')
                bar(obj.results.heat_flux);
                title('Тепловой поток');
                ylabel('Поток (W/m²)');
            end
            
            % График 3: Параметрическое исследование (если есть)
            subplot(2, 2, 3);
            if isstruct(obj.results) && length(obj.results) > 1
                if isfield(obj.results, 'max_temp')
                    plot([obj.results.max_temp], 'o-');
                    title('Параметрическое исследование');
                    xlabel('Номер комбинации');
                    ylabel('Макс. температура (°C)');
                end
            end
            
            % График 4: Сводная информация
            subplot(2, 2, 4);
            text(0.1, 0.8, sprintf('Всего комбинаций: %d', length(obj.results)), 'FontSize', 12);
            if isstruct(obj.results) && isfield(obj.results, 'max_temp_celsius')
                text(0.1, 0.6, sprintf('Макс. температура: %.2f°C', obj.results.max_temp_celsius), 'FontSize', 12);
                text(0.1, 0.4, sprintf('Тепловой поток: %.2f W/m²', obj.results.heat_flux), 'FontSize', 12);
            end
            title('Сводная информация');
            axis off;
            
            fprintf('Графики построены\n');
        end
        
        function obj = generate_report(obj, results, output_file)
            % Генерация отчета
            if nargin < 2
                results = obj.results;
            end
            if nargin < 3
                output_file = fullfile(obj.output_dir, 'comsol_report.html');
            end
            
            fprintf('Генерация отчета: %s\n', output_file);
            
            % Создание HTML отчета
            html_content = obj.create_html_report(results);
            
            % Сохранение отчета
            fid = fopen(output_file, 'w', 'UTF-8');
            if fid == -1
                error('Не удалось создать файл отчета');
            end
            
            fprintf(fid, '%s', html_content);
            fclose(fid);
            
            fprintf('Отчет создан: %s\n', output_file);
        end
        
        function html_content = create_html_report(obj, results)
            % Создание HTML отчета
            html_content = sprintf(['<!DOCTYPE html>\n' ...
                '<html lang="ru">\n' ...
                '<head>\n' ...
                '    <meta charset="UTF-8">\n' ...
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n' ...
                '    <title>COMSOL Analysis Report</title>\n' ...
                '    <style>\n' ...
                '        body { font-family: Arial, sans-serif; margin: 40px; }\n' ...
                '        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }\n' ...
                '        .section { margin: 20px 0; }\n' ...
                '        .summary { background-color: #e8f4f8; padding: 15px; border-radius: 5px; }\n' ...
                '        table { border-collapse: collapse; width: 100%%; }\n' ...
                '        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n' ...
                '        th { background-color: #f2f2f2; }\n' ...
                '    </style>\n' ...
                '</head>\n' ...
                '<body>\n' ...
                '    <div class="header">\n' ...
                '        <h1>Отчет по анализу COMSOL</h1>\n' ...
                '        <p><strong>Дата анализа:</strong> %s</p>\n' ...
                '        <p><strong>Тип анализа:</strong> Мультифизический</p>\n' ...
                '    </div>\n' ...
                '    <div class="section">\n' ...
                '        <h2>Результаты</h2>\n' ...
                '        <div class="summary">\n' ...
                '            <p><strong>Максимальная температура:</strong> %.2f°C</p>\n' ...
                '            <p><strong>Минимальная температура:</strong> %.2f°C</p>\n' ...
                '            <p><strong>Средняя температура:</strong> %.2f°C</p>\n' ...
                '            <p><strong>Тепловой поток:</strong> %.2f W/m²</p>\n' ...
                '        </div>\n' ...
                '    </div>\n' ...
                '</body>\n' ...
                '</html>\n'], ...
                datestr(now, 'yyyy-mm-dd HH:MM:SS'), ...
                results.max_temp_celsius, ...
                results.min_temp_celsius, ...
                results.avg_temp_celsius, ...
                results.heat_flux);
        end
    end
end

%% Основная функция
function main()
    % Главная функция с примерами использования
    
    fprintf('=== COMSOL MATLAB Automation Examples ===\n');
    
    % Создание объекта автоматизации
    comsol_auto = COMSOLAutomation();
    
    % Параметры геометрии
    geometry_params = struct();
    geometry_params.length = 0.1;  % 10 см
    geometry_params.width = 0.05;  % 5 см
    geometry_params.height = 0.02; % 2 см
    
    % Создание теплового анализа
    comsol_auto = comsol_auto.create_thermal_analysis(geometry_params);
    
    % Запуск анализа
    comsol_auto = comsol_auto.run_analysis();
    
    % Извлечение результатов
    comsol_auto = comsol_auto.extract_results();
    
    % Параметрическое исследование
    param_ranges = struct();
    param_ranges.length = [0.05, 0.1, 0.15];  % Различные длины
    param_ranges.width = [0.03, 0.05, 0.07]; % Различные ширины
    
    comsol_auto = comsol_auto.parametric_study(param_ranges);
    
    % Сохранение результатов
    comsol_auto.save_results('comsol_results.mat');
    
    % Построение графиков
    comsol_auto.plot_results();
    
    % Генерация отчета
    comsol_auto.generate_report();
    
    fprintf('\n=== Все примеры выполнены успешно ===\n');
    fprintf('Созданы модели для демонстрации возможностей автоматизации COMSOL\n');
end

%% Запуск основной функции
if nargin == 0
    main();
end
