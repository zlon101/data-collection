<template>
  <div class="query-page">
    <div class="filter-bar">
      <a-space>
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
      </a-space>
    </div>

    <p>总数: {{ tableData.length }}</p>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import client from '../api/client';

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

const fetchJobs = async () => {
  loading.value = true;
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
