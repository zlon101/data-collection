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
        <a-select
          v-model:value="filters.source"
          placeholder="来源"
          style="width: 120px"
          allow-clear
        >
          <a-select-option value="boss">boss</a-select-option>
          <a-select-option value="zhilian">zhilian</a-select-option>
        </a-select>
        <a-input
          v-model:value="filters.date_from"
          placeholder="日期起 (MM-DD)"
          style="width: 140px"
        />
        <span class="count-label">总数: {{ filteredData.length }}</span>
      </a-space>
    </div>

    <a-table
      :columns="columns"
      :data-source="filteredData"
      :loading="loading"
      :pagination="false"
      row-key="unique_key"
    />

    <!-- Job 文件管理弹窗 -->
    <JobFileModal
      v-model:open="fileModalVisible"
      @load-file="loadJobFile"
      @file-deleted="handleFileDeleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue';
import client from '../api/client';
import JobFileModal from '../components/JobFileModal.vue';

// ── 文件管理 ──
const fileModalVisible = ref(false);

const handleFileDeleted = (filename) => {
  if (activeJobFile.value === filename) {
    activeJobFile.value = null;
    fetchJobs();
  }
};

// ── 数据查询 ──
const activeJobFile = ref(null); // 当前查看的文件名

const filters = reactive({
  activity: undefined,
  min_salary: undefined,
  max_distance: undefined,
  source: undefined,
  date_from: undefined, // MM-DD
});

const tableData = ref([]); // 全量数据
const loading = ref(false);

// 前端筛选
const filteredData = computed(() => {
  let result = tableData.value;

  if (filters.activity) {
    result = result.filter((item) => item.活跃度?.includes(filters.activity));
  }

  if (filters.min_salary) {
    result = result.filter(
      (item) => parseSalaryMin(item.薪资, true) >= filters.min_salary,
    );
  }

  if (filters.max_distance) {
    result = result.filter((item) => {
      const dist = parseFloat(item.距离 || 0);
      return !isNaN(dist) && dist <= filters.max_distance;
    });
  }

  if (filters.source) {
    result = result.filter((item) => item.来源 === filters.source);
  }

  if (filters.date_from) {
    // 输入 MM-DD，筛选该日期及之后的数据
    result = result.filter((item) => {
      if (!item.日期) return false;
      const itemDate = item.日期.slice(0, 5);
      return itemDate >= filters.date_from;
    });
  }

  return result;
});

const columns = [
  { title: '公司', dataIndex: '公司', key: '公司', width: 150 },
  { title: '职位', dataIndex: '职位', key: '职位', width: 150 },
  {
    title: '薪资',
    dataIndex: '薪资',
    key: '薪资',
    width: 100,
    sorter: (a, b) => parseSalaryMin(a.薪资) - parseSalaryMin(b.薪资),
  },
  { title: '活跃度', dataIndex: '活跃度', key: '活跃度', width: 150 },
  {
    title: '距离',
    dataIndex: '距离',
    key: '距离',
    width: 80,
    sorter: (a, b) => parseFloat(a.距离 || 0) - parseFloat(b.距离 || 0),
  },
  {
    title: '详细地址',
    dataIndex: '详细地址',
    key: '详细地址',
    width: 200,
    ellipsis: true,
  },
  { title: '来源', dataIndex: '来源', key: '来源', width: 80 },
  { title: '日期', dataIndex: '日期', key: '日期', width: 120 },
];

function parseSalaryMin(salary, isMax = false) {
  if (!salary) return 0;
  const nums = salary.match(/[\d.]+/g);
  if (!nums || nums.length < 2) return 0;
  let val = parseFloat(isMax ? nums[1] : nums[0]);
  return val;
}

const loadJobFile = async (filename) => {
  loading.value = true;
  activeJobFile.value = filename;
  filters.activity = undefined;
  filters.min_salary = undefined;
  filters.max_distance = undefined;
  filters.source = undefined;
  filters.date_from = undefined;
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

const fetchJobs = async () => {
  loading.value = true;
  activeJobFile.value = null;
  try {
    const res = await client.get('/jobs');
    tableData.value = res.items || [];
  } catch (e) {
    console.error('获取招聘数据失败:', e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchJobs();
});
</script>

<style scoped>
.query-page {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.filter-bar {
  margin-bottom: 16px;
}

.count-label {
  margin: 0;
  font-size: 14px;
  color: #666;
}
</style>
