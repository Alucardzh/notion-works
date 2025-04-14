// API 基础 URL
const API_BASE_URL = 'http://localhost:8000';

// 显示/隐藏加载动画
function toggleLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'flex' : 'none';
}

// 显示错误消息
function showError(message) {
    alert(`错误：${message}`);
}

// 加载数据库列表
async function loadDatabases() {
    try {
        toggleLoading(true);
        const response = await axios.get(`${API_BASE_URL}/databases`);
        const select = document.getElementById('databaseSelect');
        select.innerHTML = '<option value="">选择数据库...</option>';
        response.data.forEach(db => {
            const option = document.createElement('option');
            option.value = db.id;
            option.textContent = db.title;
            select.appendChild(option);
        });
    } catch (error) {
        showError(error.response?.data?.detail || error.message);
    } finally {
        toggleLoading(false);
    }
}

// 加载数据库内容
async function loadDatabaseContent(databaseId) {
    try {
        toggleLoading(true);
        const response = await axios.get(`${API_BASE_URL}/databases/${databaseId}`);
        const contentDiv = document.getElementById('databaseContent');
        contentDiv.innerHTML = '';

        // 更新属性选择器
        updatePropertySelectors(response.data[0]?.properties || {});

        response.data.forEach(page => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            const title = page.properties?.文档名称?.title?.[0]?.plain_text || '未命名';
            
            card.innerHTML = `
                <div class="card-header">
                    <h5 class="card-title mb-0">${title}</h5>
                </div>
                <div class="card-body">
                    <pre class="mb-0"><code>${JSON.stringify(page, null, 2)}</code></pre>
                </div>
            `;
            contentDiv.appendChild(card);
        });
    } catch (error) {
        showError(error.response?.data?.detail || error.message);
    } finally {
        toggleLoading(false);
    }
}

// 更新属性选择器
function updatePropertySelectors(properties) {
    const propertyNames = Object.keys(properties);
    
    // 更新删除属性选择器
    const removeSelect = document.getElementById('propertyToRemove');
    removeSelect.innerHTML = '';
    propertyNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        removeSelect.appendChild(option);
    });
    
    // 更新筛选属性选择器
    const filterSelect = document.getElementById('filterProperty');
    filterSelect.innerHTML = '';
    propertyNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        filterSelect.appendChild(option);
    });
}

// 添加属性
async function addProperty() {
    const databaseId = document.getElementById('databaseSelect').value;
    if (!databaseId) {
        showError('请先选择数据库');
        return;
    }

    const propertyName = document.getElementById('propertyName').value;
    const propertyType = document.getElementById('propertyType').value;
    const defaultValue = document.getElementById('defaultValue').value;

    if (!propertyName) {
        showError('请输入属性名称');
        return;
    }

    try {
        toggleLoading(true);
        await axios.post(`${API_BASE_URL}/databases/property`, {
            database_id: databaseId,
            property_name: propertyName,
            property_type: propertyType,
            default_value: defaultValue || null
        });
        alert('添加属性成功');
        loadDatabaseContent(databaseId);
    } catch (error) {
        showError(error.response?.data?.detail || error.message);
    } finally {
        toggleLoading(false);
    }
}

// 删除属性
async function removeProperty() {
    const databaseId = document.getElementById('databaseSelect').value;
    if (!databaseId) {
        showError('请先选择数据库');
        return;
    }

    const propertyName = document.getElementById('propertyToRemove').value;
    if (!propertyName) {
        showError('请选择要删除的属性');
        return;
    }

    if (!confirm(`确定要删除属性 "${propertyName}" 吗？`)) {
        return;
    }

    try {
        toggleLoading(true);
        await axios.delete(`${API_BASE_URL}/databases/${databaseId}/properties/${propertyName}`);
        alert('删除属性成功');
        loadDatabaseContent(databaseId);
    } catch (error) {
        showError(error.response?.data?.detail || error.message);
    } finally {
        toggleLoading(false);
    }
}

// 筛选数据库
async function filterDatabase() {
    const databaseId = document.getElementById('databaseSelect').value;
    if (!databaseId) {
        showError('请先选择数据库');
        return;
    }

    const filterProp = document.getElementById('filterProperty').value;
    const filterValue = document.getElementById('filterValue').value;
    const filterType = document.getElementById('filterType').value;

    if (!filterProp || !filterValue) {
        showError('请填写完整的筛选条件');
        return;
    }

    try {
        toggleLoading(true);
        const response = await axios.post(`${API_BASE_URL}/databases/filter`, {
            database_id: databaseId,
            filter_property: filterProp,
            filter_value: filterValue,
            filter_type: filterType
        });

        const resultsDiv = document.getElementById('filterResults');
        resultsDiv.innerHTML = '';

        if (response.data.length === 0) {
            resultsDiv.innerHTML = '<div class="alert alert-info">未找到匹配的结果</div>';
            return;
        }

        response.data.forEach(page => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            const title = page.properties?.文档名称?.title?.[0]?.plain_text || '未命名';
            
            card.innerHTML = `
                <div class="card-header">
                    <h5 class="card-title mb-0">${title}</h5>
                </div>
                <div class="card-body">
                    <pre class="mb-0"><code>${JSON.stringify(page, null, 2)}</code></pre>
                </div>
            `;
            resultsDiv.appendChild(card);
        });
    } catch (error) {
        showError(error.response?.data?.detail || error.message);
    } finally {
        toggleLoading(false);
    }
}

// 更新页面
async function updatePages() {
    const databaseId = document.getElementById('databaseSelect').value;
    if (!databaseId) {
        showError('请先选择数据库');
        return;
    }

    const textContent = document.getElementById('updateText').value;
    if (!textContent) {
        showError('请输入要更新的文本内容');
        return;
    }

    try {
        toggleLoading(true);
        const response = await axios.post(`${API_BASE_URL}/databases/update-text`, {
            database_id: databaseId,
            text_content: textContent
        });
        alert(`更新完成！成功更新 ${response.data.success_count} 个页面`);
        loadDatabaseContent(databaseId);
    } catch (error) {
        showError(error.response?.data?.detail || error.message);
    } finally {
        toggleLoading(false);
    }
}

// 监听数据库选择变化
document.getElementById('databaseSelect').addEventListener('change', (e) => {
    if (e.target.value) {
        loadDatabaseContent(e.target.value);
    }
});

// 页面加载完成后加载数据库列表
document.addEventListener('DOMContentLoaded', loadDatabases); 