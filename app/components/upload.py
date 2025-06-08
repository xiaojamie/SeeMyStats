import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    session, url_for, current_app
)
from werkzeug.utils import secure_filename
import uuid
import shutil
from app.utils.health_parser import HealthDataParser
import tempfile

bp = Blueprint('upload', __name__, url_prefix='/upload')

# 允许的文件类型
ALLOWED_EXTENSIONS = {'zip', 'xml', 'json', 'csv'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('', methods=('GET', 'POST'))
def upload_file():
    """处理数据文件上传"""
    if request.method == 'POST':
        # 创建一个唯一的上传目录
        unique_id = uuid.uuid4()
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{unique_id}")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 检查文件上传
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            
            if allowed_file(file.filename):
                # 保存文件
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # 处理文件
                try:
                    parser = HealthDataParser()
                    success = False
                    xml_path = None
                    
                    # 如果是ZIP文件，提取XML
                    if filename.endswith('.zip'):
                        xml_path = parser.extract_from_zip(file_path)
                        if xml_path:
                            # 尝试解析XML文件
                            success = parser.parse_xml(xml_path)
                        else:
                            # 如果找不到XML文件，可能是一个导出文件夹的压缩包
                            extract_dir = os.path.join(upload_dir, "extract")
                            os.makedirs(extract_dir, exist_ok=True)
                            
                            try:
                                shutil.unpack_archive(file_path, extract_dir)
                                success = parser.parse_directory(extract_dir)
                                if success:
                                    # 存储解析目录
                                    session['data_dir_path'] = extract_dir
                            except Exception as e:
                                flash(f"解压缩文件夹时出错: {str(e)}")
                    
                    # 如果是XML文件，直接解析
                    elif filename.endswith('.xml'):
                        success = parser.parse_xml(file_path)
                        xml_path = file_path
                    
                    # 如果是JSON或CSV文件
                    elif filename.endswith(('.json', '.csv')):
                        if filename.endswith('.json'):
                            parser.parse_json_files(os.path.dirname(file_path))
                        else:
                            parser.parse_csv_files(os.path.dirname(file_path))
                        success = len(parser.records) > 0
                    
                    if success:
                        # 存储解析器实例的路径，供后续组件使用
                        if xml_path:
                            session['data_file_path'] = xml_path
                        elif not session.get('data_dir_path'):
                            session['data_dir_path'] = upload_dir
                        
                        # 获取可用的数据类型
                        data_types = parser.get_all_data_types()
                        if data_types:
                            flash(f'文件上传并解析成功！识别到{len(data_types)}种数据类型。')
                        else:
                            flash('文件已解析，但未识别到标准的健康数据类型。')
                        
                        # 释放解析器内存
                        parser.clean_up()
                        
                        return redirect(url_for('dashboard.index'))
                    else:
                        flash('无法解析健康数据。请确保您上传了正确的Apple健康导出文件。')
                except Exception as e:
                    flash(f'处理文件时出错：{str(e)}')
            else:
                flash(f'不支持的文件类型：{file.filename}')
        
        # 检查目录上传
        elif 'directory' in request.files and request.files.getlist('directory'):
            files = request.files.getlist('directory')
            if not files:
                flash('没有选择目录或目录为空')
                return redirect(request.url)
            
            try:
                # 保存所有文件，保持目录结构
                for file in files:
                    # 提取文件路径
                    filepath = file.filename
                    if os.path.sep != '/':
                        filepath = filepath.replace('/', os.path.sep)
                    
                    # 创建目标目录
                    target_dir = os.path.join(upload_dir, os.path.dirname(filepath))
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # 保存文件
                    target_path = os.path.join(upload_dir, filepath)
                    file.save(target_path)
                
                # 尝试解析目录
                parser = HealthDataParser()
                success = parser.parse_directory(upload_dir)
                
                if success:
                    # 存储目录路径
                    session['data_dir_path'] = upload_dir
                    
                    # 获取可用的数据类型
                    data_types = parser.get_all_data_types()
                    if data_types:
                        flash(f'目录上传并解析成功！识别到{len(data_types)}种数据类型。')
                    else:
                        flash('目录已解析，但未识别到标准的健康数据类型。')
                    
                    # 释放解析器内存
                    parser.clean_up()
                    
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('无法从上传的目录中解析健康数据。请确保目录包含有效的Apple健康导出文件。')
            except Exception as e:
                flash(f'处理目录时出错：{str(e)}')
        else:
            flash('没有选择文件或目录')
        
        return redirect(request.url)
    
    return render_template('upload.html') 