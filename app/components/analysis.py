from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    session, url_for, jsonify
)
from app.utils.health_parser import HealthDataParser
import pandas as pd
import json
import os
from app.components.dashboard import initialize_parser
import numpy as np
import traceback

bp = Blueprint('analysis', __name__, url_prefix='/analysis')

@bp.route('', methods=('GET',))
def index():
    """显示健康数据分析选项"""
    
    # 检查是否有已解析的数据文件
    data_file_path = session.get('data_file_path')
    data_dir_path = session.get('data_dir_path')
    
    if not data_file_path and not data_dir_path:
        # 如果没有已解析的数据，重定向到上传页面
        flash('请先上传健康数据文件')
        return redirect(url_for('upload.upload_file'))
    
    try:
        # 初始化解析器并加载数据
        parser = initialize_parser()
        if not parser:
            flash('加载数据文件时出错')
            return redirect(url_for('upload.upload_file'))
        
        # 获取所有可用的数据类型
        data_types = parser.get_all_data_types()
        
        # 获取一些基本统计数据
        stats = {}
        
        # 获取心率统计
        heart_rate_stats = parser.get_heart_rate_stats()
        if heart_rate_stats:
            stats['heart_rate'] = heart_rate_stats
        
        # 获取步数数据
        daily_steps = parser.get_daily_step_count()
        if not daily_steps.empty:
            stats['steps'] = {
                '总步数': daily_steps['步数'].sum(),
                '平均每日步数': daily_steps['步数'].mean(),
                '最高步数': daily_steps['步数'].max(),
                '最低步数': daily_steps['步数'].min()
            }
        
        # 获取睡眠数据
        sleep_data = parser.get_sleep_duration_daily()
        if not sleep_data.empty:
            stats['sleep'] = {
                '平均睡眠时长': sleep_data['睡眠时长(小时)'].mean(),
                '最长睡眠时长': sleep_data['睡眠时长(小时)'].max(),
                '最短睡眠时长': sleep_data['睡眠时长(小时)'].min()
            }
        
        # 获取心电图数据
        ecg_data = parser.get_ecg_data()
        if not ecg_data.empty:
            stats['ecg'] = {
                'ECG记录数': len(ecg_data)
            }
        
        # 清理解析器
        parser.clean_up()
        
        return render_template(
            'analysis.html', 
            data_types=data_types,
            stats=stats
        )
    
    except Exception as e:
        flash(f'加载分析页面时出错: {str(e)}')
        return redirect(url_for('upload.upload_file'))

@bp.route('/data/<data_type>', methods=('GET',))
def get_data(data_type):
    """获取特定类型的健康数据"""
    
    try:
        # 初始化解析器
        parser = initialize_parser()
        if not parser:
            return jsonify({'error': '没有可用的数据'}), 400
        
        # 获取指定类型的数据
        data = parser.get_data_by_type(data_type)
        
        # 如果没有数据，返回错误
        if data.empty:
            parser.clean_up()
            return jsonify({'error': f'没有{data_type}类型的数据'}), 404
        
        # 将数据转换为JSON
        # 注意：需要处理日期时间格式
        data_json = json.loads(data.to_json(orient='records', date_format='iso'))
        
        # 清理解析器
        parser.clean_up()
        
        return jsonify({
            'data': data_json,
            'count': len(data_json)
        })
    
    except Exception as e:
        return jsonify({'error': f'获取数据时出错: {str(e)}'}), 500

@bp.route('/correlation', methods=('GET',))
def correlation_analysis():
    """执行相关性分析"""
    
    # 获取请求参数
    type1 = request.args.get('type1')
    type2 = request.args.get('type2')
    
    if not type1 or not type2:
        return jsonify({'error': '必须指定两种数据类型进行相关性分析'}), 400
    
    try:
        # 初始化解析器
        parser = initialize_parser()
        if not parser:
            return jsonify({'error': '没有可用的数据'}), 400
        
        # 获取两种类型的数据
        data1 = parser.get_data_by_type(type1)
        data2 = parser.get_data_by_type(type2)
        
        # 如果任一类型没有数据，返回错误
        if data1.empty or data2.empty:
            parser.clean_up()
            return jsonify({'error': '指定的数据类型之一没有数据'}), 404
        
        # 为简化分析，我们按日期对数据进行分组并计算每日平均值
        # 确保日期列存在
        date_cols1 = [col for col in data1.columns if col.lower() in ['startdate', 'date', '日期', 'start']]
        date_cols2 = [col for col in data2.columns if col.lower() in ['startdate', 'date', '日期', 'start']]
        
        if not date_cols1 or not date_cols2:
            parser.clean_up()
            return jsonify({'error': '数据缺少有效的日期列'}), 400
            
        # 提取日期列
        date_col1 = date_cols1[0]
        date_col2 = date_cols2[0]
        
        # 确保日期列是日期类型
        data1[date_col1] = pd.to_datetime(data1[date_col1], errors='coerce')
        data2[date_col2] = pd.to_datetime(data2[date_col2], errors='coerce')
        
        # 提取日期部分
        data1['date'] = data1[date_col1].dt.date
        data2['date'] = data2[date_col2].dt.date
        
        # 提取值列
        value_cols1 = [col for col in data1.columns if col.lower() in ['value', 'values', '值', '数值']]
        value_cols2 = [col for col in data2.columns if col.lower() in ['value', 'values', '值', '数值']]
        
        if not value_cols1 or not value_cols2:
            parser.clean_up()
            return jsonify({'error': '数据缺少有效的值列'}), 400
            
        # 提取值列
        value_col1 = value_cols1[0]
        value_col2 = value_cols2[0]
        
        # 确保value列是数值类型
        data1[value_col1] = pd.to_numeric(data1[value_col1], errors='coerce')
        data2[value_col2] = pd.to_numeric(data2[value_col2], errors='coerce')
        
        # 过滤掉NaN值
        data1 = data1.dropna(subset=[value_col1, 'date'])
        data2 = data2.dropna(subset=[value_col2, 'date'])
        
        if data1.empty or data2.empty:
            parser.clean_up()
            return jsonify({'error': '清洗后数据为空，无法进行分析'}), 404
        
        # 计算每日平均值
        daily_data1 = data1.groupby('date')[value_col1].mean().reset_index()
        daily_data2 = data2.groupby('date')[value_col2].mean().reset_index()
        
        # 合并两个数据集
        merged_data = pd.merge(daily_data1, daily_data2, on='date', suffixes=('_1', '_2'))
        
        # 再次确保数据有效
        merged_data = merged_data.dropna()
        
        # 如果没有重叠的日期或数据过少，返回错误
        if merged_data.empty or len(merged_data) < 3:
            parser.clean_up()
            return jsonify({'error': '有效数据不足（少于3个点），无法进行相关性分析'}), 404
        
        try:
            # 检查数据是否包含无限值
            merged_data = merged_data.replace([np.inf, -np.inf], np.nan).dropna()
            
            if merged_data.empty or len(merged_data) < 3:
                parser.clean_up()
                return jsonify({'error': '清洗无限值后数据不足，无法进行分析'}), 404
            
            # 计算皮尔逊相关系数
            correlation = merged_data[f'{value_col1}_1'].corr(merged_data[f'{value_col2}_2'])
            
            if pd.isna(correlation):
                parser.clean_up()
                return jsonify({'error': '无法计算相关系数（可能数据无变化或包含特殊值）'}), 400
            
            # 计算斯皮尔曼相关系数（非参数）
            spearman_corr = merged_data[f'{value_col1}_1'].corr(merged_data[f'{value_col2}_2'], method='spearman')
            
            # 计算协方差
            covariance = merged_data[f'{value_col1}_1'].cov(merged_data[f'{value_col2}_2'])
            
            # 线性回归拟合
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                merged_data[f'{value_col1}_1'], 
                merged_data[f'{value_col2}_2']
            )
            
            # 检验正态性
            normal_test1 = None
            normal_test2 = None
            normal_test_pvalue1 = None
            normal_test_pvalue2 = None
            
            if len(merged_data) >= 8:  # 最小样本量要求
                try:
                    # shapiro-wilk 正态检验
                    normal_test1, normal_test_pvalue1 = stats.shapiro(merged_data[f'{value_col1}_1'])
                    normal_test2, normal_test_pvalue2 = stats.shapiro(merged_data[f'{value_col2}_2'])
                except:
                    pass  # 如果正态检验失败，保持为None
            
            # 准备散点图数据
            scatter_data = []
            for _, row in merged_data.iterrows():
                scatter_data.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'value_1': float(row[f'{value_col1}_1']),
                    'value_2': float(row[f'{value_col2}_2'])
                })
            
            # 生成相关系数分析提示
            corr_interpretation = ""
            if abs(correlation) < 0.1:
                corr_interpretation = "两个变量基本无相关性"
            elif abs(correlation) < 0.3:
                corr_interpretation = "两个变量呈弱相关性"
            elif abs(correlation) < 0.5:
                corr_interpretation = "两个变量呈中度相关性"
            elif abs(correlation) < 0.7:
                corr_interpretation = "两个变量呈强相关性"
            else:
                corr_interpretation = "两个变量呈极强相关性"
                
            if correlation > 0:
                corr_interpretation += "（正相关）"
            else:
                corr_interpretation += "（负相关）"
            
            # 计算R方（决定系数）
            r_squared = r_value ** 2
            
            # 生成更详细的线性回归解释
            linear_interpretation = ""
            if p_value < 0.05:
                linear_interpretation = f"这是一个统计学上显著的关系，有 {round(r_squared * 100, 2)}% 的 {type2} 变化可以通过 {type1} 解释。"
                if correlation > 0:
                    linear_interpretation += f" 每增加一个单位的 {type1}，{type2} 平均增加 {round(float(slope), 4)} 个单位。"
                else:
                    linear_interpretation += f" 每增加一个单位的 {type1}，{type2} 平均减少 {abs(round(float(slope), 4))} 个单位。"
            else:
                linear_interpretation = f"这种关系在统计学上不显著，无法确定 {type1} 对 {type2} 有预测作用。"
            
            # 添加健康相关解释
            health_interpretation = ""
            if type1 == "HKQuantityTypeIdentifierStepCount" and type2 == "HKQuantityTypeIdentifierHeartRate":
                if correlation > 0.3:
                    health_interpretation = "步数与心率的正相关表明身体活动量增加导致心率上升，这是正常的生理反应。"
                elif correlation < -0.3:
                    health_interpretation = "步数与心率的负相关可能表明心肺适应能力较好，或数据存在时间不匹配问题。"
            elif (type1 == "HKQuantityTypeIdentifierStepCount" and type2 == "HKQuantityTypeIdentifierRestingHeartRate") or \
                 (type2 == "HKQuantityTypeIdentifierStepCount" and type1 == "HKQuantityTypeIdentifierRestingHeartRate"):
                if correlation < -0.3:
                    health_interpretation = "步数增加与静息心率下降的负相关关系表明规律运动可能改善了心血管健康，这是一个积极信号。"
            elif (type1 == "HKQuantityTypeIdentifierSleepAnalysis" and type2 == "HKQuantityTypeIdentifierStepCount") or \
                 (type2 == "HKQuantityTypeIdentifierSleepAnalysis" and type1 == "HKQuantityTypeIdentifierStepCount"):
                if correlation > 0.3:
                    health_interpretation = "睡眠时长与步数的正相关表明充足的睡眠可能有助于提高日间活动水平。"
            
            # 根据数据分布提供方法建议
            method_suggestion = ""
            if (normal_test_pvalue1 is not None and normal_test_pvalue1 <= 0.05) or \
               (normal_test_pvalue2 is not None and normal_test_pvalue2 <= 0.05):
                method_suggestion = "由于至少一个变量不符合正态分布，斯皮尔曼相关系数(值为" + str(round(float(spearman_corr), 4)) + ")可能比皮尔逊相关系数更适合描述这种关系。"
            
            # 生成完整分析结果
            analysis_result = {
                'correlation': round(float(correlation), 4),
                'spearman_correlation': round(float(spearman_corr), 4) if not pd.isna(spearman_corr) else None,
                'covariance': round(float(covariance), 4) if not pd.isna(covariance) else None,
                'linear_regression': {
                    'slope': round(float(slope), 4) if not pd.isna(slope) else None,
                    'intercept': round(float(intercept), 4) if not pd.isna(intercept) else None,
                    'r_value': round(float(r_value), 4) if not pd.isna(r_value) else None,
                    'p_value': round(float(p_value), 4) if not pd.isna(p_value) else None,
                    'std_err': round(float(std_err), 4) if not pd.isna(std_err) else None,
                    'r_squared': round(float(r_squared), 4) if not pd.isna(r_value) else None
                },
                'normality_test': {
                    'variable1': {
                        'statistic': round(float(normal_test1), 4) if normal_test1 is not None else None,
                        'p_value': round(float(normal_test_pvalue1), 4) if normal_test_pvalue1 is not None else None,
                        'is_normal': bool(normal_test_pvalue1 > 0.05) if normal_test_pvalue1 is not None else None
                    },
                    'variable2': {
                        'statistic': round(float(normal_test2), 4) if normal_test2 is not None else None,
                        'p_value': round(float(normal_test_pvalue2), 4) if normal_test_pvalue2 is not None else None,
                        'is_normal': bool(normal_test_pvalue2 > 0.05) if normal_test_pvalue2 is not None else None
                    }
                },
                'type1': type1,
                'type2': type2,
                'data': scatter_data,
                'count': int(len(scatter_data)),
                'summary': f"相关系数为 {round(float(correlation), 4)}，{corr_interpretation}。值域为 -1~1，越接近 ±1 说明关系越强，接近 0 表示关系弱或无关。" + 
                           (f" {health_interpretation}" if health_interpretation else "") + 
                           (f" {method_suggestion}" if method_suggestion else ""),
                'linear_summary': f"线性关系：y = {round(float(slope), 4)}x + {round(float(intercept), 4)}，p值 = {round(float(p_value), 4)}" + 
                                 (f"，具有统计学显著性。{linear_interpretation}" if bool(p_value < 0.05) else f"，不具有统计学显著性。{linear_interpretation}")
            }
            
            # 添加基本描述统计结果
            analysis_result['descriptive_stats'] = {
                'variable1': {
                    'mean': round(float(merged_data[f'{value_col1}_1'].mean()), 4),
                    'median': round(float(merged_data[f'{value_col1}_1'].median()), 4),
                    'std': round(float(merged_data[f'{value_col1}_1'].std()), 4),
                    'min': round(float(merged_data[f'{value_col1}_1'].min()), 4),
                    'max': round(float(merged_data[f'{value_col1}_1'].max()), 4),
                },
                'variable2': {
                    'mean': round(float(merged_data[f'{value_col2}_2'].mean()), 4),
                    'median': round(float(merged_data[f'{value_col2}_2'].median()), 4),
                    'std': round(float(merged_data[f'{value_col2}_2'].std()), 4),
                    'min': round(float(merged_data[f'{value_col2}_2'].min()), 4),
                    'max': round(float(merged_data[f'{value_col2}_2'].max()), 4),
                }
            }
            
            # 清理解析器
            parser.clean_up()
            
            return jsonify(analysis_result)
            
        except Exception as analysis_error:
            parser.clean_up()
            print(f"相关性分析计算出错: {str(analysis_error)}")
            traceback.print_exc()
            return jsonify({'error': f'相关性分析计算出错: {str(analysis_error)}'}), 500
    
    except Exception as e:
        print(f"执行相关性分析时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'执行相关性分析时出错: {str(e)}'}), 500

@bp.route('/summary', methods=('GET',))
def health_summary():
    """显示用户健康数据摘要"""
    try:
        # 检查健康数据
        data_file_path = session.get('data_file_path')
        data_dir_path = session.get('data_dir_path')
        
        if not data_file_path and not data_dir_path:
            flash('没有可用的健康数据，请先上传健康数据')
            return redirect(url_for('upload.upload_file'))
        
        # 初始化解析器并加载数据
        parser = initialize_parser()
        if not parser:
            flash('加载数据文件时出错')
            return redirect(url_for('upload.upload_file'))
        
        # 收集各类健康数据
        summary = {}
        
        # 心率数据
        heart_rate_data = parser.get_heart_rate_data()
        if not heart_rate_data.empty:
            # 确保数值列是数值类型
            heart_rate_data['value'] = pd.to_numeric(heart_rate_data['value'], errors='coerce')
            # 过滤掉NaN值
            heart_rate_data = heart_rate_data.dropna(subset=['value'])
            
            if not heart_rate_data.empty:
                mean_hr = float(heart_rate_data['value'].mean())
                max_hr = float(heart_rate_data['value'].max())
                min_hr = float(heart_rate_data['value'].min())
                
                hr_status = "正常"
                if mean_hr > 100:
                    hr_status = "偏高"
                elif mean_hr < 60:
                    hr_status = "偏低"
                
                summary['heart_rate'] = {
                    'average': mean_hr,
                    'max': max_hr,
                    'min': min_hr,
                    'status': hr_status
                }
        
        # 步数数据
        steps_data = parser.get_daily_step_count()
        if not steps_data.empty:
            # 确保数值列是数值类型
            steps_data['步数'] = pd.to_numeric(steps_data['步数'], errors='coerce')
            # 过滤掉NaN值
            steps_data = steps_data.dropna(subset=['步数'])
            
            if not steps_data.empty:
                avg_steps = float(steps_data['步数'].mean())
                
                activity_level = "低活动量"
                if avg_steps >= 10000:
                    activity_level = "高活动量"
                elif avg_steps >= 7500:
                    activity_level = "中高活动量"
                elif avg_steps >= 5000:
                    activity_level = "中等活动量"
                
                summary['steps'] = {
                    'average': avg_steps,
                    'activity_level': activity_level
                }
        
        # 睡眠数据
        sleep_data = parser.get_sleep_duration_daily()
        if not sleep_data.empty:
            # 确保数值列是数值类型
            sleep_data['睡眠时长(小时)'] = pd.to_numeric(sleep_data['睡眠时长(小时)'], errors='coerce')
            # 过滤掉NaN值
            sleep_data = sleep_data.dropna(subset=['睡眠时长(小时)'])
            
            if not sleep_data.empty:
                avg_sleep = float(sleep_data['睡眠时长(小时)'].mean())
                
                sleep_status = "正常"
                if avg_sleep < 6:
                    sleep_status = "睡眠不足"
                elif avg_sleep > 9:
                    sleep_status = "睡眠过多"
                
                summary['sleep'] = {
                    'average': avg_sleep,
                    'status': sleep_status
                }
        
        # 压力指标
        stress_data = parser.get_stress_indicators()
        if not stress_data.empty:
            # 确保压力指数列是数值类型
            if '压力指数' in stress_data.columns:
                stress_data['压力指数'] = pd.to_numeric(stress_data['压力指数'], errors='coerce')
                # 过滤掉NaN值
                stress_data = stress_data.dropna(subset=['压力指数'])
                
                if not stress_data.empty:
                    avg_stress = float(stress_data['压力指数'].mean())
                    
                    stress_level = "中等压力"
                    if avg_stress > 10:
                        stress_level = "高压力"
                    elif avg_stress < 5:
                        stress_level = "低压力"
                    
                    summary['stress'] = {
                        'average': avg_stress,
                        'level': stress_level
                    }
        
        # 心电图数据
        ecg_data = parser.get_ecg_data()
        if not ecg_data.empty:
            summary['ecg'] = {
                'count': int(len(ecg_data)),
                'status': '已记录'
            }
        
        # 清理解析器
        parser.clean_up()
        
        return render_template('summary.html', summary=summary)
    
    except Exception as e:
        flash(f'生成健康摘要时出错: {str(e)}')
        return redirect(url_for('dashboard.index')) 