<template>
  <div class="crawler-page">
    <div class="page-header">
      <a-tabs v-model:activeKey="crawlerType" class="inner-tabs">
        <a-tab-pane key="app_uiautomator2" tab="App UI 自动化">
          <AppCrawlerForm ref="appFormRef" />
        </a-tab-pane>
        <a-tab-pane key="browser_playwright" tab="网页抓取">
          <BrowserCrawlerForm ref="browserFormRef" />
        </a-tab-pane>
      </a-tabs>
      <a-button @click="logModalVisible = true" class="log-btn">日志</a-button>
    </div>

    <div style="margin-top: 16px">
      <a-button type="primary" size="large" @click="startCrawl" :disabled="running" :loading="running">
        {{ running ? '采集中...' : '开始采集' }}
      </a-button>
    </div>

    <div v-if="taskId" class="status-panel">
      <h3>采集状态</h3>
      <a-tag :color="statusColor">{{ statusLabel }}</a-tag>
    </div>

    <LogModal v-model:visible="logModalVisible" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import client from '../api/client';
import AppCrawlerForm from '../components/AppCrawlerForm.vue';
import BrowserCrawlerForm from '../components/BrowserCrawlerForm.vue';
import LogModal from '../components/LogModal.vue';

const crawlerType = ref('app_uiautomator2');
const appFormRef = ref(null);
const browserFormRef = ref(null);

const taskId = ref('');
const running = ref(false);
const statusColor = ref('');
const statusLabel = ref('');

const logModalVisible = ref(false);

const startCrawl = async () => {
  statusColor.value = 'blue';
  statusLabel.value = '运行中';
  running.value = true;

  let payload;
  if (crawlerType.value === 'app_uiautomator2') {
    payload = { type: 'app_uiautomator2', params: appFormRef.value.getParams() };
  } else {
    payload = { type: 'browser_playwright', params: browserFormRef.value.getParams() };
  }

  try {
    const res = await client.post('/collector', payload);
    taskId.value = res.task_id;
    statusColor.value = 'green';
    statusLabel.value = '采集完成';
    running.value = false;
  } catch (e) {
    statusColor.value = 'red';
    statusLabel.value = '提交失败: ' + e.message;
    running.value = false;
  }
};
</script>

<style scoped>
.crawler-page {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.inner-tabs {
  flex: 1;
}

.log-btn {
  margin-left: 16px;
  flex-shrink: 0;
}

.status-panel {
  margin-top: 24px;
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.status-panel h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
}
</style>
