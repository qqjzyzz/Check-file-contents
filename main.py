import os
import pandas as pd
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from dotenv import load_dotenv
import time
import backoff
from text_filter import TextFilter  # 导入文本过滤器

# 加载环境变量
load_dotenv()

class VectorSearch:
    def __init__(self, collection_name="text_vectors", use_openai=True):
        self.collection_name = collection_name
        self.use_openai = use_openai
        # OpenAI模型维度为1536，Sentence-Transformer模型维度为384
        self.dim = 1536 if use_openai else 384
        self.text_filter = TextFilter()
        
        if use_openai:
            self.client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                base_url=os.getenv('OPENAI_API_BASE')
            )
        else:
            # 初始化Sentence-Transformer模型
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.connect_milvus()
        self.setup_collection()

    def connect_milvus(self):
        """连接到Milvus服务器"""
        try:
            connections.connect(
                alias="default",
                host=os.getenv('MILVUS_HOST', 'localhost'),
                port=os.getenv('MILVUS_PORT', '19530')
            )
            print("Successfully connected to Milvus")
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            raise

    def setup_collection(self):
        """设置Milvus集合"""
        try:
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                return

            # 定义字段
            id_field = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
            text_field = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
            vector_field = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim)
            
            # 创建集合schema
            schema = CollectionSchema(
                fields=[id_field, text_field, vector_field],
                description="Excel text embeddings"
            )
            
            # 创建集合
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                using='default'
            )

            # 创建索引
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            print(f"Collection {self.collection_name} created successfully")
        except Exception as e:
            print(f"Error setting up collection: {e}")
            raise

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_embeddings(self, texts):
        """获取文本向量嵌入"""
        if self.use_openai:
            # 使用OpenAI API
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        else:
            # 使用Sentence-Transformers
            return self.model.encode(texts, convert_to_numpy=True).tolist()

    def process_excel_with_filter(self, excel_path, column_name, filter_threshold=0.3, similarity_threshold=0.9):
        """使用初筛的Excel处理方法"""
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            
            # 检查列是否存在
            if column_name not in df.columns:
                raise ValueError(f"Column {column_name} not found in Excel file")

            # 获取文本列数据，并保留行号（从1开始计数）
            texts_with_index = list(enumerate(df[column_name].astype(str).tolist(), 1))
            
            # 第一步：使用文本过滤器进行初筛
            print(f"开始初筛，共 {len(texts_with_index)} 条文本...")
            potential_pairs = self.text_filter.batch_process(texts_with_index, threshold=filter_threshold)
            
            # 获取需要处理的唯一文本
            unique_texts = set()
            text_to_index = {}  # 用于存储文本到行号的映射
            for pair in potential_pairs:
                unique_texts.add(pair['text1'])
                unique_texts.add(pair['text2'])
                text_to_index[pair['text1']] = pair['index1']
                text_to_index[pair['text2']] = pair['index2']
            
            print(f"初筛后需要处理的文本数量: {len(unique_texts)}/{len(texts_with_index)}")
            
            # 第二步：只对筛选出的文本计算embedding
            print("正在生成文本向量...")
            embeddings_dict = {}
            total_texts = len(unique_texts)
            
            for i, text in enumerate(unique_texts, 1):
                if text not in embeddings_dict:  # 避免重复处理
                    embedding = self.get_embeddings([text])[0]
                    embeddings_dict[text] = embedding
                    print(f"进度: {i}/{total_texts} ({(i/total_texts)*100:.1f}%)")
                    time.sleep(0.5)  # 避免API限制
            
            # 准备插入数据
            texts_to_insert = list(embeddings_dict.keys())
            embeddings_to_insert = [embeddings_dict[text] for text in texts_to_insert]
            
            # 清理旧的collection数据
            if utility.has_collection(self.collection_name):
                self.collection.drop()
                self.setup_collection()
            
            # 插入数据到Milvus
            entities = [
                texts_to_insert,
                embeddings_to_insert
            ]
            self.collection.insert(entities)
            self.collection.flush()
            
            print(f"成功处理 {len(texts_to_insert)} 条文本")
            
            return texts_to_insert, embeddings_to_insert, potential_pairs, text_to_index
            
        except Exception as e:
            print(f"处理Excel文件时出错: {e}")
            raise

    def search_similar(self, query_text, top_k=5):
        """搜索相似文本"""
        try:
            # 获取查询文本的embedding
            query_embedding = self.get_embeddings([query_text])[0]
            
            # 加载集合
            self.collection.load()
            
            # 执行搜索
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text"]
            )
            
            # 返回结果
            similar_texts = []
            for hits in results:
                for hit in hits:
                    similar_texts.append({
                        'text': hit.entity.get('text'),
                        'distance': hit.distance
                    })
            
            return similar_texts
            
        except Exception as e:
            print(f"Error searching similar texts: {e}")
            raise

    def generate_similarity_report(self, texts, embeddings, text_to_index, similarity_threshold=0.9):
        """生成相似度报告"""
        try:
            print("正在生成相似度报告...")
            similar_pairs = []
            processed_pairs = set()  # 用于记录已处理的文本对
            
            # 确保集合存在并已加载
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    if not utility.has_collection(self.collection_name):
                        print("Collection not found, recreating...")
                        self.setup_collection()
                        # 重新插入数据
                        entities = [texts, embeddings]
                        self.collection.insert(entities)
                        self.collection.flush()
                    
                    self.collection.load()
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise
                    print(f"Retry {retry_count}/{max_retries} due to: {e}")
                    time.sleep(1)
            
            # 计算所有文本对之间的相似度
            for i, (text1, emb1) in enumerate(zip(texts, embeddings)):
                try:
                    # 使用Milvus搜索相似文本
                    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
                    results = self.collection.search(
                        data=[emb1],
                        anns_field="embedding",
                        param=search_params,
                        limit=len(texts),
                        output_fields=["text"]
                    )
                    
                    # 处理搜索结果
                    for hits in results:
                        for hit in hits:
                            text2 = hit.entity.get('text')
                            # 跳过自身比较
                            if text1 == text2:
                                continue
                                
                            # 创建一个排序后的文本对作为键，避免重复比较
                            pair_key = tuple(sorted([text1, text2]))
                            if pair_key in processed_pairs:
                                continue
                                
                            # 将L2距离转换为相似度分数（越小越相似）
                            similarity = 1 / (1 + hit.distance)
                            if similarity >= similarity_threshold:
                                similar_pairs.append({
                                    'text1': text1,
                                    'text2': text2,
                                    'index1': text_to_index[text1],
                                    'index2': text_to_index[text2],
                                    'similarity': similarity,
                                    'distance': hit.distance
                                })
                                processed_pairs.add(pair_key)
                    
                    if (i + 1) % 10 == 0:
                        print(f"已处理 {i + 1}/{len(texts)} 条文本")
                except Exception as e:
                    print(f"Error processing text pair {i + 1}: {e}")
                    continue
            
            # 按相似度降序排序
            similar_pairs.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 生成报告
            report_path = 'similarity_report.xlsx'
            df_report = pd.DataFrame(similar_pairs)
            # 添加更多信息到报告中
            df_report['similarity_percentage'] = df_report['similarity'].apply(lambda x: f"{x:.2%}")
            df_report['distance'] = df_report['distance']
            df_report.to_excel(report_path, index=False)
            
            print(f"\n相似度报告已生成: {report_path}")
            print(f"共找到 {len(similar_pairs)} 对相似文本")
            
            return similar_pairs
            
        except Exception as e:
            print(f"Error generating similarity report: {e}")
            raise

def main():
    # 创建.env文件示例
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://openkey.cloud/v1
MILVUS_HOST=localhost
MILVUS_PORT=19530
""")
        print("Created .env file. Please update it with your OpenAI API key")
        return

    # 初始化向量搜索
    vector_search = VectorSearch()
    
    # 使用示例
    print("""
使用示例:
1. 确保更新了.env文件中的OpenAI API密钥
2. 确保Milvus服务器正在运行
3. 调用process_excel_with_filter()处理Excel文件（带初筛）
4. 调用generate_similarity_report()生成相似度报告
5. 调用search_similar()搜索相似文本
""")

if __name__ == "__main__":
    main() 