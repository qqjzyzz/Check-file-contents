from main import VectorSearch
import pandas as pd
import os

def create_sample_excel():
    """创建示例Excel文件用于测试"""
    data = {
        'text_column': [
            "机器学习是人工智能的一个子领域",
            "人工智能的分支领域包括机器学习",
            "深度学习是机器学习的一个分支",
            "机器学习是AI领域的重要分支",
            "自然语言处理是AI的重要应用",
            "NLP是人工智能中的自然语言处理技术",
            "计算机视觉在医疗领域有重要应用",
            "医疗影像分析是计算机视觉的应用",
            "强化学习在游戏AI中表现出色",
            "游戏AI经常使用强化学习算法"
        ]
    }
    df = pd.DataFrame(data)
    excel_path = 'sample_data.xlsx'
    df.to_excel(excel_path, index=False)
    return excel_path

def main():
    # 创建示例Excel文件
    excel_path = create_sample_excel()
    print(f"Created sample Excel file: {excel_path}")

    # 初始化向量搜索
    vector_search = VectorSearch()

    # 处理Excel文件（使用初筛）
    print("\n处理Excel文件...")
    texts, embeddings, potential_pairs = vector_search.process_excel_with_filter(
        excel_path, 
        'text_column',
        filter_threshold=0.3,  # 初筛阈值
        similarity_threshold=0.85  # 最终相似度阈值
    )

    # 打印初筛结果
    print("\n初筛发现的潜在相似对：")
    for pair in potential_pairs:
        print(f"\n方法: {pair['method']}")
        print(f"文本1: {pair['text1']}")
        print(f"文本2: {pair['text2']}")
        print(f"初筛相似度: {pair['similarity']:.2%}")

    # 生成最终相似度报告
    print("\n生成最终相似度报告...")
    similar_pairs = vector_search.generate_similarity_report(texts, embeddings, similarity_threshold=0.85)

    # 打印最终结果
    print("\n最终相似度报告（前3对）:")
    for i, pair in enumerate(similar_pairs[:3], 1):
        print(f"\n{i}. 文本对:")
        print(f"   文本1: {pair['text1']}")
        print(f"   文本2: {pair['text2']}")
        print(f"   相似度: {pair['similarity']}")

    # 测试单个文本搜索
    print("\n测试单个文本搜索...")
    query_text = "AI在医疗领域的应用"
    results = vector_search.search_similar(query_text, top_k=3)
    
    print(f"\n查询文本: {query_text}")
    print("相似结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. 文本: {result['text']}")
        print(f"   相似度距离: {result['distance']}\n")

if __name__ == "__main__":
    main() 