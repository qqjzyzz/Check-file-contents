from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import pandas as pd
from main import VectorSearch
import os

app = Flask(__name__)
vector_search = VectorSearch()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        
        # 检查文件扩展名
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': '请上传Excel文件(.xlsx或.xls)'})
        
        # 清理旧文件
        upload_dir = 'uploads'
        if os.path.exists(upload_dir):
            for f in os.listdir(upload_dir):
                os.remove(os.path.join(upload_dir, f))
        else:
            os.makedirs(upload_dir)
        
        # 保存上传的文件
        file_path = os.path.join(upload_dir, 'temp.xlsx')
        file.save(file_path)
        
        # 获取列名和阈值
        column_name = request.form.get('column_name', 'text_column')
        filter_threshold = float(request.form.get('filter_threshold', 0.3))
        similarity_threshold = float(request.form.get('similarity_threshold', 0.85))
        
        # 获取总记录数
        try:
            df = pd.read_excel(file_path)
            total_records = len(df)
        except Exception as e:
            return jsonify({'error': f'无法读取Excel文件: {str(e)}'})
        
        # 处理文件
        try:
            texts, embeddings, potential_pairs, text_to_index = vector_search.process_excel_with_filter(
                file_path,
                column_name,
                filter_threshold,
                similarity_threshold
            )
            
            # 生成相似度报告
            similar_pairs = vector_search.generate_similarity_report(texts, embeddings, text_to_index, similarity_threshold)
            
            # 转换结果为前端所需格式
            results = {
                'total_records': total_records,
                'initial_pairs': [
                    {
                        'text1': pair['text1'],
                        'text2': pair['text2'],
                        'index1': pair['index1'],
                        'index2': pair['index2'],
                        'similarity': f"{pair['similarity']:.2%}",
                        'method': pair['method'],
                        'distance': pair.get('distance', 0)
                    }
                    for pair in potential_pairs
                ],
                'final_pairs': [
                    {
                        'text1': pair['text1'],
                        'text2': pair['text2'],
                        'index1': pair['index1'],
                        'index2': pair['index2'],
                        'similarity': f"{pair['similarity']:.2%}",
                        'distance': pair['distance']
                    }
                    for pair in similar_pairs
                ]
            }
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'error': f'处理文件时出错: {str(e)}'})
            
    except Exception as e:
        return jsonify({'error': f'上传文件时出错: {str(e)}'})

@app.route('/download_report')
def download_report():
    try:
        report_type = request.args.get('type', 'all')
        threshold = {
            'all': 0,
            '90': 0.9,
            '80': 0.8,
            '70': 0.7
        }.get(report_type, 0)
        
        # 读取原始报告
        df = pd.read_excel('similarity_report.xlsx')
        
        # 根据阈值筛选
        if threshold > 0:
            df = df[df['similarity'] >= threshold]
        
        # 生成新的报告文件
        filtered_report_path = f'similarity_report_{report_type}.xlsx'
        df.to_excel(filtered_report_path, index=False)
        
        return send_file(
            filtered_report_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'similarity_report_{report_type}.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True) 