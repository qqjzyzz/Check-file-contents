import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from Levenshtein import distance as levenshtein_distance
import jieba

class TextFilter:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            tokenizer=lambda x: list(jieba.cut(x)),
            token_pattern=None  # 设置为 None 以避免警告
        )

    def keyword_filter(self, text1, text2, threshold=0.3):
        """基于关键词的初步筛选"""
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))
        overlap = len(words1.intersection(words2))
        union = len(words1.union(words2))
        similarity = overlap / union if union > 0 else 0
        return similarity

    def tfidf_filter(self, text1, text2):
        """基于TF-IDF的初步筛选"""
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
            similarity = (tfidf_matrix * tfidf_matrix.T).toarray()[0][1]
            return similarity
        except:
            return 0

    def edit_distance_filter(self, text1, text2):
        """基于编辑距离的初步筛选"""
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0
        distance = levenshtein_distance(text1, text2)
        similarity = 1 - (distance / max_len)
        return similarity

    def batch_process(self, texts_with_index, threshold=0.3):
        """批量处理文本列表，返回可能相似的文本对"""
        similar_pairs = {}  # 使用字典存储文本对的最高相似度结果
        total_pairs = len(texts_with_index) * (len(texts_with_index) - 1) // 2
        processed_pairs = 0
        last_progress = -1  # 用于控制进度显示频率
        
        print(f"开始文本初筛，共 {len(texts_with_index)} 条文本...")
        
        # 预处理所有文本的分词结果
        text_words = {}
        for idx, text in texts_with_index:
            text_words[idx] = set(jieba.cut(text))
        
        for i, (idx1, text1) in enumerate(texts_with_index):
            for j, (idx2, text2) in enumerate(texts_with_index[i+1:], i+1):
                # 快速预筛选：如果文本长度差异太大，直接跳过
                len1, len2 = len(text1), len(text2)
                if min(len1, len2) / max(len1, len2) < 0.5:
                    processed_pairs += 1
                    continue
                
                # 快速关键词匹配预筛选
                words1 = text_words[idx1]
                words2 = text_words[idx2]
                overlap = len(words1.intersection(words2))
                if overlap < 2:  # 如果共同词汇太少，直接跳过
                    processed_pairs += 1
                    continue
                
                # 计算详细相似度
                similarities = {
                    'keyword': len(words1.intersection(words2)) / len(words1.union(words2)),
                    'tfidf': self.tfidf_filter(text1, text2),
                    'edit_distance': self.edit_distance_filter(text1, text2)
                }
                
                # 找出最高相似度及其对应的方法
                max_method = max(similarities.items(), key=lambda x: x[1])
                max_similarity = max_method[1]
                best_method = max_method[0]
                
                # 如果最高相似度超过阈值，保存结果
                if max_similarity >= threshold:
                    pair_key = (min(idx1, idx2), max(idx1, idx2))
                    current_result = {
                        'text1': text1,
                        'text2': text2,
                        'index1': idx1,
                        'index2': idx2,
                        'similarity': max_similarity,
                        'method': best_method
                    }
                    
                    # 如果这对文本已经存在，只保留相似度更高的结果
                    if pair_key not in similar_pairs or similar_pairs[pair_key]['similarity'] < max_similarity:
                        similar_pairs[pair_key] = current_result
                
                processed_pairs += 1
                # 每处理5%显示一次进度
                current_progress = int((processed_pairs / total_pairs) * 20)
                if current_progress > last_progress:
                    percent = (processed_pairs / total_pairs) * 100
                    print(f"初筛进度: {percent:.1f}% ({processed_pairs}/{total_pairs})")
                    last_progress = current_progress

        print(f"初筛完成，找到 {len(similar_pairs)} 对相似文本")
        # 将字典转换为列表
        return list(similar_pairs.values())

def main():
    # 测试用例
    texts = [
        "机器学习是人工智能的一个分支",
        "人工智能包含机器学习技术",
        "深度学习是机器学习的一种方法",
        "Python是一门编程语言",
        "编程语言包括Python和Java"
    ]
    
    # 创建过滤器实例
    filter = TextFilter()
    
    # 测试所有方法
    print("使用所有方法进行筛选：")
    results = filter.batch_process(texts, method='all', threshold=0.3)
    
    # 打印结果
    for result in results:
        print(f"\n方法: {result['method']}")
        print(f"文本1: {result['text1']}")
        print(f"文本2: {result['text2']}")
        print(f"相似度: {result['similarity']:.2%}")

if __name__ == "__main__":
    main() 