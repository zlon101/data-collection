<template>
  <a-modal
    v-model:open="visible"
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
          <span style="cursor: pointer;" @click="handleLoadFile(record.filename)">{{ record.filename }}</span>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-popconfirm
              v-if="!record.filename.startsWith('merged_data')"
              title="确认删除该文件？"
              ok-text="删除"
              cancel-text="取消"
              @confirm="handleDeleteFile(record.filename)"
            >
              <a-button type="link" danger size="small">删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
  </a-modal>
</template>

<script setup>
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import client from '../api/client';

const props = defineProps({
  open: { type: Boolean, default: false },
});

const emit = defineEmits(['update:open', 'load-file', 'file-deleted']);

const visible = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
});

const fileList = ref([]);
const fileLoading = ref(false);
const merging = ref(false);

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

const handleDeleteFile = async (filename) => {
  try {
    await client.delete(`/job/files/${filename}`);
    message.success(`文件已删除: ${filename}`);
    emit('file-deleted', filename);
    await fetchFiles();
  } catch (e) {
    message.error('删除失败: ' + (e.response?.data?.detail || e.message));
  }
};

const mergeFiles = async () => {
  merging.value = true;
  try {
    const res = await client.post('/job/merge');
    message.success(`合并完成: ${res.output_file}`);
    await fetchFiles();
    emit('load-file', res.output_file);
  } catch (e) {
    message.error('合并失败: ' + (e.response?.data?.detail || e.message));
  } finally {
    merging.value = false;
  }
};

const handleLoadFile = (filename) => {
  visible.value = false;
  emit('load-file', filename);
};

defineExpose({ fetchFiles });
</script>

<style scoped>
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
</style>
