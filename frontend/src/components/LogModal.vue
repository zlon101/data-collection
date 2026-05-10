<template>
  <a-modal
    v-model:open="visible"
    title="采集日志"
    width="80%"
    :footer="null"
    @cancel="handleClose"
  >
    <a-select
      v-model:value="selectedTaskId"
      placeholder="选择任务"
      style="width: 100%; margin-bottom: 12px"
      @change="onTaskChange"
    >
      <a-select-option v-for="task in tasks" :key="task.task_id" :value="task.task_id">
        {{ task.task_id }} ({{ task.type }}) - {{ task.status }}
      </a-select-option>
    </a-select>
    <div v-if="logsText" class="log-viewer">
      <pre>{{ logsText }}</pre>
    </div>
    <a-empty v-else description="暂无日志" />
  </a-modal>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue';
import client from '../api/client';

const props = defineProps({
  taskId: { type: String, default: '' },
});

const visible = defineModel('visible', { type: Boolean, default: false });

const tasks = ref([]);
const selectedTaskId = ref('');
const logsText = ref('');
let pollingTimer = null;

const fetchTasks = async () => {
  const res = await client.get('/collector/tasks');
  tasks.value = res;
};

const fetchLogs = async (id) => {
  const res = await client.get(`/collector/logs/${id}`);
  logsText.value = res;
  const task = tasks.value.find(t => t.task_id === id);
  if (task && task.status !== 'running' && task.status !== 'pending') {
    stopPolling();
  }
};

const startPolling = (id) => {
  stopPolling();
  fetchLogs(id);
  pollingTimer = setInterval(() => fetchLogs(id), 1000);
};

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
};

const handleClose = () => {
  stopPolling();
  logsText.value = '';
  selectedTaskId.value = '';
};

const onTaskChange = (id) => {
  stopPolling();
  logsText.value = '';
  if (!id) return;
  startPolling(id);
};

watch(visible, async (val) => {
  if (val) {
    await fetchTasks();
    if (props.taskId) {
      selectedTaskId.value = props.taskId;
      onTaskChange(props.taskId);
    }
  } else {
    handleClose();
  }
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.log-viewer {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Menlo', 'Consolas', monospace;
  font-size: 13px;
}

.log-viewer pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
