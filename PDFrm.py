import sys
import os
sys.setrecursionlimit(5000)
import shutil
import pdfplumber
import re
import time
from datetime import datetime
from charset_normalizer import md__mypyc

# 定义文件名开头与项目代码之间的映射关系
file_categories = {
    'p'     :   'Prep',    
    'prep'  :   'Prep',      
    'blank' :   'Prep',
    'test'  :   'Prep',
}

source_folder = 'source_folder'
destination_folder = 'destination_folder'
data_type = 'LCMS_ZJ'
# 创建一个文件夹，用于存放未知文件
unknown_folder = os.path.join(source_folder, 'Unknown')
#os.makedirs(unknown_folder, exist_ok=True)

#这段代码将整个文件夹中的文件全部改名
def rename_pdf_files(path):
    # 获取目录中的PDF文件列表
    pdf_files = [f for f in os.listdir(path) if f.endswith(".pdf")]

    for pdf_file in pdf_files:
        # 构建完整的PDF文件路径
        pdf_file_path = os.path.join(path, pdf_file)

        pdf_name, extension = os.path.splitext(pdf_file)

        try:
            # 打开PDF文件
            with pdfplumber.open(pdf_file_path) as pdf:
                # 获取第一页的内容
                page = pdf.pages[0]
                text = page.extract_text()
                #print(text)
                # 使用正则表达式提取样本名称
                sample_name_match = re.search(r'Project Name: +(.*?)\n', text)
                if sample_name_match:
                    source_name = sample_name_match.group(1)

                    # 去除非法字符并替换空格为下划线
                    legal_name = re.sub(r'[/*?:<>|\\]', '', source_name).replace('  ', '_')

                    # 构建新文件名
                    new_filename = legal_name + '_' + pdf_file
                    pdf.close()
                    #print (pdf_name)
                    #print (new_filename)
                    # 重命名PDF文件
                    os.rename(pdf_file_path, os.path.join(path, new_filename))
                else:
                    pdf.close()
                    os.rename(pdf_file_path, os.path.join(path, pdf_name + '_NoProjectName.pdf'))
        except Exception as e:
            print(f"Error renaming {pdf_file}: {str(e)}")
            continue  # 继续处理下一个文件

调用函数并传入文件夹路径
rename_pdf_files(source_folder)

##这段代码只修改没有在字典中找到值的文件的文件名
def rename_pdf_file(pdf_file_path):
    pdf_name, extension = os.path.splitext(os.path.basename(pdf_file_path))

    try:
        # 打开PDF文件
        with pdfplumber.open(pdf_file_path) as pdf:
            # 获取第一页的内容
            page = pdf.pages[0]
            text = page.extract_text()
            pdf.close()
            # 使用正则表达式提取样本名称
            project_name_match = re.search(r'Project Name: +(.*?)\n', text)
            sample_name_match = re.search(r'Sample name: +(.*?)\s+', text)
            source_name = project_name_match.group(1)
            sample_name = sample_name_match.group(1)

            # 去除非法字符并替换空格为下划线
            legal_name = re.sub(r'[/*?:<>|\\]', '', source_name).replace('  ', '_')
            sample_name_legal = re.sub(r'[/*?:<>|\\]', '', sample_name).replace('  ', '_')
            
            if source_name:

                # 构建新文件名
                new_filename = f"{legal_name}_{pdf_name}{extension}"
            else:
                # 如果没有找到项目名称，使用默认的文件名
                new_filename = f"NoProject_{pdf_name}{extension}"

            # 构建新的文件路径
            new_file_path = os.path.join(os.path.dirname(pdf_file_path), new_filename)

            # 重命名PDF文件
            
            os.rename(pdf_file_path, new_file_path)

            # 返回新文件的完整路径
        return new_file_path
        
    except Exception as e:
        print(f"Error renaming {pdf_file_path}: {str(e)}")
        # 在报错时返回原文件路径
        return pdf_file_path


# 遍历源文件夹中的所有文件

for filename in os.listdir(source_folder):
    file_path_org = os.path.join(source_folder, filename)
    file_path = file_path_org
    if os.path.isfile(file_path):  # 只处理文件，跳过文件夹
        # 获取文件创建日期
        file_create_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        date_folder = file_create_date.strftime('%Y%m%d')  # 文件日期字符串，用于分类
        
        # 获取文件名开头的项目名称
        match = re.search(r'[^a-zA-Z0-9]',filename)
        if match:
            file_prefix = filename.split(match.group())[0].lower()
        else:
            file_prefix = filename
        #print (file_prefix)
        
        # 查找项目代码对应的文件夹路径
        if file_prefix in file_categories:
            project_folder = os.path.join(destination_folder, file_categories[file_prefix], data_type, date_folder)
        else:

            file_path = rename_pdf_file(file_path_org)
            filename_new = os.path.basename(file_path)
            match_new = re.search(r'[^a-zA-Z0-9]',filename_new)
            # print(filename_new)
            # print(match_new)
            if match_new:
                file_prefix_new = filename_new.split(match_new.group())[0].lower()
                if file_prefix_new in file_categories:
                    project_folder = os.path.join(destination_folder, file_categories[file_prefix_new], data_type, date_folder)
                else:
                    project_folder = os.path.join(unknown_folder, data_type, date_folder)           
            else:
                project_folder = os.path.join(unknown_folder, data_type, date_folder)
       
        # 创建项目文件夹（若不存在）
        os.makedirs(project_folder, exist_ok=True)
        
        new_file_path = os.path.join(project_folder, filename)
        
        # 检查目标文件夹是否已存在同名文件，若存在则加上后缀区别
        if os.path.exists(new_file_path):
            name, ext = os.path.splitext(filename)
            count = 1
            while True:
                new_filename = f"{name}_{count}{ext}"
                new_file_path = os.path.join(project_folder, new_filename)
                if not os.path.exists(new_file_path):
                    break
                count += 1
        
        # 移动文件到目标文件夹
               
        try:
            shutil.move(file_path, new_file_path)
        except PermissionError as e:
            print(f"无法移动文件：{e}")
            # 跳过该文件，继续执行后续操作
            continue  # 继续下一次迭代
