<template>
  <div class="app-container">
    <header>
      <h1>数据采集与分析工作站</h1>
      <div class="header-controls">
        <select v-model="currentSource" @change="fetchData">
          <option value="wechat">微信公众号</option>
          <option value="web">网页</option>
          <option value="app">APP</option>
        </select>
        <button @click="fetchData">刷新数据</button>
      </div>
    </header>

    <main>
      <section class="stats-grid">
        <div class="card stat-card">
          <h3>文章总数</h3>
          <div class="stat-value">{{ summary.total || 0 }}</div>
        </div>
        <div class="card chart-card">
          <h3>情感倾向分布</h3>
          <div ref="sentimentChart" class="chart"></div>
        </div>
        <div class="card chart-card">
          <h3>核心实体词云</h3>
          <div ref="entityChart" class="chart"></div>
        </div>
      </section>

      <section class="table-section card">
        <h3>文章列表</h3>
        <table>
          <thead>
            <tr>
              <th>标题</th>
              <th>发布时间</th>
              <th>情感</th>
              <th>摘要</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in summary.timeline" :key="item.title">
              <td>{{ item.title }}</td>
              <td>{{ item.publish_date || item.publish_time }}</td>
              <td>
                <span :class="['sentiment-tag', item.sentiment]">
                  {{ item.sentiment }}
                </span>
              </td>
              <td class="summary-text">{{ item.summary }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="files-section grid">
        <div class="card">
          <h3>原始数据 (Raw)</h3>
          <ul>
            <li v-for="file in rawFiles" :key="file.filename">
              {{ file.filename }} ({{ file.size_kb }}KB)
              <button @click="triggerAnalyze(file.filename)">开始分析</button>
            </li>
          </ul>
        </div>
        <div class="card">
          <h3>分析结果 (Analyzed)</h3>
          <ul>
            <li v-for="file in analyzedFiles" :key="file.filename">
              {{ file.filename }} ({{ file.size_kb }}KB)
            </li>
          </ul>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';

const currentSource = ref('wechat');
const summary = ref({ total: 0, timeline: [], sentiment_stats: {}, top_entities: [] });
const rawFiles = ref([]);
const analyzedFiles = ref([]);

const sentimentChart = ref(null);
const entityChart = ref(null);

const fetchData = async () => {
  try {
    const [summaryRes, filesRes] = await Promise.all([
      axios.get(`/api/summary?source=${currentSource.value}`),
      axios.get(`/api/files?source=${currentSource.value}`)
    ]);

    summary.value = summaryRes.data;
    rawFiles.value = filesRes.data.raw;
    analyzedFiles.value = filesRes.data.analyzed;

    nextTick(() => {
      initCharts();
    });
  } catch (error) {
    console.error('Failed to fetch data:', error);
  }
};

const triggerAnalyze = async (filename) => {
  try {
    await axios.post('/api/analyze', {
      filename,
      source: currentSource.value
    });
    alert('分析任务已提交，请稍后刷新查看结果');
  } catch (error) {
    alert('分析提交失败: ' + error.message);
  }
};

const initCharts = () => {
  if (sentimentChart.value) {
    const sChart = echarts.init(sentimentChart.value);
    const sData = Object.entries(summary.value.sentiment_stats).map(([name, value]) => ({ name, value }));
    sChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: '70%',
        data: sData,
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
        }
      }]
    });
  }

  if (entityChart.value) {
    const eChart = echarts.init(entityChart.value);
    eChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: summary.value.top_entities.map(e => e.name), axisLabel: { rotate: 45 } },
      yAxis: { type: 'value' },
      series: [{
        data: summary.value.top_entities.map(e => e.value),
        type: 'bar',
        itemStyle: { color: '#5470c6' }
      }]
    });
  }
};

onMounted(() => {
  fetchData();
});
</script>

<style>
:root {
  --primary: #4f46e5;
  --bg: #f3f4f6;
  --card-bg: #ffffff;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg);
  color: #1f2937;
}

.app-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.stats-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr 2fr 2fr;
  margin-bottom: 2rem;
}

.card {
  background: var(--card-bg);
  padding: 1.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chart {
  height: 300px;
}

.stat-value {
  font-size: 3rem;
  font-weight: bold;
  color: var(--primary);
  text-align: center;
  margin-top: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.sentiment-tag {
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.875rem;
}

.正面 { background: #dcfce7; color: #166534; }
.负面 { background: #fee2e2; color: #991b1b; }
.中性 { background: #f3f4f6; color: #374151; }

.summary-text {
  font-size: 0.875rem;
  color: #4b5563;
  max-width: 400px;
}

button {
  background: var(--primary);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
}

select {
  padding: 0.5rem;
  border-radius: 0.375rem;
  border: 1px solid #d1d5db;
}
</style>
