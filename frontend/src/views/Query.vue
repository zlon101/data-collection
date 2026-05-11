<template>
  <div class="query-page">
    <!-- 数据查询区域 -->
    <div class="filter-bar">
      <a-space>
        <a-button @click="fileModalVisible = true">Job 文件管理</a-button>
        <a-select
          v-model:value="filters.activity"
          placeholder="活跃度"
          style="width: 160px"
          allow-clear
        >
          <a-select-option value="今日活跃">今日活跃</a-select-option>
          <a-select-option value="昨日活跃">昨日活跃</a-select-option>
          <a-select-option value="3日内活跃">3日内活跃</a-select-option>
        </a-select>
        <a-input-number
          v-model:value="filters.min_salary"
          placeholder="最低薪资(千/月)"
          :min="0"
          style="width: 180px"
        />
        <a-input-number
          v-model:value="filters.max_distance"
          placeholder="最大距离(km)"
          :min="0"
          :precision="1"
          style="width: 160px"
        />
        <a-button type="primary" @click="fetchJobs">查询</a-button>
        <a-button @click="resetFilters">重置</a-button>
        <p>总数: {{ tableData.length }}</p>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data-source="tableData"
      :loading="loading"
      :pagination="false"
      row-key="unique_key"
    />

    <a-modal
      v-model:open="detailVisible"
      :title="detailItem?.职位 + ' - ' + detailItem?.公司"
      width="700px"
    >
      <template v-if="detailItem">
        <a-descriptions bordered :column="2" size="small">
          <a-descriptions-item label="薪资">{{ detailItem.薪资 }}</a-descriptions-item>
          <a-descriptions-item label="距离">{{ detailItem.距离 }} km</a-descriptions-item>
          <a-descriptions-item label="活跃度">{{ detailItem.活跃度 }}</a-descriptions-item>
          <a-descriptions-item label="HR">{{ detailItem.HR }}</a-descriptions-item>
          <a-descriptions-item label="详细地址" :span="2">{{ detailItem.详细地址 }}</a-descriptions-item>
          <a-descriptions-item label="日期">{{ detailItem.日期 }}</a-descriptions-item>
          <a-descriptions-item label="来源">{{ detailItem.来源 }}</a-descriptions-item>
          <a-descriptions-item label="职位描述" :span="2">
            <pre class="job-desc">{{ detailItem.职位描述 }}</pre>
          </a-descriptions-item>
        </a-descriptions>
      </template>
    </a-modal>

    <!-- Job 文件管理弹窗 -->
    <a-modal
      v-model:open="fileModalVisible"
      title="Job 文件管理"
      width="800px"
      :footer="null"
    >
      <div class="file-toolbar">
        <a-button type="primary" @click="fetchFiles">刷新</a-button>
        <a-popconfirm
          title="确认合并所有文件？合并后将删除原文件"
          ok-text="确认"
          cancel-text="取消"
          @confirm="mergeFiles"
        >
          <a-button type="primary" danger :loading="merging">合并全部</a-button>
        </a-popconfirm>
        <span class="file-count">共 {{ fileList.length }} 个文件</span>
      </div>
      <a-table
        :columns="fileColumns"
        :data-source="fileList"
        :loading="fileLoading"
        :pagination="false"
        row-key="filename"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'filename'">
            <span style="cursor: pointer;" @click="loadJobFile(record.filename)">{{ record.filename }}</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-popconfirm
                v-if="!record.filename.startsWith('merged_data')"
                title="确认删除该文件？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="deleteFile(record.filename)"
              >
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import client from '../api/client';

// ── 文件管理 ──
const fileList = ref([]);
const fileLoading = ref(false);
const merging = ref(false);
const fileModalVisible = ref(false);

const fileColumns = [
  { title: '文件名', dataIndex: 'filename', key: 'filename', width: 250 },
  { title: '大小', dataIndex: 'size', key: 'size', width: 100, customRender: ({ text }) => text ? (text / 1024).toFixed(1) + ' KB' : '0 B' },
  { title: '修改时间', dataIndex: 'modified', key: 'modified', width: 160 },
  { title: '操作', key: 'action', width: 120 },
];

const fetchFiles = async () => {
  fileLoading.value = true;
  try {
    const res = await client.get('/job/files');
    fileList.value = res.files || [];
  } catch (e) {
    console.error('获取文件列表失败:', e);
  } finally {
    fileLoading.value = false;
  }
};

const deleteFile = async (filename) => {
  try {
    await client.delete(`/job/files/${filename}`);
    message.success(`文件已删除: ${filename}`);
    if (activeJobFile.value === filename) {
      activeJobFile.value = null;
      await fetchJobs();
    }
    await fetchFiles();
  } catch (e) {
    message.error('删除失败: ' + (e.response?.data?.detail || e.message));
  }
};

const mergeFiles = async () => {
  merging.value = true;
  activeJobFile.value = null;
  try {
    const res = await client.post('/job/merge');
    message.success(`合并完成: ${res.output_file}`);
    await fetchFiles();
    // 自动加载合并文件内容
    await loadJobFile(res.output_file);
  } catch (e) {
    message.error('合并失败: ' + (e.response?.data?.detail || e.message));
  } finally {
    merging.value = false;
  }
};

// ── 数据查询 ──
const activeJobFile = ref(null); // 当前查看的文件名

const filters = ref({
  activity: undefined,
  min_salary: undefined,
  max_distance: undefined,
});

const tableData = ref([]);
const loading = ref(false);
const detailVisible = ref(false);
const detailItem = ref(null);

const columns = [
  { title: '公司', dataIndex: '公司', key: '公司', width: 150 },
  { title: '职位', dataIndex: '职位', key: '职位', width: 150 },
  { title: '薪资', dataIndex: '薪资', key: '薪资', width: 100, sorter: (a, b) => parseSalaryMin(a.薪资) - parseSalaryMin(b.薪资) },
  { title: '活跃度', dataIndex: '活跃度', key: '活跃度', width: 150 },
  { title: '距离', dataIndex: '距离', key: '距离', width: 80, sorter: (a, b) => parseFloat(a.距离 || 0) - parseFloat(b.距离 || 0) },
  { title: '详细地址', dataIndex: '详细地址', key: '详细地址', width: 200, ellipsis: true },
  { title: '来源', dataIndex: '来源', key: '来源', width: 80 },
  { title: '日期', dataIndex: '日期', key: '日期', width: 120 },
];

function parseSalaryMin(salary) {
  if (!salary) return 0;
  const nums = salary.match(/[\d.]+/g);
  if (!nums || nums.length < 2) return 0;
  let val = parseFloat(nums[0]);
  if (salary.includes('万')) val *= 10;
  else if (salary.includes('k') || salary.includes('K')) val *= 1;
  else if (salary.includes('元')) val /= 1000;
  return val;
}

const loadJobFile = async (filename) => {
  loading.value = true;
  activeJobFile.value = filename;
  try {
    const res = await client.get(`/job/files/${filename}`);
    tableData.value = res.items || [];
  } catch (e) {
    console.error('加载文件失败:', e);
    tableData.value = [];
  } finally {
    loading.value = false;
  }
};

const fetchJobFiles = async () => {
  if (activeJobFile.value) {
    await loadJobFile(activeJobFile.value);
  } else {
    await fetchJobs();
  }
};

const fetchJobs = async () => {
  loading.value = true;
  activeJobFile.value = null;
  try {
    const params = {};
    if (filters.value.activity) params.activity = filters.value.activity;
    if (filters.value.min_salary) params.min_salary = filters.value.min_salary;
    if (filters.value.max_distance) params.max_distance = filters.value.max_distance;
    const res = await client.get('/jobs', { params });
    tableData.value = res.items || [];
  } catch (e) {
    console.error('获取招聘数据失败:', e);
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.value = {
    activity: undefined,
    min_salary: undefined,
    max_distance: undefined,
  };
  fetchJobs();
};

const showDetail = (record) => {
  detailItem.value = record;
  detailVisible.value = true;
};

onMounted(() => {
  fetchFiles();
  fetchJobs();
});
</script>

<style scoped>
.query-page {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.file-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.file-count {
  margin-left: 8px;
  color: #999;
  font-size: 13px;
}

.filter-bar {
  margin-bottom: 16px;
}

.job-desc {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}
</style>
