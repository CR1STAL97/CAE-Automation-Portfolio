%% Базовый пример использования COMSOL Automation
% Демонстрирует основные возможности системы автоматизации COMSOL

function basic_automation_example()
    % Базовый пример автоматизации COMSOL
    
    fprintf('=== Базовый пример COMSOL Automation ===\n');
    
    % 1. Создание системы
    fprintf('\n1. Создание системы автоматизации...\n');
    
    % Конфигурация
    config = struct();
    config.materials = struct(...
        'Aluminum', struct(...
            'thermal_conductivity', 205, ...
            'density', 2700, ...
            'heat_capacity', 900 ...
        ), ...
        'Steel', struct(...
            'thermal_conductivity', 50, ...
            'density', 7850, ...
            'heat_capacity', 460 ...
        ) ...
    );
    
    comsol_auto = COMSOLAutomation(config, 'results/basic_automation');
    
    % 2. Параметры геометрии
    fprintf('\n2. Настройка параметров геометрии...\n');
    
    geometry_params = struct();
    geometry_params.length = 0.1;   % 10 см
    geometry_params.width = 0.05;   % 5 см
    geometry_params.height = 0.02;  % 2 см
    
    fprintf('Геометрия: %.2f x %.2f x %.2f м\n', ...
        geometry_params.length, geometry_params.width, geometry_params.height);
    
    % 3. Создание теплового анализа
    fprintf('\n3. Создание теплового анализа...\n');
    
    try
        comsol_auto = comsol_auto.create_thermal_analysis(geometry_params);
        fprintf('✅ Тепловой анализ создан успешно\n');
    catch ME
        fprintf('❌ Ошибка при создании анализа: %s\n', ME.message);
        return;
    end
    
    % 4. Запуск анализа
    fprintf('\n4. Запуск анализа...\n');
    
    try
        comsol_auto = comsol_auto.run_analysis();
        fprintf('✅ Анализ выполнен успешно\n');
    catch ME
        fprintf('❌ Ошибка при выполнении анализа: %s\n', ME.message);
        return;
    end
    
    % 5. Извлечение результатов
    fprintf('\n5. Извлечение результатов...\n');
    
    try
        results = comsol_auto.extract_results();
        fprintf('✅ Результаты извлечены успешно\n');
    catch ME
        fprintf('❌ Ошибка при извлечении результатов: %s\n', ME.message);
        return;
    end
    
    % 6. Анализ результатов
    fprintf('\n6. Анализ результатов:\n');
    fprintf('-' * 50 + '\n');
    fprintf('Максимальная температура: %.2f°C\n', results.max_temp_celsius);
    fprintf('Минимальная температура: %.2f°C\n', results.min_temp_celsius);
    fprintf('Средняя температура: %.2f°C\n', results.avg_temp_celsius);
    fprintf('Тепловой поток: %.2f W/m²\n', results.heat_flux);
    fprintf('-' * 50 + '\n');
    
    % 7. Построение графиков
    fprintf('\n7. Построение графиков...\n');
    
    try
        comsol_auto.plot_results();
        fprintf('✅ Графики построены\n');
    catch ME
        fprintf('⚠️ Ошибка при построении графиков: %s\n', ME.message);
    end
    
    % 8. Генерация отчета
    fprintf('\n8. Генерация отчета...\n');
    
    try
        comsol_auto.generate_report();
        fprintf('✅ Отчет создан\n');
    catch ME
        fprintf('⚠️ Ошибка при создании отчета: %s\n', ME.message);
    end
    
    % 9. Сохранение результатов
    fprintf('\n9. Сохранение результатов...\n');
    
    try
        comsol_auto.save_results('results/basic_automation/results.mat');
        fprintf('✅ Результаты сохранены\n');
    catch ME
        fprintf('⚠️ Ошибка при сохранении: %s\n', ME.message);
    end
    
    fprintf('\n=== Базовый пример завершен ===\n');
end

function parametric_study_example()
    % Пример параметрического исследования
    
    fprintf('\n=== Параметрическое исследование ===\n');
    
    % Создание системы
    comsol_auto = COMSOLAutomation([], 'results/parametric_study');
    
    % Параметры геометрии
    geometry_params = struct();
    geometry_params.length = 0.1;
    geometry_params.width = 0.05;
    geometry_params.height = 0.02;
    
    % Создание анализа
    comsol_auto = comsol_auto.create_thermal_analysis(geometry_params);
    
    % Параметрическое исследование
    param_ranges = struct();
    param_ranges.length = [0.05, 0.1, 0.15];  % Различные длины
    param_ranges.width = [0.03, 0.05, 0.07];  % Различные ширины
    
    fprintf('Исследование %d x %d = %d комбинаций параметров\n', ...
        length(param_ranges.length), length(param_ranges.width), ...
        length(param_ranges.length) * length(param_ranges.width));
    
    try
        comsol_auto = comsol_auto.parametric_study(param_ranges);
        fprintf('✅ Параметрическое исследование завершено\n');
        
        % Анализ результатов
        if ~isempty(comsol_auto.results)
            results = comsol_auto.results;
            
            % Нахождение оптимальных параметров
            max_temps = [results.max_temp];
            [min_temp, min_idx] = min(max_temps);
            
            fprintf('\nРезультаты параметрического исследования:\n');
            fprintf('-' * 60 + '\n');
            fprintf('Оптимальная комбинация (минимальная температура):\n');
            fprintf('  Длина: %.3f м\n', results(min_idx).length);
            fprintf('  Ширина: %.3f м\n', results(min_idx).width);
            fprintf('  Макс. температура: %.2f°C\n', results(min_idx).max_temp);
            fprintf('-' * 60 + '\n');
            
            % Создание графика чувствительности
            create_sensitivity_plot(results);
        end
        
    catch ME
        fprintf('❌ Ошибка параметрического исследования: %s\n', ME.message);
    end
end

function optimization_example()
    % Пример оптимизации геометрии
    
    fprintf('\n=== Оптимизация геометрии ===\n');
    
    % Создание системы
    comsol_auto = COMSOLAutomation([], 'results/optimization');
    
    % Параметры геометрии
    geometry_params = struct();
    geometry_params.length = 0.1;
    geometry_params.width = 0.05;
    geometry_params.height = 0.02;
    
    % Создание анализа
    comsol_auto = comsol_auto.create_thermal_analysis(geometry_params);
    
    % Функция цели (минимизация максимальной температуры)
    objective_function = @(results) results.max_temp_celsius;
    
    % Ограничения
    constraints = struct();
    constraints.lower_bounds = [0.05, 0.03, 0.01];  % Минимальные размеры
    constraints.upper_bounds = [0.2, 0.1, 0.05];     % Максимальные размеры
    
    fprintf('Начальные параметры: L=%.3f, W=%.3f, H=%.3f\n', ...
        geometry_params.length, geometry_params.width, geometry_params.height);
    
    try
        comsol_auto = comsol_auto.optimize_geometry(objective_function, constraints);
        fprintf('✅ Оптимизация завершена\n');
        
    catch ME
        fprintf('❌ Ошибка оптимизации: %s\n', ME.message);
    end
end

function create_sensitivity_plot(results)
    % Создание графика чувствительности параметров
    
    if isempty(results)
        return;
    end
    
    try
        figure('Name', 'Parameter Sensitivity Analysis', 'Position', [100, 100, 1200, 600]);
        
        % График 1: Влияние длины на температуру
        subplot(1, 2, 1);
        lengths = [results.length];
        max_temps = [results.max_temp];
        plot(lengths, max_temps, 'bo-', 'LineWidth', 2, 'MarkerSize', 8);
        xlabel('Длина (м)');
        ylabel('Максимальная температура (°C)');
        title('Влияние длины на температуру');
        grid on;
        
        % График 2: Влияние ширины на температуру
        subplot(1, 2, 2);
        widths = [results.width];
        plot(widths, max_temps, 'ro-', 'LineWidth', 2, 'MarkerSize', 8);
        xlabel('Ширина (м)');
        ylabel('Максимальная температура (°C)');
        title('Влияние ширины на температуру');
        grid on;
        
        % Сохранение графика
        saveas(gcf, 'results/parametric_study/sensitivity_analysis.png');
        fprintf('✅ График чувствительности сохранен\n');
        
    catch ME
        fprintf('⚠️ Ошибка при создании графика: %s\n', ME.message);
    end
end

function multiphysics_example()
    % Пример мультифизического анализа
    
    fprintf('\n=== Мультифизический анализ ===\n');
    
    % Создание системы
    comsol_auto = COMSOLAutomation([], 'results/multiphysics');
    
    % Параметры геометрии
    geometry_params = struct();
    geometry_params.length = 0.1;
    geometry_params.width = 0.05;
    geometry_params.height = 0.02;
    
    % Создание мультифизического анализа
    try
        comsol_auto = comsol_auto.create_multiphysics_analysis(geometry_params);
        fprintf('✅ Мультифизический анализ создан\n');
        
        % Запуск анализа
        comsol_auto = comsol_auto.run_analysis();
        fprintf('✅ Мультифизический анализ выполнен\n');
        
        % Извлечение результатов
        results = comsol_auto.extract_results();
        
        fprintf('\nРезультаты мультифизического анализа:\n');
        fprintf('-' * 50 + '\n');
        fprintf('Максимальная температура: %.2f°C\n', results.max_temp_celsius);
        fprintf('Тепловой поток: %.2f W/m²\n', results.heat_flux);
        fprintf('-' * 50 + '\n');
        
    catch ME
        fprintf('❌ Ошибка мультифизического анализа: %s\n', ME.message);
    end
end

function batch_processing_example()
    % Пример пакетной обработки
    
    fprintf('\n=== Пакетная обработка ===\n');
    
    % Список конфигураций для обработки
    configs = {
        struct('length', 0.05, 'width', 0.03, 'height', 0.01),
        struct('length', 0.1, 'width', 0.05, 'height', 0.02),
        struct('length', 0.15, 'width', 0.07, 'height', 0.03)
    };
    
    results = [];
    
    for i = 1:length(configs)
        fprintf('\n--- Обработка конфигурации %d/%d ---\n', i, length(configs));
        
        try
            % Создание системы для каждой конфигурации
            comsol_auto = COMSOLAutomation([], sprintf('results/batch_%d', i));
            
            % Создание анализа
            comsol_auto = comsol_auto.create_thermal_analysis(configs{i});
            
            % Запуск анализа
            comsol_auto = comsol_auto.run_analysis();
            
            % Извлечение результатов
            current_results = comsol_auto.extract_results();
            
            % Сохранение результатов
            results = [results; current_results];
            
            fprintf('✅ Конфигурация %d обработана\n', i);
            
        catch ME
            fprintf('❌ Ошибка в конфигурации %d: %s\n', i, ME.message);
        end
    end
    
    % Сводный анализ
    if ~isempty(results)
        fprintf('\n=== Сводный анализ пакетной обработки ===\n');
        fprintf('Обработано конфигураций: %d\n', length(results));
        
        max_temps = [results.max_temp_celsius];
        fprintf('Диапазон температур: %.2f - %.2f°C\n', min(max_temps), max(max_temps));
        fprintf('Средняя температура: %.2f°C\n', mean(max_temps));
    end
end

%% Главная функция
function main()
    % Запуск всех примеров
    
    fprintf('🚀 Запуск примеров COMSOL Automation\n');
    fprintf('=' * 60 + '\n');
    
    try
        % Базовый пример
        basic_automation_example();
        
        % Параметрическое исследование
        parametric_study_example();
        
        % Оптимизация
        optimization_example();
        
        % Мультифизический анализ
        multiphysics_example();
        
        % Пакетная обработка
        batch_processing_example();
        
        fprintf('\n🎉 Все примеры выполнены успешно!\n');
        
    catch ME
        fprintf('\n❌ Ошибка при выполнении примеров: %s\n', ME.message);
        fprintf('Стек вызовов:\n');
        for i = 1:length(ME.stack)
            fprintf('  %s (строка %d)\n', ME.stack(i).name, ME.stack(i).line);
        end
    end
end

%% Запуск примеров
if nargin == 0
    main();
end
