<template>
  <div class="config-selector">
    <a-select
      v-model:value="selectedConfigName"
      show-search
      placeholder="选择或输入配置名"
      :options="dynamicOptions"
      :filter-option="filterOption"
      @search="handleSearch"
      @change="handleChange"
      style="flex: 1; min-width: 200px"
      allow-clear
    >
    </a-select>
    <a-popconfirm
      title="确认删除此配置？"
      :disabled="!selectedConfigName || !isExistingConfig"
      @confirm="handleDelete"
    >
      <a-button danger size="small" :disabled="!selectedConfigName || !isExistingConfig" style="margin-left: 8px">
        删除
      </a-button>
    </a-popconfirm>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  type: { type: String, required: true },
  configName: { type: String, default: '' },
  configs: { type: Array, default: () => [] },
});

const emit = defineEmits(['update:configName', 'load', 'delete']);

const selectedConfigName = ref(props.configName);
const searchText = ref('');

watch(() => props.configName, (val) => {
  selectedConfigName.value = val;
});

const isExistingConfig = computed(() =>
  selectedConfigName.value && props.configs.includes(selectedConfigName.value)
);

const dynamicOptions = computed(() => {
  const options = props.configs.map(c => ({ label: c, value: c }));
  // 搜索文本非空且不匹配已有配置时，显示创建新配置选项
  if (searchText.value && !props.configs.includes(searchText.value)) {
    options.push({
      label: `创建新配置: ${searchText.value}`,
      value: searchText.value,
      isCreate: true,
    });
  }
  return options;
});

const filterOption = (input, option) => {
  if (option.isCreate) return true;
  return option.label.toLowerCase().includes(input.toLowerCase());
};

const handleSearch = (value) => {
  searchText.value = value;
};

const handleChange = (value) => {
  emit('update:configName', value || '');
  // 选择已有配置时触发加载
  if (value && props.configs.includes(value)) {
    emit('load', value);
  }
};

const handleDelete = () => {
  if (selectedConfigName.value && props.configs.includes(selectedConfigName.value)) {
    emit('delete', selectedConfigName.value);
  }
};
</script>

<style scoped>
.config-selector {
  display: flex;
  align-items: center;
}
</style>
