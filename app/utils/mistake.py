import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

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
    
    def create_health_dashboard(self):
        """创建健康数据仪表板"""
        try:
            # 获取各类型数据
            steps_data = self.parser.get_step_count_data()
            heart_rate_data = self.parser.get_heart_rate_data()
            sleep_data = self.parser.get_sleep_analysis_data()
            stress_data = self.parser.get_stress_indicators()
            ecg_data = self.parser.get_ecg_data()
            
            # 检查是否有足够的数据
            has_steps = not steps_data.empty
            has_heart_rate = not heart_rate_data.empty
            has_sleep = not sleep_data.empty
            has_stress = not stress_data.empty
            has_ecg = not ecg_data.empty
            
            # 如果没有任何数据，返回None
            if not any([has_steps, has_heart_rate, has_sleep, has_stress, has_ecg]):
                print("没有足够的数据来创建仪表板")
                return None
            
            # 根据有效数据类型决定布局
            if has_ecg:
                # 2x3布局：步数、心率、睡眠、心电记录数、应力指标、ECG分类
                fig = make_subplots(
                    rows=2, cols=3,
                    subplot_titles=(
                        "每日步数", "心率趋势", "睡眠时长",
                        "心电记录", "应力指标", "ECG分类"
                    ),
                    specs=[
                        [{"type": "xy"}, {"type": "xy"}, {"type": "xy"}],
                        [{"type": "xy"}, {"type": "xy"}, {"type": "pie"}]
                    ],
                    vertical_spacing=0.12,
                    horizontal_spacing=0.06
                )
            else:
                # 2x2布局：步数、心率、睡眠、应力指标
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=("每日步数", "心率趋势", "睡眠时长", "应力指标"),
                    vertical_spacing=0.15,
                    horizontal_spacing=0.1
                )
            
            # 添加每日步数图表
            if has_steps:
                # 确保数据已排序
                steps_data = steps_data.sort_values(by='startDate')
                fig.add_trace(
                    go.Scatter(
                        x=steps_data['startDate'], 
                        y=steps_data['value'], 
                        mode='lines+markers',
                        name='每日步数',
                        line=dict(width=2, color='#1f77b4'),
                        marker=dict(size=5)
                    ),
                    row=1, col=1
                )
                fig.update_xaxes(title_text='日期', row=1, col=1)
                fig.update_yaxes(title_text='步数', row=1, col=1)
            
            # 添加心率趋势图表
            if has_heart_rate:
                # 确保数据已排序
                heart_rate_data = heart_rate_data.sort_values(by='startDate')
                fig.add_trace(
                    go.Scatter(
                        x=heart_rate_data['startDate'], 
                        y=heart_rate_data['value'], 
                        mode='lines',
                        name='心率',
                        line=dict(width=2, color='#d62728')
                    ),
                    row=1, col=2
                )
                fig.update_xaxes(title_text='时间', row=1, col=2)
                fig.update_yaxes(title_text='心率 (BPM)', row=1, col=2)
            
            # 添加睡眠时长图表
            if has_sleep:
                # 确保数据已排序
                sleep_data = sleep_data.sort_values(by='startDate')
                # 将时长转换为小时
                sleep_data['hours'] = sleep_data['value'].astype(float) / 3600
                fig.add_trace(
                    go.Bar(
                        x=sleep_data['startDate'], 
                        y=sleep_data['hours'], 
                        name='睡眠时长',
                        marker_color='#2ca02c'
                    ),
                    row=1, col=3
                )
                fig.update_xaxes(title_text='日期', row=1, col=3)
                fig.update_yaxes(title_text='睡眠时长 (小时)', row=1, col=3)
            
            # 添加心电图数据
            if has_ecg:
                # 按日期分组统计记录数
                ecg_data['startDate'] = pd.to_datetime(ecg_data['startDate'], errors='coerce')
                daily_ecg = ecg_data.groupby(ecg_data['startDate'].dt.date).size().reset_index()
                daily_ecg.columns = ['date', 'count']
                
                fig.add_trace(
                    go.Bar(
                        x=daily_ecg['date'],
                        y=daily_ecg['count'],
                        name='ECG记录数',
                        marker_color='#ff7f0e'
                    ),
                    row=2, col=1
                )
                fig.update_xaxes(title_text='日期', row=2, col=1)
                fig.update_yaxes(title_text='记录数', row=2, col=1)
                
                # 添加ECG分类饼图
                class_col = None
                for col in ['分類', '分类', 'classification']:
                    if col in ecg_data.columns:
                        class_col = col
                        break
                
                if class_col:
                    class_counts = ecg_data[class_col].value_counts().reset_index()
                    class_counts.columns = ['class', 'count']
                    
                    fig.add_trace(
                        go.Pie(
                            labels=class_counts['class'],
                            values=class_counts['count'],
                            name='ECG分类',
                            marker_colors=px.colors.qualitative.Plotly
                        ),
                        row=2, col=3
                    )
            
            # 添加应力指标图表
            if has_stress:
                # 确保数据已排序
                stress_data = stress_data.sort_values(by='startDate')
                fig.add_trace(
                    go.Scatter(
                        x=stress_data['startDate'], 
                        y=stress_data['value'], 
                        mode='markers',
                        name='应力指标',
                        marker=dict(
                            size=8,
                            color=stress_data['value'],
                            colorscale='Viridis',
                            showscale=True
                        )
                    ),
                    row=2, col=2
                )
                fig.update_xaxes(title_text='时间', row=2, col=2)
                fig.update_yaxes(title_text='应力水平', row=2, col=2)
            
            # 设置图表布局
            fig.update_layout(
                title_text="健康数据摘要",
                height=800,
                showlegend=False
            )
            
            return json.loads(fig.to_json())
        
        except Exception as e:
            print(f"创建健康仪表板时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def plot_ecg_summary(self, ecg_data):
        """绘制心电图数据摘要"""
        if ecg_data.empty:
            print("没有心电图数据可供绘制")
            return None

        try:
            # 创建一个2行1列的图表布局
            fig = make_subplots(rows=2, cols=1, 
                               subplot_titles=("ECG记录数量", "ECG分类分布"),
                               specs=[[{"type": "xy"}], [{"type": "pie"}]],
                               row_heights=[0.6, 0.4],
                               vertical_spacing=0.1)
            
            # 按日期分组统计记录数
            if 'startDate' in ecg_data.columns:
                # 确保日期列是datetime类型
                ecg_data['startDate'] = pd.to_datetime(ecg_data['startDate'], errors='coerce')
                # 计算每天的记录数
                daily_counts = ecg_data.groupby(ecg_data['startDate'].dt.date).size().reset_index()
                daily_counts.columns = ['date', 'count']
                
                # 绘制每天的记录数量
                fig.add_trace(
                    go.Bar(
                        x=daily_counts['date'],
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
            if '分類' in ecg_data.columns or '分类' in ecg_data.columns or 'classification' in ecg_data.columns:
                # 选择存在的分类列
                class_col = None
                for col in ['分類', '分类', 'classification']:
                    if col in ecg_data.columns:
                        class_col = col
                        break
                
                if class_col:
                    # 统计各分类的数量
                    class_counts = ecg_data[class_col].value_counts().reset_index()
                    class_counts.columns = ['class', 'count']
                    
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
            
            return fig
        
        except Exception as e:
            print(f"绘制心电图摘要时出错: {e}")
            import traceback
            traceback.print_exc()
            return None 