<template>
  <a-form layout="vertical">
    <a-form-item label="目标网址 (url)">
      <a-input v-model:value="params.url" placeholder="https://..." />
    </a-form-item>
    <a-form-item label="字段配置 (fields)">
      <div v-for="(field, index) in params.fields" :key="index" class="field-row">
        <a-input v-model:value="field.name" placeholder="字段名" style="width: 120px; margin-right: 8px" />
        <a-input v-model:value="field.selector" placeholder="CSS 选择器" style="flex: 1; margin-right: 8px" />
        <a-button danger size="small" @click="removeField(index)">删除</a-button>
      </div>
      <a-button type="dashed" size="small" @click="addField" style="margin-top: 8px">+ 添加字段</a-button>
    </a-form-item>
    <a-form-item label="容器选择器 (container_selector)">
      <a-input v-model:value="params.container_selector" placeholder="如: div.item" />
    </a-form-item>
    <a-form-item label="下一页按钮 (next_button_selector，可选)">
      <a-input v-model:value="params.next_button_selector" placeholder="如: .next-page" />
    </a-form-item>
    <a-row :gutter="16">
      <a-col :span="8">
        <a-form-item label="最大页数 (max_pages)">
          <a-input-number v-model:value="params.max_pages" :min="0" style="width: 100%" />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="页面延迟 delay (秒)">
          <a-input-number v-model:value="params.delay" :min="0" :step="0.5" style="width: 100%" />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="保存文件名">
          <a-input v-model:value="params.output_filename" placeholder="scraped_data.json" />
        </a-form-item>
      </a-col>
    </a-row>
  </a-form>
</template>

<script setup>
import { ref } from 'vue';

const params = ref({
  url: '',
  fields: [],
  container_selector: '',
  next_button_selector: '',
  max_pages: 0,
  delay: 3.0,
  output_filename: 'scraped_data.json',
});

const addField = () => {
  params.value.fields.push({ name: '', selector: '' });
};

const removeField = (index) => {
  params.value.fields.splice(index, 1);
};

defineExpose({
  getParams: () => {
    const fields = {};
    params.value.fields.forEach(f => {
      if (f.name && f.selector) fields[f.name] = f.selector;
    });
    return {
      url: params.value.url,
      fields,
      container_selector: params.value.container_selector,
      next_button_selector: params.value.next_button_selector || undefined,
      max_pages: params.value.max_pages,
      delay: params.value.delay,
      output_filename: params.value.output_filename,
    };
  },
  addField,
  removeField,
});
</script>

<style scoped>
.field-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
</style>
