<template>
  <div class="crawler-page">
    <div class="page-header">
      <a-tabs v-model:activeKey="crawlerType" class="inner-tabs">
        <a-tab-pane key="app_uiautomator2" tab="App UI 自动化">
          <a-tabs v-model:activeKey="appType" class="app-sub-tabs" type="card">
            <a-tab-pane key="boss" tab="Boss">
              <BossForm ref="bossFormRef" />
            </a-tab-pane>
            <a-tab-pane key="zhilian" tab="智联">
              <ZhilianForm ref="zhilianFormRef" />
            </a-tab-pane>
          </a-tabs>
        </a-tab-pane>
        <a-tab-pane key="browser_playwright" tab="网页抓取">
          <div class="browser-crawler-section">
            <ConfigSelector
              type="browser_playwright"
              v-model:configName="browserConfigName"
              :configs="browserConfigs"
              @load="loadConfig"
              @delete="deleteConfig"
            />
            <BrowserCrawlerForm ref="browserFormRef" />
          </div>
        </a-tab-pane>
      </a-tabs>
      <div class="action-btns">
        <a-button @click="saveConfig" :disabled="running">保存</a-button>
        <a-button @click="logModalVisible = true" :disabled="!taskId" class="log-btn">日志</a-button>
      </div>
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

    <LogModal v-model:visible="logModalVisible" :task-id="taskId" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import client from '../api/client';
import BossForm from '../components/BossForm.vue';
import ZhilianForm from '../components/ZhilianForm.vue';
import BrowserCrawlerForm from '../components/BrowserCrawlerForm.vue';
import ConfigSelector from '../components/ConfigSelector.vue';
import LogModal from '../components/LogModal.vue';

const crawlerType = ref('app_uiautomator2');
const appType = ref('boss');
const bossFormRef = ref(null);
const zhilianFormRef = ref(null);
const browserFormRef = ref(null);

const taskId = ref('');
const running = ref(false);
const statusColor = ref('');
const statusLabel = ref('');

const logModalVisible = ref(false);

// 网页抓取配置管理
const browserConfigName = ref('');
const browserConfigs = ref([]);

const loadBrowserConfigs = async () => {
  try {
    const res = await client.get('/collector/configs');
    browserConfigs.value = res.configs || [];
  } catch (e) {
    // 静默失败
  }
};

const loadConfig = async (name) => {
  try {
    const res = await client.get(`/collector/config/${name}`);
    browserFormRef.value?.loadParams(res.params);
    message.success(`已加载配置: ${name}`);
  } catch (e) {
    message.error('加载配置失败: ' + e.message);
  }
};

const deleteConfig = async (name) => {
  try {
    await client.delete(`/collector/config/${name}`);
    if (browserConfigName.value === name) {
      browserConfigName.value = '';
    }
    await loadBrowserConfigs();
    message.success(`配置已删除: ${name}`);
  } catch (e) {
    message.error('删除配置失败: ' + e.message);
  }
};

onMounted(() => {
  loadBrowserConfigs();
});

const getActiveFormRef = () => {
  if (crawlerType.value === 'app_uiautomator2') {
    return appType.value === 'boss' ? bossFormRef : zhilianFormRef;
  }
  return browserFormRef;
};

const startCrawl = async () => {
  statusColor.value = 'blue';
  statusLabel.value = '运行中';
  running.value = true;

  let payload;
  if (crawlerType.value === 'app_uiautomator2') {
    payload = { type: 'app_uiautomator2', params: getActiveFormRef().value.getParams() };
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

const saveConfig = async () => {
  const formRef = getActiveFormRef();
  const params = formRef.value.getParams();
  let configName;
  if (crawlerType.value === 'browser_playwright') {
    configName = browserConfigName.value;
    if (!configName) {
      message.warning('请输入配置名');
      return;
    }
  } else {
    configName = params.app_type || crawlerType.value;
  }
  try {
    await client.post(`/collector/config?config_name=${configName}`, params);
    message.success(`配置已保存: ${configName}`);
    // 刷新配置列表
    if (crawlerType.value === 'browser_playwright') {
      await loadBrowserConfigs();
    }
  } catch (e) {
    message.error('保存失败: ' + e.message);
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

.app-sub-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}

.browser-crawler-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-btns {
  display: flex;
  gap: 8px;
  margin-left: 16px;
  flex-shrink: 0;
}

.log-btn {
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
