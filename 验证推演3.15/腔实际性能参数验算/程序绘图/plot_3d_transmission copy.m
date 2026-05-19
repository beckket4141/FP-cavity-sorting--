% 清理环境
clear; clc; close all;

% --- 1. 透射率真值字典 (来自你提供的数据) ---
% keys 为 l 的模式数字, values 为由于插损等带来的真实透射率上限
l_keys = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
T_vals = [0.928928, 0.916598, 0.904994, 0.897154, 0.898728, 0.877059, 0.867480, 0.840313, 0.839592, 0.816486];
T_map = containers.Map(l_keys, T_vals);

% --- 2. 读取当前目录下所有的 CSV 文件 ---
files = dir('*.csv');
data_list = {};
all_lambdas = [];

for i = 1:length(files)
    fname = files(i).name;
    % 正则表达式提取文件名中的 l 值 (兼容 "l0.csv", "data_l0.csv", "l0_test.csv" 等各种命名)
    tokens = regexp(fname, '(?:^|[_-])l(\d+)(?:[_\.]|$)', 'tokens');
    if isempty(tokens)
        continue;
    end
    l_num = str2double(tokens{1}{1});
    
    if ~isKey(T_map, l_num)
        continue;
    end
    
    % 读取 CSV 数据
    opts = detectImportOptions(fname);
    tb = readtable(fname, opts);
    colNames = tb.Properties.VariableNames;
    
    % 猜测列名 (匹配不区分大小写的 lambda/wavelength 和 power/uw)
    lambda_idx = find(contains(lower(colNames), 'lambda') | contains(lower(colNames), 'wavelength'), 1);
    power_idx = find(contains(lower(colNames), 'power') | contains(lower(colNames), 'trans') | contains(lower(colNames), 'uw'), 1);
    
    if isempty(lambda_idx) || isempty(power_idx)
        fprintf('跳过文件 %s: 找不到对应的列名\n', fname);
        continue;
    end
    
    lambdas = tb{:, lambda_idx};
    powers = tb{:, power_idx};
    
    % 按波长排序以防万一
    [lambdas, sort_idx] = sort(lambdas);
    powers = powers(sort_idx);
    
    % [新增] 仅保留波长 <= 795 nm 的数据
    valid_mask = lambdas <= 795.0;
    lambdas = lambdas(valid_mask);
    powers = powers(valid_mask);
    
    if isempty(lambdas)
        fprintf('跳过文件 %s: 795nm 以下没有有效数据\n', fname);
        continue;
    end
    
    % --- 3. 核心物理换算逻辑：恢复真实透射率 ---
    P_max = max(powers);             % 仅在 <795nm 范围内的最高绝对功率
    T_max = T_map(l_num);            % 该模式的真实透射率
    P_in = P_max / T_max;            % 反推算等效输入功率
    trans = powers / P_in;           % 转化为真实透射率
    
    % 存入数据列表
    data_list{end+1} = struct('l', l_num, 'lambdas', lambdas, 'trans', trans, 'fname', fname);
    all_lambdas = [all_lambdas; lambdas]; % 记录所有波长用于找极小值
end

if isempty(data_list)
    error('没有读取到有效的数据！');
end

% 找出基准波长
base_lambda = min(all_lambdas);
fprintf('找到的全局基准波长 (Base Wavelength): %.4f nm\n', base_lambda);

% 对数据按 l 进行排序
ls = cellfun(@(x) x.l, data_list);
[~, sort_idx] = sort(ls);
data_list = data_list(sort_idx);

% --- 4. 开始 MATLAB 3D 绘图 ---
fig = figure('Position', [100, 100, 1100, 650], 'Color', 'w');
hold on; grid on;

% 配色方案: 使用平滑过渡。为了模仿原图的暖色调/紫色调
% 我们可以使用 MATLAB R2019a+ 内置的 'magma' 或者 'inferno' 小稍作修改
% 如果你的 MATLAB 版本较老，可以使用 colormap(jet(length(data_list)))，这里用 parula
colors = parula(length(data_list)); 

% 若想模仿你的原图暖色调，可以自己定义一个色带，例如从深紫到淡黄
c1 = [0.4, 0.3, 0.4]; % 紫色
c2 = [0.95, 0.8, 0.6]; % 淡橘/黄
colors = [linspace(c1(1),c2(1),length(data_list))', ...
          linspace(c1(2),c2(2),length(data_list))', ...
          linspace(c1(3),c2(3),length(data_list))'];

for i = 1:length(data_list)
    d = data_list{i};
    l_num = d.l;
    
    % 转为皮米(pm)并基于基准偏移
    x_pm = (d.lambdas - base_lambda) * 1000;
    
    % 对透射率进行轻微平滑，消除密集采样点重叠导致的“有粗有细”感
    y_trans = smoothdata(d.trans, 'sgolay', 15); 
    
    % [核心修复] 平滑(smoothdata)会把尖锐的最高峰给“削平”一点点，导致图上最高点达不到理论值。
    % 按照您要求的逻辑：所有平滑后的该模式数据，统统除以 (当前最高点 / 理论最高点)
    % 从而强制确保图上显示出来的最高点，严丝合缝地等于 T_vals 里的理论最高点
    y_trans = y_trans / (max(y_trans) / T_map(l_num));
    
    z_l = l_num * ones(size(x_pm)); % 现在将 l 作为 Y 轴(深度), 透射率作为 Z 轴
    
    % 构建多面体闭合以进行颜色填充 (Z=0 底面)
    % 注意坐标对应： X=波长, Y=模式l, Z=透射率
    x_fill = [x_pm(1); x_pm; x_pm(end)];
    y_fill = [l_num; z_l; l_num];
    z_fill = [0; y_trans; 0];
    
    % 使用 patch 填充区域，去掉面的轮廓线(EdgeColor='none')使之更柔软
    patch(x_fill, y_fill, z_fill, colors(i, :), ...
        'FaceAlpha', 0.5, ...             % 增大透明度，更柔和
        'EdgeColor', 'none');             % **关键改变1**：去掉多边形的黑色轮廓边
    
    % **关键改变2**：单独画顶部曲线（相当于原图上方的深色曲线）
    % 使曲线比填充色更深一点
    darker_color = colors(i, :) * 0.7;
    plot3(x_pm, z_l, y_trans, 'Color', darker_color, 'LineWidth', 1.5);
    
    % --- 寻找主峰并绘制向下的垂直虚线(引下线) ---
    [max_val, max_idx] = max(y_trans);
    peak_x = x_pm(max_idx);
    
    % **关键改变3**：修复引下线坐标（波长X, 模式Y, 高度Z）
    plot3([peak_x, peak_x], [l_num, l_num], [0, max_val], ...
        ':', 'Color', [0.3 0.3 0.3], 'LineWidth', 1.2);
end

% --- 5. 视角与轴外观优化 (模仿顶刊参考图) ---
% 标签 (交换了 X 和 Y)
xlabel(sprintf('\\lambda - %.4fnm (pm)', base_lambda), 'FontSize', 14, 'Interpreter', 'tex');
ylabel('{\itl}', 'FontSize', 16, 'Interpreter', 'tex'); % 去掉 OAM mode 只留 l 并稍微放大一点
zlabel('Transmission', 'FontSize', 14, 'Interpreter', 'tex');

% 刻度
set(gca, 'ZTick', 0:0.25:1);
all_l = cellfun(@(x) x.l, data_list);
set(gca, 'YTick', min(all_l):1:max(all_l));

% 坐标轴范围
zlim([0 1.05]);
xlim([0 max(x_pm)]); 

% 网格线颜色与字体样式
set(gca, 'FontSize', 12, 'FontName', 'Times New Roman', 'GridAlpha', 0.25);
box on;

% --- 极其关键 --- 调整物理拉伸比例
% 将波长(X)拉长，模式(Y)深度压紧
pbaspect([2.5 1.5 0.8]); 

% 视图角度：仰角略低(约15度)，方位角(Azimuth)转动使 X 轴为横向底边长轴
camproj('perspective'); 
view(9.9215, 31.2759); 

hold off;
fprintf('绘图完成！\n');

% --- 6. 导出高质量 PDF ---
output_pdf = 'transmission_3d_plot.pdf';
fprintf('正在导出高质量 PDF 到当前文件夹: %s ...\n', output_pdf);
% 使用 exportgraphics 导出高质量矢量图，自动裁剪白边 (需要 MATLAB R2020a 或更高版本)
exportgraphics(fig, output_pdf, 'ContentType', 'vector', 'BackgroundColor', 'none');
fprintf('PDF 保存成功！\n');