import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import traceback
import datetime

class HealthDataVisualizer:
    """Apple健康数据可视化类"""
    
    def __init__(self, parser):
        """
        初始化可视化器
        
        参数:
            parser: HealthDataParser实例，用于获取健康数据
        """
        self.parser = parser
    
    def plot_daily_steps(self):
        """绘制每日步数图表"""
        daily_steps = self.parser.get_daily_step_count()
        if daily_steps.empty:
            return None
        
        fig = px.bar(
            daily_steps, 
            x='日期', 
            y='步数',
            title='每日步数',
            labels={'日期': '日期', '步数': '步数'},
            color_discrete_sequence=['#1f77b4']
        )
        
        # 添加平均线
        avg_steps = daily_steps['步数'].mean()
        fig.add_hline(
            y=avg_steps,
            line_dash="dash",
            line_color="red",
            annotation_text=f"平均: {avg_steps:.0f}步",
            annotation_position="top right"
        )
        
        # 设置布局
        fig.update_layout(
            xaxis_title='日期',
            yaxis_title='步数',
            hovermode='x unified',
            height=400
        )
        
        return json.loads(fig.to_json())
    
    def plot_heart_rate_over_time(self):
        """绘制心率随时间变化图表"""
        hr_data = self.parser.get_heart_rate_data()
        if hr_data.empty:
            return None
        
        # 确保value列是数值类型
        hr_data['value'] = pd.to_numeric(hr_data['value'], errors='coerce')
        
        # 重采样为小时数据点以减少数据量
        hr_data.set_index('startDate', inplace=True)
        hr_hourly = hr_data.resample('H').mean().reset_index()
        
        # 创建图表
        fig = px.line(
            hr_hourly, 
            x='startDate', 
            y='value',
            title='心率变化趋势',
            labels={'startDate': '时间', 'value': '心率 (bpm)'},
            color_discrete_sequence=['#ff7f0e']
        )
        
        # 添加心率区间
        fig.add_hrect(
            y0=100, y1=max(hr_hourly['value'].max(), 100),
            fillcolor="red", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="高心率区间",
            annotation_position="top right"
        )
        
        fig.add_hrect(
            y0=60, y1=100,
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="正常心率区间",
            annotation_position="top left"
        )
        
        fig.add_hrect(
            y0=min(hr_hourly['value'].min(), 60), y1=60,
            fillcolor="blue", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="低心率区间",
            annotation_position="bottom left"
        )
        
        # 设置布局
        fig.update_layout(
            xaxis_title='时间',
            yaxis_title='心率 (bpm)',
            hovermode='x unified',
            height=400
        )
        
        return json.loads(fig.to_json())
    
    def plot_sleep_duration(self):
        """绘制睡眠时长图表"""
        sleep_data = self.parser.get_sleep_duration_daily()
        if sleep_data.empty:
            return None
        
        # 创建图表
        fig = px.bar(
            sleep_data, 
            x='日期', 
            y='睡眠时长(小时)',
            title='每日睡眠时长',
            labels={'日期': '日期', '睡眠时长(小时)': '睡眠时长 (小时)'},
            color_discrete_sequence=['#2ca02c']
        )
        
        # 添加推荐睡眠时长线
        fig.add_hline(
            y=8,
            line_dash="dash",
            line_color="red",
            annotation_text="推荐睡眠时长: 8小时",
            annotation_position="top right"
        )
        
        # 设置布局
        fig.update_layout(
            xaxis_title='日期',
            yaxis_title='睡眠时长 (小时)',
            hovermode='x unified',
            height=400
        )
        
        return json.loads(fig.to_json())
    
    def plot_stress_indicators(self):
        """绘制压力指标图表"""
        stress_data = self.parser.get_stress_indicators()
        if stress_data.empty:
            return None
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("心率波动 (压力指标)", "每日压力指数"),
            vertical_spacing=0.15
        )
        
        # 添加心率波动图
        fig.add_trace(
            go.Scatter(
                x=stress_data['日期'], 
                y=stress_data['心率波动'],
                mode='lines+markers',
                name='心率波动',
                line=dict(color='#d62728')
            ),
            row=1, col=1
        )
        
        # 添加压力指数图
        fig.add_trace(
            go.Bar(
                x=stress_data['日期'], 
                y=stress_data['压力指数'],
                name='压力指数',
                marker_color='#9467bd'
            ),
            row=2, col=1
        )
        
        # 设置布局
        fig.update_layout(
            height=600,
            hovermode='x unified',
            showlegend=False
        )
        
        fig.update_xaxes(title_text='日期', row=2, col=1)
        fig.update_yaxes(title_text='心率标准差', row=1, col=1)
        fig.update_yaxes(title_text='压力指数', row=2, col=1)
        
        return json.loads(fig.to_json())
    
    def create_health_dashboard(self, days=30):
        """创建健康数据仪表板"""
        try:
            print(f"开始创建健康仪表板...")
            
            # 获取步数数据
            steps_data = self.parser.get_step_count_data()
            print(f"步数数据类型: {type(steps_data)}")
            if not steps_data.empty:
                print(f"步数数据列: {steps_data.columns.tolist()}")
                print(f"步数value列类型: {type(steps_data['value'].iloc[0]) if 'value' in steps_data.columns and not steps_data.empty else 'N/A'}")
            
            steps_df = self._prepare_steps_chart_data(steps_data, days)
            
            # 获取心率数据
            heart_rate_data = self.parser.get_heart_rate_data()
            print(f"心率数据类型: {type(heart_rate_data)}")
            if not heart_rate_data.empty:
                print(f"心率数据列: {heart_rate_data.columns.tolist()}")
                print(f"心率value列类型: {type(heart_rate_data['value'].iloc[0]) if 'value' in heart_rate_data.columns and not heart_rate_data.empty else 'N/A'}")
            
            hr_df = self._prepare_heart_rate_chart_data(heart_rate_data, days)
            print(f"处理后的心率数据类型: {type(hr_df)}")
            if not hr_df.empty:
                print(f"处理后的心率数据列: {hr_df.columns.tolist()}")
                print(f"处理后心率value列类型: {type(hr_df['value'].iloc[0]) if 'value' in hr_df.columns and not hr_df.empty else 'N/A'}")
            
            # 获取睡眠数据
            sleep_data = self.parser.get_sleep_analysis_data()
            print(f"睡眠数据类型: {type(sleep_data)}")
            if not sleep_data.empty:
                print(f"睡眠数据列: {sleep_data.columns.tolist()}")
                if 'duration' in sleep_data.columns:
                    print(f"睡眠duration列类型: {type(sleep_data['duration'].iloc[0])}")
            
            # 直接使用duration列，duration列已经在sleep_analysis_data方法中计算好了
            if not sleep_data.empty and 'duration' in sleep_data.columns:
                sleep_df = self._prepare_sleep_chart_data(sleep_data, days)
                print(f"处理后的睡眠数据类型: {type(sleep_df)}")
                if not sleep_df.empty:
                    print(f"处理后的睡眠数据列: {sleep_df.columns.tolist()}")
                    print(f"处理后睡眠duration列类型: {type(sleep_df['duration'].iloc[0]) if 'duration' in sleep_df.columns and not sleep_df.empty else 'N/A'}")
            else:
                sleep_df = pd.DataFrame()
            
            # 获取ECG数据
            ecg_data = self.parser.get_ecg_data()
            print(f"ECG数据类型: {type(ecg_data)}")
            if not ecg_data.empty:
                print(f"ECG数据列: {ecg_data.columns.tolist()}")
            
            ecg_df = self._prepare_ecg_chart_data(ecg_data, days)
            
            # 准备返回的完整图表数据
            chart_data = {}
            has_any_data = False
            
            # 创建各个图表并存储
            try:
                print(f"创建步数图表...")
                steps_chart = None
                if not steps_df.empty:
                    steps_chart = self._create_steps_chart(steps_df)
                    if steps_chart and 'data' in steps_chart and len(steps_chart['data']) > 0:
                        chart_data['steps'] = steps_chart
                        has_any_data = True
                        print(f"步数图表创建成功，包含 {len(steps_chart['data'])} 个trace")
                    else:
                        print(f"步数图表创建失败或无有效数据")
                else:
                    print(f"步数数据为空，跳过图表创建")
            except Exception as e:
                print(f"创建步数图表时出错: {str(e)}")
                traceback.print_exc()

            try:
                print(f"创建心率图表...")
                hr_chart = None
                if not hr_df.empty:
                    hr_chart = self._create_heart_rate_chart(hr_df)
                    if hr_chart and 'data' in hr_chart and len(hr_chart['data']) > 0:
                        chart_data['heart_rate'] = hr_chart
                        has_any_data = True
                        print(f"心率图表创建成功，包含 {len(hr_chart['data'])} 个trace")
                    else:
                        print(f"心率图表创建失败或无有效数据")
                else:
                    print(f"心率数据为空，跳过图表创建")
            except Exception as e:
                print(f"创建心率图表时出错: {str(e)}")
                traceback.print_exc()

            try:
                print(f"创建睡眠图表...")
                sleep_chart = None
                if not sleep_df.empty and 'duration' in sleep_df.columns:
                    sleep_chart = self._create_sleep_chart(sleep_df)
                    if sleep_chart and 'data' in sleep_chart and len(sleep_chart['data']) > 0:
                        chart_data['sleep'] = sleep_chart
                        has_any_data = True
                        print(f"睡眠图表创建成功，包含 {len(sleep_chart['data'])} 个trace")
                    else:
                        print(f"睡眠图表创建失败或无有效数据")
                else:
                    print(f"睡眠数据为空或缺少duration列，跳过图表创建")
            except Exception as e:
                print(f"创建睡眠图表时出错: {str(e)}")
                traceback.print_exc()

            try:
                print(f"创建ECG图表...")
                ecg_chart = None
                if not ecg_df.empty:
                    ecg_chart = self._create_ecg_chart(ecg_df)
                    if ecg_chart and 'data' in ecg_chart and len(ecg_chart['data']) > 0:
                        chart_data['ecg'] = ecg_chart
                        has_any_data = True
                        print(f"ECG图表创建成功，包含 {len(ecg_chart['data'])} 个trace")
                    else:
                        print(f"ECG图表创建失败或无有效数据")
                else:
                    print(f"ECG数据为空，跳过图表创建")
            except Exception as e:
                print(f"创建ECG图表时出错: {str(e)}")
                traceback.print_exc()

            # 检查是否有任何有效图表
            if not has_any_data:
                print(f"没有任何有效数据可用于创建仪表板")
                # 创建一个默认的空仪表板，但带有提示信息
                empty_chart = {
                    "data": [
                        {
                            "type": "scatter",
                            "x": [],
                            "y": [],
                            "mode": "text",
                            "text": ["暂无健康数据"],
                            "textposition": "middle center"
                        }
                    ],
                    "layout": {
                        "title": {"text": "暂无可用的健康数据"},
                        "height": 500,
                        "xaxis": {"visible": False},
                        "yaxis": {"visible": False}
                    }
                }
                return empty_chart
            
            # 创建一个综合仪表板
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "每日步数" if 'steps' in chart_data else "",
                    "心率变化" if 'heart_rate' in chart_data else "",
                    "睡眠时长" if 'sleep' in chart_data else "",
                    "ECG记录" if 'ecg' in chart_data else ""
                ),
                specs=[
                    [{"type": "scatter"}, {"type": "scatter"}],
                    [{"type": "scatter"}, {"type": "scatter"}]
                ],
                vertical_spacing=0.12,
                horizontal_spacing=0.07
            )
            
            # 填充仪表板
            trace_count = 0
            
            # 添加步数图表
            if 'steps' in chart_data and 'data' in chart_data['steps']:
                for trace in chart_data['steps']['data']:
                    if trace:
                        fig.add_trace(trace, row=1, col=1)
                        trace_count += 1
                        
            # 添加心率图表
            if 'heart_rate' in chart_data and 'data' in chart_data['heart_rate']:
                for trace in chart_data['heart_rate']['data']:
                    if trace:
                        fig.add_trace(trace, row=1, col=2)
                        trace_count += 1
                        
            # 添加睡眠图表
            if 'sleep' in chart_data and 'data' in chart_data['sleep']:
                for trace in chart_data['sleep']['data']:
                    if trace:
                        fig.add_trace(trace, row=2, col=1)
                        trace_count += 1
                        
            # 添加ECG图表
            if 'ecg' in chart_data and 'data' in chart_data['ecg']:
                # 检查ECG图表中的饼图，需要特殊处理
                for i, trace in enumerate(chart_data['ecg']['data']):
                    if trace:
                        if 'type' in trace and trace['type'] == 'pie':
                            # 饼图需要特殊处理，这里简化为条形图
                            labels = trace.get('labels', [])
                            values = trace.get('values', [])
                            if labels and values:
                                bar_trace = go.Bar(
                                    x=labels,
                                    y=values,
                                    name="ECG分类"
                                )
                                fig.add_trace(bar_trace, row=2, col=2)
                                trace_count += 1
                        else:
                            fig.add_trace(trace, row=2, col=2)
                            trace_count += 1
            
            # 设置布局
            fig.update_layout(
                title_text="健康数据摘要",
                height=800,
                showlegend=False
            )
            
            print(f"综合仪表板创建完成，共添加了 {trace_count} 个trace")
            
            # 检查是否有任何trace被添加
            if trace_count == 0:
                print(f"警告：仪表板中没有添加任何trace")
                # 创建一个默认的空仪表板，但带有提示信息
                empty_chart = {
                    "data": [
                        {
                            "type": "scatter",
                            "x": [],
                            "y": [],
                            "mode": "text",
                            "text": ["暂无健康数据"],
                            "textposition": "middle center"
                        }
                    ],
                    "layout": {
                        "title": {"text": "暂无可用的健康数据"},
                        "height": 500,
                        "xaxis": {"visible": False},
                        "yaxis": {"visible": False}
                    }
                }
                return empty_chart
                
            dashboard_json = json.loads(fig.to_json())
            print(f"仪表板成功转换为JSON格式")
            return dashboard_json
            
        except Exception as e:
            print(f"创建健康仪表板时出错: {str(e)}")
            traceback.print_exc()
            # 返回错误信息
            return {
                "data": [
                    {
                        "type": "scatter",
                        "x": [],
                        "y": [],
                        "mode": "text",
                        "text": [f"创建仪表板时出错: {str(e)}"],
                        "textposition": "middle center"
                    }
                ],
                "layout": {
                    "title": {"text": "仪表板创建失败"},
                    "height": 500,
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False}
                }
            }
    
    def plot_ecg_summary(self, ecg_data):
        """绘制心电图数据摘要"""
        if ecg_data.empty:
            print("没有心电图数据可供绘制")
            return {"error": "暂无心电图数据"}

        try:
            # 检查必要的数据列
            date_col = None
            for col in ['date', 'startDate']:
                if col in ecg_data.columns:
                    date_col = col
                    break
                    
            if date_col is None:
                print("ECG数据缺少日期列")
                return {"error": "ECG数据格式不正确，缺少日期信息"}
            
            print(f"ECG数据列: {ecg_data.columns.tolist()}")
            print(f"ECG数据类型: {type(ecg_data)}")
            print(f"ECG数据行数: {len(ecg_data)}")
                
            # 创建一个多面板的图表布局
            fig = make_subplots(rows=2, cols=1, 
                              subplot_titles=("ECG记录数量", "ECG分类分布"),
                              specs=[[{"type": "xy"}], [{"type": "pie"}]],
                              row_heights=[0.6, 0.4],
                              vertical_spacing=0.1)
            
            # 确保日期列是datetime类型
            ecg_data[date_col] = pd.to_datetime(ecg_data[date_col], errors='coerce')
            # 删除NaT（无效日期）
            ecg_data = ecg_data.dropna(subset=[date_col])
            
            if ecg_data.empty:
                print("清理日期后ECG数据为空")
                return {"error": "ECG数据日期无效"}
                
            # 计算每天的记录数
            daily_counts = ecg_data.groupby(ecg_data[date_col].dt.date).size().reset_index()
            daily_counts.columns = ['date', 'count']
            
            # 确保count列是整数类型
            daily_counts['count'] = daily_counts['count'].astype(int)
            
            print(f"ECG每日记录数: {daily_counts['count'].tolist()}")
            
            # 确保有记录后再绘制图表
            if not daily_counts.empty:
                # 绘制每天的记录数量
                fig.add_trace(
                    go.Bar(
                        x=[str(d) for d in daily_counts['date']],  # 确保日期是字符串类型以便JSON序列化
                        y=daily_counts['count'],
                        name="每日ECG记录数",
                        marker_color='rgb(55, 83, 109)'
                    ),
                    row=1, col=1
                )
                
                # 设置x轴格式为日期
                fig.update_xaxes(title_text="日期", row=1, col=1)
                fig.update_yaxes(title_text="记录数量", row=1, col=1)
                
                # 处理分类信息 - 优先使用 classification 列
                class_col = None
                for col in ['classification', 'Classification', '分類', '分类']:
                    if col in ecg_data.columns:
                        class_col = col
                        break
                
                if class_col:
                    # 过滤掉缺失的分类
                    valid_class_data = ecg_data.dropna(subset=[class_col])
                    
                    if not valid_class_data.empty:
                        # 统计各分类的数量
                        class_counts = valid_class_data[class_col].value_counts().reset_index()
                        class_counts.columns = ['class', 'count']
                        
                        # 确保count列是整数类型
                        class_counts['count'] = class_counts['count'].astype(int)
                        # 确保class列是字符串类型
                        class_counts['class'] = class_counts['class'].astype(str)
                        
                        print(f"ECG分类分布: {class_counts[['class', 'count']].values.tolist()}")
                        
                        # 绘制饼图
                        fig.add_trace(
                            go.Pie(
                                labels=class_counts['class'],
                                values=class_counts['count'],
                                name="分类分布",
                                marker_colors=px.colors.qualitative.Plotly
                            ),
                            row=2, col=1
                        )
                
                # 设置图表布局
                fig.update_layout(
                    title_text="心电图数据摘要",
                    height=800,
                    showlegend=True
                )
                
                print(f"ECG图表创建完成，包含 {len(fig.data)} 个trace")
                
                # 安全地转换为JSON
                try:
                    json_data = json.loads(fig.to_json())
                    print(f"ECG图表成功转换为JSON")
                    return json_data
                except Exception as json_error:
                    print(f"ECG图表JSON转换出错: {str(json_error)}")
                    return {"error": "ECG图表数据处理出错"}
            else:
                print("ECG每日记录数为空")
                return {"error": "ECG记录数为0"}
        except Exception as e:
            print(f"绘制心电图摘要时出错: {e}")
            traceback.print_exc()
            return {"error": f"处理ECG数据时出错: {str(e)}"}

    def _prepare_steps_chart_data(self, steps_data, days=30):
        """准备步数图表数据"""
        try:
            print(f"开始准备步数图表数据...")
            if steps_data.empty:
                print("步数数据为空")
                return pd.DataFrame()
            
            print(f"步数数据列: {steps_data.columns.tolist()}")
            
            # 提取日期部分
            steps_data['日期'] = steps_data['startDate'].dt.date
            print(f"添加日期列后的数据列: {steps_data.columns.tolist()}")
            
            # 按日期分组并计算总步数
            daily_steps = steps_data.groupby('日期').agg({'value': 'sum'}).reset_index()
            print(f"按日期分组后的数据列: {daily_steps.columns.tolist()}")
            
            # 确保value列是数值类型
            daily_steps['value'] = pd.to_numeric(daily_steps['value'], errors='coerce')
            daily_steps = daily_steps.dropna(subset=['value'])
            if not daily_steps.empty:
                print(f"确保数值类型后步数value列类型: {type(daily_steps['value'].iloc[0])}")
            
            # 只保留最近的N天数据
            cutoff_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).date()
            recent_steps = daily_steps[daily_steps['日期'] >= cutoff_date]
            
            # 按日期排序
            recent_steps = recent_steps.sort_values('日期')
            
            # 转换日期为字符串，以便JSON序列化
            recent_steps['日期'] = recent_steps['日期'].astype(str)
            print(f"处理后的步数数据形状: {recent_steps.shape}")
            
            return recent_steps
        except Exception as e:
            print(f"准备步数图表数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

    def _prepare_heart_rate_chart_data(self, heart_rate_data, days=30):
        """准备心率图表数据"""
        try:
            print(f"开始准备心率图表数据...")
            if heart_rate_data.empty:
                print("心率数据为空")
                return pd.DataFrame()
            
            print(f"原始心率数据列: {heart_rate_data.columns.tolist()}")
            if 'value' in heart_rate_data.columns:
                print(f"心率value列类型: {type(heart_rate_data['value'].iloc[0]) if not heart_rate_data.empty else 'N/A'}")
                
                # 确保value列是数值类型
                heart_rate_data['value'] = pd.to_numeric(heart_rate_data['value'], errors='coerce')
                # 过滤掉NaN值
                heart_rate_data = heart_rate_data.dropna(subset=['value'])
                if not heart_rate_data.empty:
                    print(f"转换后心率value列类型: {type(heart_rate_data['value'].iloc[0])}")
            
            # 重采样为小时数据点以减少数据量
            heart_rate_data.set_index('startDate', inplace=True)
            hr_hourly = heart_rate_data.resample('H').mean().reset_index()
            print(f"重采样后的心率数据列: {hr_hourly.columns.tolist()}")
            
            # 提取日期部分
            hr_hourly['日期'] = hr_hourly['startDate'].dt.date
            
            # 只保留最近的N天数据
            cutoff_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).date()
            recent_hr = hr_hourly[hr_hourly['日期'] >= cutoff_date]
            
            # 按日期排序
            recent_hr = recent_hr.sort_values('日期')
            
            # 转换日期为字符串，以便JSON序列化
            recent_hr['日期'] = recent_hr['日期'].astype(str)
            print(f"处理后的心率数据形状: {recent_hr.shape}")
            if 'value' in recent_hr.columns and not recent_hr.empty:
                print(f"处理后心率value列类型: {type(recent_hr['value'].iloc[0])}")
                print(f"心率value前几个值: {recent_hr['value'].head().tolist()}")
            
            return recent_hr
        except Exception as e:
            print(f"准备心率图表数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

    def _prepare_sleep_chart_data(self, sleep_data, days=30):
        """准备睡眠图表数据"""
        try:
            print(f"开始准备睡眠图表数据...")
            if sleep_data.empty:
                print("睡眠数据为空")
                return pd.DataFrame()
            
            print(f"原始睡眠数据列: {sleep_data.columns.tolist()}")
            if 'duration' in sleep_data.columns:
                print(f"睡眠duration列类型: {type(sleep_data['duration'].iloc[0]) if not sleep_data.empty else 'N/A'}")
                # 确保duration列是数值类型
                sleep_data['duration'] = pd.to_numeric(sleep_data['duration'], errors='coerce')
                # 过滤掉NaN值
                sleep_data = sleep_data.dropna(subset=['duration'])
                if not sleep_data.empty:
                    print(f"转换后睡眠duration列类型: {type(sleep_data['duration'].iloc[0])}")
                    print(f"睡眠duration前几个值: {sleep_data['duration'].head().tolist()}")
            
            # 提取日期部分 - 添加这一步，从startDate创建日期列
            if 'startDate' in sleep_data.columns and '日期' not in sleep_data.columns:
                print("从startDate创建日期列")
                sleep_data['日期'] = sleep_data['startDate'].dt.date
            
            # 只保留最近的N天数据
            cutoff_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).date()
            
            # 确保日期列存在
            if '日期' not in sleep_data.columns:
                print("警告：睡眠数据中缺少日期列，返回所有数据")
                recent_sleep = sleep_data.copy()
            else:
                recent_sleep = sleep_data[sleep_data['日期'] >= cutoff_date]
            
            # 按日期排序
            if '日期' in recent_sleep.columns:
                recent_sleep = recent_sleep.sort_values('日期')
                
                # 转换日期为字符串，以便JSON序列化
                recent_sleep['日期'] = recent_sleep['日期'].astype(str)
            else:
                # 如果没有日期列，尝试按startDate排序
                if 'startDate' in recent_sleep.columns:
                    recent_sleep = recent_sleep.sort_values('startDate')
                    
                    # 创建一个日期列用于显示
                    recent_sleep['日期'] = recent_sleep['startDate'].dt.date.astype(str)
            
            print(f"处理后的睡眠数据形状: {recent_sleep.shape}")
            
            return recent_sleep
        except Exception as e:
            print(f"准备睡眠图表数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

    def _prepare_ecg_chart_data(self, ecg_data, days=30):
        """准备ECG图表数据"""
        try:
            print(f"开始准备ECG图表数据...")
            if ecg_data.empty:
                print("ECG数据为空")
                return pd.DataFrame()
            
            print(f"ECG数据类型: {type(ecg_data)}")
            print(f"ECG数据列: {ecg_data.columns.tolist()}")
            
            # 识别日期列
            date_col = None
            for col in ['date', 'startDate']:
                if col in ecg_data.columns:
                    date_col = col
                    break
                    
            if date_col is None:
                print("ECG数据缺少日期列")
                return pd.DataFrame()
            
            # 提取日期部分
            ecg_data['日期'] = ecg_data[date_col].dt.date
            
            # 只保留最近的N天数据
            cutoff_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).date()
            recent_ecg = ecg_data[ecg_data['日期'] >= cutoff_date]
            
            # 按日期排序
            recent_ecg = recent_ecg.sort_values('日期')
            
            # 转换日期为字符串，以便JSON序列化
            recent_ecg['日期'] = recent_ecg['日期'].astype(str)
            print(f"处理后的ECG数据形状: {recent_ecg.shape}")
            
            return recent_ecg
        except Exception as e:
            print(f"准备ECG图表数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

    def _create_steps_chart(self, steps_data):
        """创建步数图表"""
        try:
            print(f"开始创建步数图表...")
            if steps_data.empty:
                return None
            
            print(f"步数数据列: {steps_data.columns.tolist()}")
            print(f"步数value列类型: {type(steps_data['value'].iloc[0]) if 'value' in steps_data.columns and not steps_data.empty else 'N/A'}")
            
            # 创建一个副本避免修改原始数据
            steps_chart_data = steps_data.copy()
            
            # 确保value列是数值类型
            if 'value' in steps_chart_data.columns:
                steps_chart_data['value'] = pd.to_numeric(steps_chart_data['value'], errors='coerce')
                steps_chart_data = steps_chart_data.dropna(subset=['value'])
                if not steps_chart_data.empty:
                    print(f"转换后步数value列类型: {type(steps_chart_data['value'].iloc[0])}")
                    print(f"前几个步数值: {steps_chart_data['value'].head().tolist()}")
            
            if steps_chart_data.empty:
                print("数据转换后为空，无法创建图表")
                return None
            
            fig = px.bar(
                steps_chart_data, 
                x='日期', 
                y='value',
                title='每日步数',
                labels={'日期': '日期', 'value': '步数'},
                color_discrete_sequence=['#1f77b4']
            )
            
            # 添加平均线
            avg_steps = float(steps_chart_data['value'].mean())
            print(f"平均步数: {avg_steps}, 类型: {type(avg_steps)}")
            
            fig.add_hline(
                y=avg_steps,
                line_dash="dash",
                line_color="red",
                annotation_text=f"平均: {avg_steps:.0f}步",
                annotation_position="top right"
            )
            
            # 设置布局
            fig.update_layout(
                xaxis_title='日期',
                yaxis_title='步数',
                hovermode='x unified',
                height=400
            )
            
            print(f"步数图表创建完成")
            return json.loads(fig.to_json())
        except Exception as e:
            print(f"创建步数图表时出错: {str(e)}")
            traceback.print_exc()
            return None

    def _create_heart_rate_chart(self, hr_data):
        """创建心率图表"""
        try:
            print(f"开始创建心率图表...")
            if hr_data.empty:
                return None
            
            print(f"心率数据列: {hr_data.columns.tolist()}")
            print(f"心率value列类型: {type(hr_data['value'].iloc[0]) if 'value' in hr_data.columns and not hr_data.empty else 'N/A'}")
            
            # 创建一个副本避免修改原始数据
            hr_chart_data = hr_data.copy()
            
            # 确保value列是数值类型
            if 'value' in hr_chart_data.columns:
                hr_chart_data['value'] = pd.to_numeric(hr_chart_data['value'], errors='coerce')
                hr_chart_data = hr_chart_data.dropna(subset=['value'])
                if not hr_chart_data.empty:
                    print(f"转换后心率value列类型: {type(hr_chart_data['value'].iloc[0])}")
                    print(f"前几个心率值: {hr_chart_data['value'].head().tolist()}")
            
            if hr_chart_data.empty:
                print("数据转换后为空，无法创建图表")
                return None
            
            fig = px.line(
                hr_chart_data, 
                x='日期', 
                y='value',
                title='心率变化趋势',
                labels={'日期': '日期', 'value': '心率 (bpm)'},
                color_discrete_sequence=['#ff7f0e']
            )
            
            # 添加心率区间
            max_value = float(hr_chart_data['value'].max())
            min_value = float(hr_chart_data['value'].min())
            print(f"心率最大值: {max_value}, 类型: {type(max_value)}")
            print(f"心率最小值: {min_value}, 类型: {type(min_value)}")
            
            fig.add_hrect(
                y0=100, y1=max(max_value, 100),
                fillcolor="red", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="高心率区间",
                annotation_position="top right"
            )
            
            fig.add_hrect(
                y0=60, y1=100,
                fillcolor="green", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="正常心率区间",
                annotation_position="top left"
            )
            
            fig.add_hrect(
                y0=min(min_value, 60), y1=60,
                fillcolor="blue", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="低心率区间",
                annotation_position="bottom left"
            )
            
            # 设置布局
            fig.update_layout(
                xaxis_title='日期',
                yaxis_title='心率 (bpm)',
                hovermode='x unified',
                height=400
            )
            
            print(f"心率图表创建完成")
            return json.loads(fig.to_json())
        except Exception as e:
            print(f"创建心率图表时出错: {str(e)}")
            traceback.print_exc()
            return None

    def _create_sleep_chart(self, sleep_data):
        """创建睡眠图表"""
        try:
            print(f"开始创建睡眠图表...")
            if sleep_data.empty:
                return None
            
            print(f"睡眠数据列: {sleep_data.columns.tolist()}")
            print(f"睡眠duration列类型: {type(sleep_data['duration'].iloc[0]) if 'duration' in sleep_data.columns and not sleep_data.empty else 'N/A'}")
            
            # 创建一个副本避免修改原始数据
            sleep_chart_data = sleep_data.copy()
            
            # 确保duration列是数值类型
            if 'duration' in sleep_chart_data.columns:
                sleep_chart_data['duration'] = pd.to_numeric(sleep_chart_data['duration'], errors='coerce')
                sleep_chart_data = sleep_chart_data.dropna(subset=['duration'])
                if not sleep_chart_data.empty:
                    print(f"转换后睡眠duration列类型: {type(sleep_chart_data['duration'].iloc[0])}")
                    print(f"前几个睡眠duration值: {sleep_chart_data['duration'].head().tolist()}")
            
            if sleep_chart_data.empty:
                print("数据转换后为空，无法创建图表")
                return None
            
            # 创建图表
            fig = go.Figure()
            
            # 添加睡眠时间柱状图
            fig.add_trace(go.Bar(
                x=sleep_chart_data['日期'],
                y=sleep_chart_data['duration'],  # 这里使用duration而不是value
                marker_color='skyblue',
                name='睡眠时长(小时)'
            ))
            
            # 设置图表标题和轴标签
            fig.update_layout(
                title='每日睡眠时长',
                xaxis_title='日期',
                yaxis_title='睡眠时长(小时)',
                template='plotly_white',
                margin=dict(l=0, r=0, t=30, b=0),
                height=300
            )
            
            print(f"睡眠图表创建完成")
            # 与其他图表保持一致，返回JSON而不是HTML
            return json.loads(fig.to_json())
        except Exception as e:
            print(f"创建睡眠图表时出错: {str(e)}")
            traceback.print_exc()
            return None

    def _create_ecg_chart(self, ecg_data):
        """创建ECG图表"""
        try:
            print(f"开始创建ECG图表...")
            if ecg_data.empty:
                print("ECG数据为空，跳过图表创建")
                return None
            
            print(f"ECG数据列: {ecg_data.columns.tolist()}")
            
            # 创建一个副本避免修改原始数据
            ecg_chart_data = ecg_data.copy()
            
            # 创建一个2行1列的图表布局
            fig = make_subplots(rows=2, cols=1, 
                              subplot_titles=("ECG记录分布", "ECG分类统计"),
                              specs=[[{"type": "xy"}], [{"type": "pie"}]],
                              row_heights=[0.6, 0.4],
                              vertical_spacing=0.1)
            
            # 获取日期列
            date_col = None
            for col in ['date', 'startDate']:
                if col in ecg_chart_data.columns:
                    date_col = col
                    break
                    
            if date_col is None:
                print("ECG数据缺少日期列，无法创建图表")
                return None
            
            # 按日期分组统计记录数
            # 确保日期列是datetime类型
            ecg_chart_data[date_col] = pd.to_datetime(ecg_chart_data[date_col], errors='coerce')
            # 删除NaT（无效日期）
            ecg_chart_data = ecg_chart_data.dropna(subset=[date_col])
            
            if ecg_chart_data.empty:
                print("清理日期后ECG数据为空，无法创建图表")
                return None
                
            # 计算每天的记录数
            daily_counts = ecg_chart_data.groupby(ecg_chart_data[date_col].dt.date).size().reset_index()
            daily_counts.columns = ['date', 'count']
            
            # 确保count列是整数类型
            daily_counts['count'] = daily_counts['count'].astype(int)
            
            print(f"ECG每日记录数: {daily_counts['count'].tolist()}")
            
            # 绘制每天的记录数量
            fig.add_trace(
                go.Bar(
                    x=daily_counts['date'].astype(str),  # 确保日期是字符串类型以便JSON序列化
                    y=daily_counts['count'],
                    name="每日ECG记录数",
                    marker_color='rgb(55, 83, 109)'
                ),
                row=1, col=1
            )
            
            # 设置x轴格式为日期
            fig.update_xaxes(title_text="日期", row=1, col=1)
            fig.update_yaxes(title_text="记录数量", row=1, col=1)
        
            # 绘制分类分布饼图
            class_col = None
            for col in ['classification', 'Classification', '分類', '分类']:
                if col in ecg_chart_data.columns:
                    class_col = col
                    break
            
            if class_col:
                # 过滤掉缺失的分类
                valid_class_data = ecg_chart_data.dropna(subset=[class_col])
                
                if not valid_class_data.empty:
                    # 统计各分类的数量
                    class_counts = valid_class_data[class_col].value_counts().reset_index()
                    class_counts.columns = ['class', 'count']
                    
                    # 确保count列是整数类型
                    class_counts['count'] = class_counts['count'].astype(int)
                    # 确保class列是字符串类型
                    class_counts['class'] = class_counts['class'].astype(str)
                    
                    print(f"ECG分类分布: {class_counts[['class', 'count']].values.tolist()}")
                    
                    # 绘制饼图
                    fig.add_trace(
                        go.Pie(
                            labels=class_counts['class'],
                            values=class_counts['count'],
                            name="分类分布",
                            marker_colors=px.colors.qualitative.Plotly
                        ),
                        row=2, col=1
                    )
            
            # 设置图表布局
            fig.update_layout(
                title_text="心电图数据摘要",
                height=800,
                showlegend=True
            )
            
            # 安全地转换为JSON
            try:
                json_data = json.loads(fig.to_json())
                print(f"ECG图表创建成功，包含 {len(fig.data)} 个trace")
                return json_data
            except Exception as json_error:
                print(f"ECG图表JSON转换出错: {str(json_error)}")
                # 返回一个简单的占位图表
                return {"data": [], "layout": {"title": {"text": "ECG数据处理出错"}}}
            
        except Exception as e:
            print(f"创建ECG图表时出错: {str(e)}")
            traceback.print_exc()
            return None 