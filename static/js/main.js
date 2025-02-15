// 全局变量
let initialData = [];
let finalData = [];
let currentInitialPage = 1;
let currentFinalPage = 1;
let similarityChart = null;
let methodChart = null;

// 初始化事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 监听滑块值变化
    document.getElementById('filter_threshold').addEventListener('input', function(e) {
        document.getElementById('filter_threshold_value').textContent = e.target.value;
    });

    document.getElementById('similarity_threshold').addEventListener('input', function(e) {
        document.getElementById('similarity_threshold_value').textContent = e.target.value;
    });

    // 监听页面大小变化
    document.getElementById('initialPageSize').addEventListener('change', function() {
        currentInitialPage = 1;
        updateInitialTable();
    });

    document.getElementById('finalPageSize').addEventListener('change', function() {
        currentFinalPage = 1;
        updateFinalTable();
    });

    // 监听搜索框
    document.getElementById('initialSearch').addEventListener('input', function() {
        currentInitialPage = 1;
        updateInitialTable();
    });

    document.getElementById('finalSearch').addEventListener('input', function() {
        currentFinalPage = 1;
        updateFinalTable();
    });
});

// 更新进度条
function updateProgress(percent, text) {
    document.getElementById('progressBar').style.width = `${percent}%`;
    document.getElementById('progressText').textContent = text;
}

// 显示/隐藏加载动画
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
    updateProgress(0, '准备中...');
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 获取相似度样式类
function getSimilarityClass(similarity) {
    const value = parseFloat(similarity);
    if (value >= 0.9) return 'similarity-high';
    if (value >= 0.7) return 'similarity-medium';
    return 'similarity-low';
}

// 表格排序函数
function sortTable(tableType, column) {
    const data = tableType === 'initial' ? initialData : finalData;
    const currentOrder = data.sortOrder || 'asc';
    const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
    
    data.sort((a, b) => {
        let valueA = a[column];
        let valueB = b[column];
        
        // 处理相似度的百分比字符串
        if (column === 'similarity') {
            valueA = parseFloat(valueA);
            valueB = parseFloat(valueB);
        }
        
        if (currentOrder === 'asc') {
            return valueA > valueB ? 1 : -1;
        } else {
            return valueA < valueB ? 1 : -1;
        }
    });
    
    data.sortOrder = newOrder;
    
    if (tableType === 'initial') {
        initialData = data;
        updateInitialTable();
    } else {
        finalData = data;
        updateFinalTable();
    }
}

// 生成分页按钮
function generatePagination(currentPage, totalPages, onPageChange) {
    const pagination = [];
    
    // 添加"上一页"按钮
    pagination.push(`
        <button class="btn btn-outline-secondary btn-sm ${currentPage === 1 ? 'disabled' : ''}"
                onclick="${currentPage > 1 ? `${onPageChange}(${currentPage - 1})` : ''}">&laquo;</button>
    `);
    
    // 添加页码按钮
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            pagination.push(`
                <button class="btn btn-outline-secondary btn-sm ${i === currentPage ? 'active' : ''}"
                        onclick="${onPageChange}(${i})">${i}</button>
            `);
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            pagination.push(`<button class="btn btn-outline-secondary btn-sm disabled">...</button>`);
        }
    }
    
    // 添加"下一页"按钮
    pagination.push(`
        <button class="btn btn-outline-secondary btn-sm ${currentPage === totalPages ? 'disabled' : ''}"
                onclick="${currentPage < totalPages ? `${onPageChange}(${currentPage + 1})` : ''}">&raquo;</button>
    `);
    
    return pagination.join('');
}

// 更新初筛结果表格
function updateInitialTable() {
    const pageSize = parseInt(document.getElementById('initialPageSize').value);
    const searchText = document.getElementById('initialSearch').value.toLowerCase();
    
    // 过滤数据
    const filteredData = initialData.filter(item => 
        item.text1.toLowerCase().includes(searchText) ||
        item.text2.toLowerCase().includes(searchText) ||
        item.index1.toString().includes(searchText) ||
        item.index2.toString().includes(searchText)
    );
    
    // 计算分页
    const totalPages = Math.ceil(filteredData.length / pageSize);
    const start = (currentInitialPage - 1) * pageSize;
    const end = start + pageSize;
    const pageData = filteredData.slice(start, end);
    
    // 更新表格内容
    const tbody = document.getElementById('initialResultsBody');
    tbody.innerHTML = pageData.map(pair => `
        <tr>
            <td>${pair.index1}</td>
            <td>${pair.text1}</td>
            <td>${pair.index2}</td>
            <td>${pair.text2}</td>
            <td class="${getSimilarityClass(pair.similarity)}">${pair.similarity}</td>
            <td>${pair.distance.toFixed(4)}</td>
            <td>${pair.method}</td>
        </tr>
    `).join('');
    
    // 更新分页按钮
    document.getElementById('initialPagination').innerHTML = generatePagination(
        currentInitialPage,
        totalPages,
        'setInitialPage'
    );
    
    // 更新分页信息
    document.getElementById('initialPageInfo').textContent = 
        `显示 ${start + 1} 到 ${Math.min(end, filteredData.length)} 条，共 ${filteredData.length} 条`;
}

// 更新最终结果表格
function updateFinalTable() {
    const pageSize = parseInt(document.getElementById('finalPageSize').value);
    const searchText = document.getElementById('finalSearch').value.toLowerCase();
    
    // 过滤数据
    const filteredData = finalData.filter(item => 
        item.text1.toLowerCase().includes(searchText) ||
        item.text2.toLowerCase().includes(searchText) ||
        item.index1.toString().includes(searchText) ||
        item.index2.toString().includes(searchText)
    );
    
    // 计算分页
    const totalPages = Math.ceil(filteredData.length / pageSize);
    const start = (currentFinalPage - 1) * pageSize;
    const end = start + pageSize;
    const pageData = filteredData.slice(start, end);
    
    // 更新表格内容
    const tbody = document.getElementById('finalResultsBody');
    tbody.innerHTML = pageData.map(pair => `
        <tr>
            <td>${pair.index1}</td>
            <td>${pair.text1}</td>
            <td>${pair.index2}</td>
            <td>${pair.text2}</td>
            <td class="${getSimilarityClass(pair.similarity)}">${pair.similarity}</td>
            <td>${pair.distance.toFixed(4)}</td>
        </tr>
    `).join('');
    
    // 更新分页按钮
    document.getElementById('finalPagination').innerHTML = generatePagination(
        currentFinalPage,
        totalPages,
        'setFinalPage'
    );
    
    // 更新分页信息
    document.getElementById('finalPageInfo').textContent = 
        `显示 ${start + 1} 到 ${Math.min(end, filteredData.length)} 条，共 ${filteredData.length} 条`;
}

// 设置当前页码
function setInitialPage(page) {
    currentInitialPage = page;
    updateInitialTable();
}

function setFinalPage(page) {
    currentFinalPage = page;
    updateFinalTable();
}

// 更新统计信息
function updateStatistics(data) {
    // 更新数字统计
    document.getElementById('totalRecords').textContent = data.total_records;
    document.getElementById('initialPairs').textContent = data.initial_pairs.length;
    document.getElementById('finalPairs').textContent = data.final_pairs.length;
    document.getElementById('highSimilarityPairs').textContent = 
        data.final_pairs.filter(p => parseFloat(p.similarity) >= 0.9).length;
    
    // 更新相似度分布图表
    updateSimilarityChart(data.final_pairs);
    
    // 更新方法分布图表
    updateMethodChart(data.initial_pairs);
    
    // 显示统计面板
    document.getElementById('statistics').classList.remove('d-none');
}

// 更新相似度分布图表
function updateSimilarityChart(pairs) {
    const ctx = document.getElementById('similarityChart').getContext('2d');
    
    // 计算相似度分布
    const distribution = {
        '90-100%': 0,
        '80-90%': 0,
        '70-80%': 0,
        '< 70%': 0
    };
    
    pairs.forEach(pair => {
        const similarity = parseFloat(pair.similarity);
        if (similarity >= 0.9) distribution['90-100%']++;
        else if (similarity >= 0.8) distribution['80-90%']++;
        else if (similarity >= 0.7) distribution['70-80%']++;
        else distribution['< 70%']++;
    });
    
    if (similarityChart) {
        similarityChart.destroy();
    }
    
    similarityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(distribution),
            datasets: [{
                label: '相似度分布',
                data: Object.values(distribution),
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',  // 绿色
                    'rgba(255, 193, 7, 0.8)',  // 黄色
                    'rgba(255, 143, 0, 0.8)',  // 橙色
                    'rgba(220, 53, 69, 0.8)'   // 红色
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '相似度分布'
                }
            }
        }
    });
}

// 更新方法分布图表
function updateMethodChart(pairs) {
    const ctx = document.getElementById('methodChart').getContext('2d');
    
    // 计算方法分布
    const distribution = {
        'keyword': 0,
        'tfidf': 0,
        'edit_distance': 0
    };
    
    pairs.forEach(pair => {
        distribution[pair.method]++;
    });
    
    if (methodChart) {
        methodChart.destroy();
    }
    
    methodChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['关键词匹配', 'TF-IDF', '编辑距离'],
            datasets: [{
                data: Object.values(distribution),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '初筛方法分布'
                }
            }
        }
    });
}

// 处理表单提交
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    showLoading();

    const formData = new FormData(this);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 保存数据到全局变量
        initialData = data.initial_pairs;
        finalData = data.final_pairs;
        
        // 更新统计信息
        updateStatistics(data);

        // 显示初筛结果
        document.getElementById('initialResults').classList.remove('d-none');
        currentInitialPage = 1;
        updateInitialTable();

        // 显示最终结果
        document.getElementById('finalResults').classList.remove('d-none');
        currentFinalPage = 1;
        updateFinalTable();

    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: '错误',
            text: error.message
        });
    } finally {
        hideLoading();
    }
}); 