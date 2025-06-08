from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    session, url_for, jsonify
)
import os
from app.utils.health_parser import HealthDataParser
from app.utils.visualization import HealthDataVisualizer
import pandas as pd

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def initialize_parser():
    """初始化解析器并加载数据"""
    parser = HealthDataParser()
    
    # 检查是否有已解析的数据文件
    data_file_path = session.get('data_file_path')
    data_dir_path = session.get('data_dir_path')
    
    if data_file_path and os.path.exists(data_file_path):
        # 如果有XML文件路径，直接解析
        if not parser.parse_xml(data_file_path):
            raise Exception("加载数据文件时出错")
    elif data_dir_path and os.path.exists(data_dir_path):
        # 如果有目录路径，解析整个目录
        if not parser.parse_directory(data_dir_path):
            raise Exception("加载数据目录时出错")
    else:
        # 如果没有可用数据
        return None
    
    return parser

@bp.route('', methods=('GET',))
def index():
    """显示健康数据仪表板"""
    
    # 检查是否有已解析的数据文件或目录
    data_file_path = session.get('data_file_path')
    data_dir_path = session.get('data_dir_path')
    
    if not data_file_path and not data_dir_path:
        # 如果没有已解析的数据，显示首页
        return render_template('index.html', has_data=False)
    
    try:
        # 初始化解析器并加载数据
        parser = initialize_parser()
        if not parser:
            flash('找不到有效的健康数据')
            return render_template('index.html', has_data=False)
        
        # 初始化可视化器
        visualizer = HealthDataVisualizer(parser)
        
        # 获取数据统计
        stats = {}
        
        # 获取心率统计
        heart_rate_stats = parser.get_heart_rate_stats()
        if heart_rate_stats:
            stats['heart_rate'] = heart_rate_stats
        
        # 获取步数数据
        daily_steps = parser.get_daily_step_count()
        if not daily_steps.empty:
            # 确保步数列是数值类型，处理缺失值
            daily_steps['步数'] = pd.to_numeric(daily_steps['步数'], errors='coerce')
            # 删除无效数据
            daily_steps = daily_steps.dropna(subset=['步数'])
            
            if not daily_steps.empty:
                total_steps = float(daily_steps['步数'].sum())
                avg_steps = float(daily_steps['步数'].mean())
                # 四舍五入到整数
                stats['steps'] = {
                    '总步数': round(total_steps, 0),
                    '平均每日步数': round(avg_steps, 0)
                }
        
        # 获取睡眠数据
        sleep_data = parser.get_sleep_duration_daily()
        if not sleep_data.empty:
            # 确保睡眠时长列是数值类型，处理缺失值
            sleep_data['睡眠时长(小时)'] = pd.to_numeric(sleep_data['睡眠时长(小时)'], errors='coerce')
            # 删除无效数据
            sleep_data = sleep_data.dropna(subset=['睡眠时长(小时)'])
            
            if not sleep_data.empty:
                avg_sleep = float(sleep_data['睡眠时长(小时)'].mean())
                # 四舍五入到1位小数
                stats['sleep'] = {
                    '平均睡眠时长': round(avg_sleep, 1)
                }
        
        # 获取心电图数据
        ecg_data = parser.get_ecg_data()
        if not ecg_data.empty:
            ecg_count = len(ecg_data)
            stats['ecg'] = {
                'ECG记录数': ecg_count
            }
        
        # 获取压力指标数据
        stress_data = parser.get_stress_indicators()
        if not stress_data.empty and '压力指数' in stress_data.columns:
            # 确保压力指数列是数值类型，处理缺失值
            stress_data['压力指数'] = pd.to_numeric(stress_data['压力指数'], errors='coerce')
            # 删除无效数据
            stress_data = stress_data.dropna(subset=['压力指数'])
            
            if not stress_data.empty:
                avg_stress = float(stress_data['压力指数'].mean())
                # 四舍五入到1位小数
                stats['stress'] = {
                    '平均压力指数': round(avg_stress, 1)
                }
        
        # 创建仪表板图表
        dashboard_chart = visualizer.create_health_dashboard()
        
        # 获取所有可用的数据类型
        data_types = parser.get_all_data_types()
        
        # 清理解析器
        parser.clean_up()
        
        return render_template(
            'dashboard.html', 
            has_data=True,
            stats=stats,
            dashboard_chart=dashboard_chart,
            data_types=data_types
        )
    
    except Exception as e:
        flash(f'生成仪表板时出错: {str(e)}')
        return render_template('index.html', has_data=False)

@bp.route('/clear', methods=('GET',))
def clear_data():
    """清除会话中的数据"""
    session.pop('data_file_path', None)
    session.pop('data_dir_path', None)
    flash('数据已清除')
    return redirect(url_for('dashboard.index'))

@bp.route('/chart/<chart_type>', methods=('GET',))
def get_chart(chart_type):
    """获取指定类型的图表"""
    try:
        parser = initialize_parser()
        if not parser:
            return {"error": "没有可用的数据"}
        
        visualizer = HealthDataVisualizer(parser)
        
        if chart_type == 'heart_rate':
            chart = visualizer.plot_heart_rate_over_time()
            return chart if chart else {"error": "暂无心率数据"}
        elif chart_type == 'steps':
            chart = visualizer.plot_daily_steps()
            return chart if chart else {"error": "暂无步数数据"}
        elif chart_type == 'sleep':
            chart = visualizer.plot_sleep_duration()
            return chart if chart else {"error": "暂无睡眠数据"}
        elif chart_type == 'stress':
            # 获取压力指标图表
            stress_data = parser.get_stress_indicators()
            if stress_data.empty or '压力指数' not in stress_data.columns:
                return {"error": "暂无压力数据"}
            chart = visualizer.plot_stress_indicators()
            return chart if chart else {"error": "暂无压力数据"}
        elif chart_type == 'ecg':
            # 获取ECG数据并传入plot_ecg_summary方法
            ecg_data = parser.get_ecg_data()
            if ecg_data.empty:
                return {"error": "暂无心电图数据"}
            chart = visualizer.plot_ecg_summary(ecg_data)
            return chart if chart else {"error": "暂无心电图数据"}
        elif chart_type == 'dashboard':
            chart = visualizer.create_health_dashboard()
            return chart
        else:
            return {"error": "无效的图表类型"}
    except Exception as e:
        print(f"获取图表时出错: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)} 