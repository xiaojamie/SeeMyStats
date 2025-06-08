import os
import pandas as pd
import numpy as np
import zipfile
import xml.etree.ElementTree as ET
import json
import glob
from datetime import datetime, timezone
import shutil
import csv
import traceback

class HealthDataParser:
    """Apple健康数据解析类"""
    
    def __init__(self):
        """初始化解析器"""
        self.records = []  # 所有健康记录
        self.record_types = {}  # 记录类型映射
        self.xml_root = None  # XML根元素
        self.temp_dirs = []  # 临时目录列表，用于清理
    
    def clean_up(self):
        """清理临时文件和目录"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs = []
    
    def extract_from_zip(self, zip_path):
        """
        从ZIP文件中提取Apple健康导出的XML文件
        
        参数:
            zip_path: ZIP文件路径
            
        返回:
            提取的XML文件路径或None（如果未找到）
        """
        try:
            # 创建临时目录
            import tempfile
            extract_dir = tempfile.mkdtemp()
            self.temp_dirs.append(extract_dir)
            
            # 提取ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 查找export.xml或輸出.xml文件
                xml_files = [f for f in zip_ref.namelist() if f.endswith('export.xml') or f.endswith('輸出.xml')]
                
                if not xml_files:
                    print("在ZIP文件中找不到export.xml或輸出.xml文件")
                    return None
                
                # 提取找到的XML文件
                xml_path = os.path.join(extract_dir, os.path.basename(xml_files[0]))
                for xml_file in xml_files:
                    with open(xml_path, 'wb') as f:
                        f.write(zip_ref.read(xml_file))
                
                return xml_path
        except Exception as e:
            print(f"从ZIP文件提取XML时出错: {str(e)}")
            traceback.print_exc()
            return None
    
    def parse_xml(self, xml_path):
        """
        解析Apple健康导出的XML文件
        
        参数:
            xml_path: XML文件路径
            
        返回:
            解析是否成功
        """
        try:
            # 解析XML文件
            # 注意：Apple健康导出的XML文件可能非常大，使用迭代解析
            print(f"开始解析XML文件: {xml_path}")
            
            # 使用迭代器解析大型XML文件
            for event, elem in ET.iterparse(xml_path, events=('end',)):
                if elem.tag == 'Record':
                    # 提取记录属性
                    record = elem.attrib
                    self.records.append(record)
                    
                    # 记录类型
                    record_type = record.get('type')
                    if record_type:
                        if record_type not in self.record_types:
                            self.record_types[record_type] = []
                        self.record_types[record_type].append(record)
                
                # 清除元素以节省内存
                elem.clear()
            
            print(f"XML解析完成，共获取{len(self.records)}条记录，{len(self.record_types)}种类型")
            return len(self.records) > 0
        except Exception as e:
            print(f"解析XML文件时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def parse_directory(self, directory_path):
        """
        解析包含Apple健康导出文件的目录
        
        参数:
            directory_path: 目录路径
            
        返回:
            解析是否成功
        """
        try:
            success = False
            
            # 查找XML文件
            xml_files = glob.glob(os.path.join(directory_path, "**", "*.xml"), recursive=True)
            for xml_file in xml_files:
                if os.path.basename(xml_file) in ['export.xml', '輸出.xml']:
                    if self.parse_xml(xml_file):
                        success = True
                        break
            
            # 如果没有找到XML文件或解析不成功，尝试查找JSON文件
            if not success:
                success = self.parse_json_files(directory_path)
            
            # 如果仍然不成功，尝试查找CSV文件
            if not success:
                success = self.parse_csv_files(directory_path)
            
            return success
        except Exception as e:
            print(f"解析目录时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def parse_json_files(self, directory_path):
        """
        解析目录中的JSON文件
        
        参数:
            directory_path: 目录路径
            
        返回:
            解析是否成功
        """
        try:
            json_files = glob.glob(os.path.join(directory_path, "**", "*.json"), recursive=True)
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # 检查是否是健康记录JSON格式
                        if isinstance(data, list):
                            for record in data:
                                if isinstance(record, dict) and 'type' in record:
                                    self.records.append(record)
                                    
                                    # 记录类型
                                    record_type = record.get('type')
                                    if record_type:
                                        if record_type not in self.record_types:
                                            self.record_types[record_type] = []
                                        self.record_types[record_type].append(record)
                except Exception as e:
                    print(f"解析JSON文件 {json_file} 时出错: {str(e)}")
                    continue
            
            return len(self.records) > 0
        except Exception as e:
            print(f"解析JSON文件时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def parse_csv_files(self, directory_path):
        """
        解析目录中的CSV文件
        
        参数:
            directory_path: 目录路径
            
        返回:
            解析是否成功
        """
        try:
            csv_files = glob.glob(os.path.join(directory_path, "**", "*.csv"), recursive=True)
            for csv_file in csv_files:
                try:
                    # 检测文件编码
                    encoding = 'utf-8'
                    try:
                        with open(csv_file, 'r', encoding='utf-8') as f:
                            f.readline()
                    except UnicodeDecodeError:
                        encoding = 'latin-1'  # 尝试使用其他编码
                    
                    # 读取CSV文件
                    df = pd.read_csv(csv_file, encoding=encoding)
                    
                    # 检查列名以确定这是否是健康数据CSV
                    health_data_columns = ['type', 'startDate', 'endDate', 'value']
                    has_health_columns = any(col in df.columns for col in health_data_columns)
                    
                    if has_health_columns:
                        # 转换为字典记录列表
                        records = df.to_dict('records')
                        
                        for record in records:
                            # 确保记录有type字段
                            if 'type' in record:
                                self.records.append(record)
                                
                                # 记录类型
                                record_type = record.get('type')
                                if record_type:
                                    if record_type not in self.record_types:
                                        self.record_types[record_type] = []
                                    self.record_types[record_type].append(record)
                except Exception as e:
                    print(f"解析CSV文件 {csv_file} 时出错: {str(e)}")
                    continue
            
            return len(self.records) > 0
        except Exception as e:
            print(f"解析CSV文件时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_all_data_types(self):
        """获取所有可用的数据类型"""
        return list(self.record_types.keys())
    
    def get_data_by_type(self, data_type):
        """
        获取指定类型的健康数据
        
        参数:
            data_type: Apple Health 中的类型字符串（如 "HKQuantityTypeIdentifierBodyMassIndex"）
            
        返回:
            包含指定类型数据的 DataFrame，如果该类型不存在则返回空的 DataFrame
        """
        try:
            # 检查该类型是否存在
            if data_type not in self.record_types:
                print(f"数据类型 {data_type} 不存在")
                return pd.DataFrame()
            
            # 获取该类型的所有记录
            records = self.record_types[data_type]
            
            if not records:
                print(f"数据类型 {data_type} 没有记录")
                return pd.DataFrame()
            
            # 将记录列表转换为 DataFrame
            df = pd.DataFrame(records)
            
            # 确保日期列是 datetime 类型
            for col in df.columns:
                if col.lower() in ['startdate', 'enddate', 'date', '日期', 'start', 'end']:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass
            
            # 按日期排序（如果有合适的日期列）
            date_cols = [col for col in df.columns if col.lower() in ['startdate', 'date', '日期', 'start']]
            if date_cols:
                df = df.sort_values(date_cols[0])
            
            return df
            
        except Exception as e:
            print(f"获取类型 {data_type} 的数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def _safe_date_conversion(self, date_str):
        """
        安全地将日期字符串转换为datetime对象
        
        参数:
            date_str: 日期字符串
            
        返回:
            datetime对象
        """
        try:
            # 检查并处理带有时区信息的日期
            if 'Z' in date_str or '+' in date_str or 'T' in date_str:
                # 尝试多种日期格式
                for fmt in ['%Y-%m-%d %H:%M:%S%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%SZ', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        # 替换Z为+00:00以标准化UTC时区表示
                        if 'Z' in date_str:
                            date_str = date_str.replace('Z', '+00:00')
                        return pd.to_datetime(date_str, format=fmt)
                    except:
                        continue
                
                # 如果以上格式都失败，尝试使用pandas默认解析
                return pd.to_datetime(date_str, utc=True)
            else:
                # 对于没有时区信息的日期，假设为本地时间
                return pd.to_datetime(date_str)
        except Exception as e:
            print(f"日期转换出错 ({date_str}): {str(e)}")
            # 返回当前时间作为后备选项
            return pd.Timestamp.now()
    
    def _extract_date(self, record):
        """
        从记录中提取日期
        
        参数:
            record: 健康记录字典
            
        返回:
            提取的日期或当前日期（如果无法提取）
        """
        date = None
        
        # 尝试不同的日期字段
        date_fields = ['startDate', 'endDate', 'date', '日期', 'Start', 'End']
        for field in date_fields:
            if field in record and record[field]:
                try:
                    date = self._safe_date_conversion(record[field])
                    break
                except:
                    continue
        
        # 如果无法提取，使用当前日期
        if date is None:
            date = pd.Timestamp.now()
        
        return date
    
    def _extract_value(self, record):
        """
        从记录中提取值
        
        参数:
            record: 健康记录字典
            
        返回:
            提取的值或None（如果无法提取）
        """
        value = None
        
        # 尝试不同的值字段
        value_fields = ['value', 'Value', '值', '数值']
        for field in value_fields:
            if field in record and record[field]:
                try:
                    value = float(record[field])
                    break
                except:
                    value = record[field]
                    break
        
        return value
    
    def get_step_count_data(self):
        """
        获取步数数据
        
        返回:
            包含步数数据的DataFrame
        """
        try:
            # 步数相关的类型
            step_types = [
                'HKQuantityTypeIdentifierStepCount',
                'com.apple.health.type.quantity.steps',
                'StepCount'
            ]
            
            # 收集所有步数记录
            step_records = []
            for type_name in step_types:
                if type_name in self.record_types:
                    step_records.extend(self.record_types[type_name])
            
            if not step_records:
                return pd.DataFrame()
            
            # 提取每条记录的日期和步数值
            data = []
            for record in step_records:
                date = self._extract_date(record)
                value = self._extract_value(record)
                
                if date is not None and value is not None:
                    try:
                        value = float(value)
                        data.append({
                            'startDate': date,
                            'value': value
                        })
                    except:
                        continue
            
            if not data:
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 确保日期是datetime类型
            df['startDate'] = pd.to_datetime(df['startDate'])
            
            # 按日期排序
            df = df.sort_values('startDate')
            
            return df
        except Exception as e:
            print(f"获取步数数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_daily_step_count(self):
        """
        获取每日步数总和
        
        返回:
            包含每日步数的DataFrame
        """
        try:
            steps_data = self.get_step_count_data()
            if steps_data.empty:
                return pd.DataFrame()
            
            # 提取日期部分
            steps_data['日期'] = steps_data['startDate'].dt.date
            
            # 按日期分组并求和
            daily_steps = steps_data.groupby('日期')['value'].sum().reset_index()
            
            # 重命名列
            daily_steps.columns = ['日期', '步数']
            
            # 转换日期为字符串，便于JSON序列化
            daily_steps['日期'] = daily_steps['日期'].astype(str)
            
            return daily_steps
        except Exception as e:
            print(f"获取每日步数时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_heart_rate_data(self):
        """
        获取心率数据
        
        返回:
            包含心率数据的DataFrame
        """
        try:
            # 心率相关的类型
            hr_types = [
                'HKQuantityTypeIdentifierHeartRate',
                'com.apple.health.type.quantity.heartrate',
                'HeartRate'
            ]
            
            # 收集所有心率记录
            hr_records = []
            for type_name in hr_types:
                if type_name in self.record_types:
                    hr_records.extend(self.record_types[type_name])
            
            if not hr_records:
                return pd.DataFrame()
            
            # 提取每条记录的日期和心率值
            data = []
            for record in hr_records:
                date = self._extract_date(record)
                value = self._extract_value(record)
                
                if date is not None and value is not None:
                    try:
                        value = float(value)
                        data.append({
                            'startDate': date,
                            'value': value
                        })
                    except:
                        continue
            
            if not data:
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 确保日期是datetime类型
            df['startDate'] = pd.to_datetime(df['startDate'])
            
            # 按日期排序
            df = df.sort_values('startDate')
            
            return df
        except Exception as e:
            print(f"获取心率数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_heart_rate_stats(self):
        """
        获取心率统计信息
        
        返回:
            包含心率统计的字典
        """
        try:
            hr_data = self.get_heart_rate_data()
            if hr_data.empty:
                return None
            
            hr_data['value'] = pd.to_numeric(hr_data['value'], errors='coerce')
            
            # 计算统计值
            avg_hr = hr_data['value'].mean()
            max_hr = hr_data['value'].max()
            min_hr = hr_data['value'].min()
            
            # 返回统计数据
            return {
                '平均心率': avg_hr,
                '最高心率': max_hr,
                '最低心率': min_hr
            }
        except Exception as e:
            print(f"获取心率统计时出错: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_sleep_analysis_data(self):
        """
        获取睡眠分析数据
        
        返回:
            包含睡眠数据的DataFrame
        """
        try:
            # 睡眠相关的类型
            sleep_types = [
                'HKCategoryTypeIdentifierSleepAnalysis',
                'com.apple.health.type.category.sleep',
                'SleepAnalysis'
            ]
            
            # 收集所有睡眠记录
            sleep_records = []
            for type_name in sleep_types:
                if type_name in self.record_types:
                    sleep_records.extend(self.record_types[type_name])
            
            if not sleep_records:
                return pd.DataFrame()
            
            # 提取每条记录的日期、持续时间和睡眠状态
            data = []
            for record in sleep_records:
                start_date = self._extract_date(record)
                
                # 尝试获取结束日期
                end_date = None
                if 'endDate' in record and record['endDate']:
                    try:
                        end_date = self._safe_date_conversion(record['endDate'])
                    except:
                        pass
                
                # 如果没有结束日期，尝试使用其他字段
                if end_date is None and 'End' in record and record['End']:
                    try:
                        end_date = self._safe_date_conversion(record['End'])
                    except:
                        pass
                
                # 计算持续时间
                duration = None
                if end_date is not None:
                    duration = (end_date - start_date).total_seconds() / 3600  # 小时
                
                # 尝试获取睡眠状态
                value = None
                if 'value' in record and record['value']:
                    value = record['value']
                elif 'Value' in record and record['Value']:
                    value = record['Value']
                
                if start_date is not None and (duration is not None or value is not None):
                    data.append({
                        'startDate': start_date,
                        'endDate': end_date,
                        'duration': duration,
                        'value': value
                    })
            
            if not data:
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 确保日期是datetime类型
            df['startDate'] = pd.to_datetime(df['startDate'])
            if 'endDate' in df.columns:
                df['endDate'] = pd.to_datetime(df['endDate'])
            
            # 按开始日期排序
            df = df.sort_values('startDate')
            
            return df
        except Exception as e:
            print(f"获取睡眠数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_sleep_duration_daily(self):
        """
        获取每日睡眠时长
        
        返回:
            包含每日睡眠时长的DataFrame
        """
        try:
            sleep_data = self.get_sleep_analysis_data()
            if sleep_data.empty:
                return pd.DataFrame()
            
            # 仅保留入睡状态的记录（如果有状态信息）
            if 'value' in sleep_data.columns:
                # 尝试过滤睡眠状态
                try:
                    sleep_states = ['asleep', 'inBed', '入睡', '睡眠']
                    mask = sleep_data['value'].str.lower().isin([state.lower() for state in sleep_states])
                    filtered_sleep_data = sleep_data[mask]
                    
                    # 如果过滤后没有数据，则使用所有数据
                    if filtered_sleep_data.empty:
                        filtered_sleep_data = sleep_data
                except:
                    filtered_sleep_data = sleep_data
            else:
                filtered_sleep_data = sleep_data
            
            # 提取日期部分
            filtered_sleep_data['日期'] = filtered_sleep_data['startDate'].dt.date
            
            # 按日期分组并计算总睡眠时长
            if 'duration' in filtered_sleep_data.columns and not filtered_sleep_data['duration'].isna().all():
                # 如果有持续时间列，直接使用
                daily_sleep = filtered_sleep_data.groupby('日期')['duration'].sum().reset_index()
            else:
                # 否则，尝试使用开始和结束时间计算
                if 'endDate' in filtered_sleep_data.columns:
                    filtered_sleep_data['duration'] = (
                        filtered_sleep_data['endDate'] - filtered_sleep_data['startDate']
                    ).dt.total_seconds() / 3600  # 小时
                    daily_sleep = filtered_sleep_data.groupby('日期')['duration'].sum().reset_index()
                else:
                    return pd.DataFrame()
            
            # 重命名列
            daily_sleep.columns = ['日期', '睡眠时长(小时)']
            
            # 转换日期为字符串，便于JSON序列化
            daily_sleep['日期'] = daily_sleep['日期'].astype(str)
            
            return daily_sleep
        except Exception as e:
            print(f"获取每日睡眠时长时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_stress_indicators(self):
        """
        获取压力指标数据
        
        返回:
            包含压力指标的DataFrame
        """
        try:
            # 获取心率变异性数据
            hr_data = self.get_heart_rate_data()
            if hr_data.empty:
                # 返回包含必要列的空DataFrame
                return pd.DataFrame(columns=['日期', '心率波动', '心率范围', '平均心率', '压力指数', 'startDate'])
            
            # 确保数值类型
            hr_data['value'] = pd.to_numeric(hr_data['value'], errors='coerce')
            # 过滤掉NaN值
            hr_data = hr_data.dropna(subset=['value'])
            
            if hr_data.empty:
                # 返回包含必要列的空DataFrame
                return pd.DataFrame(columns=['日期', '心率波动', '心率范围', '平均心率', '压力指数', 'startDate'])
            
            # 提取日期部分
            hr_data['日期'] = hr_data['startDate'].dt.date
            
            # 计算每天的心率标准差和范围作为压力指标
            stress_data = hr_data.groupby('日期').agg(
                心率波动=('value', 'std'),
                心率范围=('value', lambda x: x.max() - x.min()),
                平均心率=('value', 'mean')
            ).reset_index()
            
            # 填充可能的NaN值
            stress_data = stress_data.fillna(0)
            
            # 确保所有数值列是float类型
            for col in ['心率波动', '心率范围', '平均心率']:
                stress_data[col] = pd.to_numeric(stress_data[col], errors='coerce').fillna(0).astype(float)
            
            # 计算压力指数（标准差和心率范围的综合指标）
            stress_data['压力指数'] = (
                stress_data['心率波动'] * 0.6 + stress_data['心率范围'] * 0.4
            ) / 10.0
            
            # 确保压力指数是float类型
            stress_data['压力指数'] = pd.to_numeric(stress_data['压力指数'], errors='coerce').fillna(0).astype(float)
            
            # 确保压力指数在1-10范围内
            stress_data['压力指数'] = np.clip(stress_data['压力指数'], 1, 10)
            
            # 存储日期原始值
            stress_data['startDate'] = stress_data['日期']
            
            # 转换日期为字符串，便于JSON序列化
            stress_data['日期'] = stress_data['日期'].astype(str)
            
            # 按日期排序
            stress_data = stress_data.sort_values('日期')
            
            # 最终再次确认所有数值列是float类型
            for col in ['心率波动', '心率范围', '平均心率', '压力指数']:
                stress_data[col] = pd.to_numeric(stress_data[col], errors='coerce').fillna(0).astype(float)
            
            return stress_data
        except Exception as e:
            print(f"获取压力指标时出错: {str(e)}")
            traceback.print_exc()
            # 返回包含必要列的空DataFrame
            return pd.DataFrame(columns=['日期', '心率波动', '心率范围', '平均心率', '压力指数', 'startDate'])
    
    def get_ecg_data(self):
        """
        获取ECG/心电图数据。
        会先检查是否有 electrocardiograms 目录中的 CSV 文件数据，
        如果没有，再尝试从XML中提取ECG数据。
        
        返回:
            包含ECG数据的DataFrame，列包括：
            ['filename', 'date', 'classification', 'device', 'sampling_rate', 'signal', 'length']
        """
        try:
            # 首先尝试从 electrocardiograms 目录读取 CSV 文件
            ecg_df = self.parse_ecg_files()
            
            # 如果从CSV读取到了数据，直接返回
            if not ecg_df.empty:
                print(f"从CSV文件中读取到 {len(ecg_df)} 条ECG记录")
                return ecg_df
                
            print("未找到ECG CSV文件，尝试从XML中提取数据...")
            
            # ECG相关的类型
            ecg_types = [
                'HKDataTypeIdentifierElectrocardiogram',
                'com.apple.health.type.electrocardiogram',
                'ElectrocardiogramData'
            ]
            
            # 收集所有ECG记录
            ecg_records = []
            for type_name in ecg_types:
                if type_name in self.record_types:
                    ecg_records.extend(self.record_types[type_name])
            
            if not ecg_records:
                print("XML中没有找到ECG数据")
                return pd.DataFrame()
            
            # 提取每条记录的日期和ECG数据
            data = []
            for record in ecg_records:
                date = self._extract_date(record)
                
                # 尝试获取分类值或波形数据
                classification = None
                if 'classification' in record:
                    classification = record['classification']
                elif 'Classification' in record:
                    classification = record['Classification']
                
                # 获取平均心率
                heart_rate = None
                if 'averageHeartRate' in record:
                    heart_rate = record['averageHeartRate']
                elif 'heartRate' in record:
                    heart_rate = record['heartRate']
                
                # 转换为数值
                try:
                    if heart_rate is not None:
                        heart_rate = float(heart_rate)
                except:
                    heart_rate = None
                
                if date is not None:
                    data.append({
                        'date': date,
                        'classification': classification,
                        'heart_rate': heart_rate,
                        'source': 'xml'
                    })
            
            if not data:
                print("没有有效的ECG记录")
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 确保日期是datetime类型
            df['date'] = pd.to_datetime(df['date'])
            
            # 按日期排序
            df = df.sort_values('date')
            
            return df
        except Exception as e:
            print(f"获取ECG数据时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()
            
    def parse_ecg_files(self):
        """
        解析electrocardiograms目录中的CSV文件
        
        返回:
            包含ECG数据的DataFrame，列包括：
            ['filename', 'date', 'classification', 'device', 'sampling_rate', 'signal', 'length']
        """
        try:
            # 查找可能的基础目录路径
            base_dir = None
            
            # 优先检查从session中提取的目录路径
            if hasattr(self, 'base_dir') and self.base_dir:
                base_dir = self.base_dir
            
            # 如果没有基础目录，查找可能的上传目录
            if not base_dir:
                # 查找可能的实例目录
                instance_dir = os.path.join(os.getcwd(), 'instance')
                if os.path.exists(instance_dir):
                    upload_dirs = glob.glob(os.path.join(instance_dir, 'uploads', '*'))
                    if upload_dirs:
                        # 使用最新的上传目录
                        upload_dirs.sort(key=os.path.getmtime, reverse=True)
                        base_dir = upload_dirs[0]
            
            if not base_dir:
                print("找不到有效的基础目录路径")
                return pd.DataFrame()
            
            # 构造ECG文件夹路径
            ecg_dir = os.path.join(base_dir, 'apple_health_export', 'electrocardiograms')
            
            # 检查ECG目录是否存在
            if not os.path.exists(ecg_dir):
                print(f"ECG目录不存在: {ecg_dir}")
                return pd.DataFrame()
            
            # 查找所有CSV文件
            csv_files = glob.glob(os.path.join(ecg_dir, '*.csv'))
            if not csv_files:
                print(f"ECG目录中没有CSV文件: {ecg_dir}")
                return pd.DataFrame()
            
            print(f"找到 {len(csv_files)} 个ECG CSV文件")
            
            # 解析每个CSV文件
            ecg_data = []
            for csv_file in csv_files:
                try:
                    # 提取文件名
                    filename = os.path.basename(csv_file)
                    
                    # 读取并解析CSV文件
                    metadata = {}
                    signal_data = []
                    in_metadata = True
                    
                    # 尝试不同的编码
                    encoding_list = ['utf-8', 'latin-1', 'gb18030', 'big5']
                    file_content = None
                    
                    for encoding in encoding_list:
                        try:
                            with open(csv_file, 'r', encoding=encoding) as f:
                                file_content = f.readlines()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if not file_content:
                        print(f"无法解码文件: {csv_file}")
                        continue
                    
                    # 解析文件内容
                    for line in file_content:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 检查是否仍在元数据部分
                        if in_metadata and ',' in line:
                            key, value = line.split(',', 1)
                            metadata[key.strip()] = value.strip()
                        else:
                            # 如果没有逗号，可能已经到了信号数据部分
                            try:
                                # 尝试将行转换为浮点数
                                value = float(line)
                                signal_data.append(value)
                                in_metadata = False  # 标记已进入信号数据部分
                            except ValueError:
                                # 如果不是浮点数，可能仍在元数据部分但格式不同
                                pass
                    
                    # 提取关键元数据
                    date = None
                    classification = None
                    device = None
                    sampling_rate = None
                    
                    # 尝试提取日期
                    date_keys = ['記錄日期', '记录日期', 'Date']
                    for key in date_keys:
                        if key in metadata:
                            try:
                                # 尝试解析各种可能的日期格式
                                date_str = metadata[key]
                                # 处理可能包含时区的日期字符串
                                if ' -' in date_str or ' +' in date_str:
                                    # 示例: "2025-04-02 11:38:52 -0400"
                                    date = pd.to_datetime(date_str, errors='coerce')
                                else:
                                    date = pd.to_datetime(date_str, errors='coerce')
                            except:
                                pass
                    
                    # 尝试提取分类
                    class_keys = ['分類', '分类', 'Classification']
                    for key in class_keys:
                        if key in metadata:
                            classification = metadata[key]
                    
                    # 尝试提取设备
                    device_keys = ['裝置', '设备', 'Device']
                    for key in device_keys:
                        if key in metadata:
                            device = metadata[key]
                    
                    # 尝试提取采样率
                    rate_keys = ['取樣頻率', '采样频率', 'Sampling Frequency']
                    for key in rate_keys:
                        if key in metadata:
                            try:
                                # 可能的格式: "500 Hz"
                                rate_str = metadata[key].split()[0]
                                sampling_rate = float(rate_str)
                            except:
                                pass
                    
                    # 如果没有找到日期，跳过这个文件
                    if date is None:
                        print(f"文件中没有有效的日期: {csv_file}")
                        continue
                    
                    # 创建记录
                    ecg_record = {
                        'filename': filename,
                        'date': date,
                        'classification': classification,
                        'device': device,
                        'sampling_rate': sampling_rate,
                        'signal': signal_data,
                        'length': len(signal_data)
                    }
                    
                    ecg_data.append(ecg_record)
                    
                except Exception as e:
                    print(f"解析ECG文件时出错 {csv_file}: {str(e)}")
                    continue
            
            if not ecg_data:
                print("没有成功解析任何ECG文件")
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(ecg_data)
            
            # 按日期排序
            df = df.sort_values('date')
            
            print(f"成功解析 {len(df)} 个ECG记录")
            return df
            
        except Exception as e:
            print(f"解析ECG文件时出错: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()