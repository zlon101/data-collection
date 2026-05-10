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
    <div v-if="logs.length" class="log-viewer">
      <div v-for="(entry, i) in logs" :key="i" class="log-line">
        <span :class="['log-level', entry.level.toLowerCase()]">[{{ entry.level }}]</span>
        <span class="log-msg">{{ entry.message }}</span>
      </div>
    </div>
    <a-empty v-else description="暂无日志" />
  </a-modal>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue';
import client from '../api/client';
import { createEventSource } from '../api/sse';

const props = defineProps({
  taskId: { type: String, default: '' },
});

const visible = defineModel('visible', { type: Boolean, default: false });

const tasks = ref([]);
const selectedTaskId = ref('');
const logs = ref([]);
let es = null;

const fetchTasks = async () => {
  const res = await client.get('/collector/tasks');
  tasks.value = res.data;
};

const handleClose = () => {
  if (es) {
    es.close();
    es = null;
  }
  logs.value = [];
  selectedTaskId.value = '';
};

const onTaskChange = (id) => {
  if (es) {
    es.close();
    es = null;
  }
  logs.value = [];
  if (!id) return;

  es = createEventSource(id, {
    onLog: (entry) => {
      logs.value.push(entry);
    },
    onComplete: () => {},
    onError: (err) => {
      logs.value.push({ level: 'ERROR', message: err.error });
    },
  });
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
  if (es) es.close();
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

.log-line {
  display: flex;
  gap: 8px;
  padding: 2px 0;
}

.log-level {
  font-weight: bold;
  min-width: 50px;
}

.log-level.info { color: #569cd6; }
.log-level.warning { color: #dcdcaa; }
.log-level.error { color: #f44747; }

.log-msg {
  flex: 1;
}
</style>
