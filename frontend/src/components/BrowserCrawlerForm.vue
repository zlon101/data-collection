<template>
  <a-form layout="vertical">
    <a-form-item label="目标网址 (url)">
      <a-input v-model:value="params.url" placeholder="https://..." />
    </a-form-item>

    <a-form-item label="容器选择器 (list_item_selector)">
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
    <a-form-item label="字段配置 (fields)">
      <div v-for="(field, index) in params.fields" :key="index" class="field-row">
        <a-input v-model:value="field.name" placeholder="字段名" style="width: 120px; margin-right: 8px" />
        <a-input v-model:value="field.selector" placeholder="CSS 选择器" style="flex: 1; margin-right: 8px" />
        <a-button danger size="small" @click="removeField(index)">删除</a-button>
      </div>
      <a-button type="dashed" size="small" @click="addField" style="margin-top: 8px">+ 添加字段</a-button>
    </a-form-item>

    <a-divider>详情页抓取</a-divider>

    <a-form-item>
      <a-switch v-model:checked="params.enable_detail" />
      <span style="margin-left: 8px">启用详情页抓取</span>
    </a-form-item>

    <template v-if="params.enable_detail">

      <a-form-item label="详情容器选择器 (detail_container_selector)">
        <a-input v-model:value="params.detail_container_selector" placeholder="如: .article-content" />
      </a-form-item>
      <a-form-item label="详情URL来源">
        <a-select v-model:value="params.detail_url_field" placeholder="选择列表字段中包含详情页链接的字段" allow-clear>
          <a-select-option v-for="f in validListFields" :key="f" :value="f">{{ f }}</a-select-option>
        </a-select>
      </a-form-item>
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="导航模式">
            <a-select v-model:value="params.navigation_mode">
              <a-select-option value="go_back">返回按钮 (go_back)</a-select-option>
              <a-select-option value="new_tab">新标签页 (new_tab)</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="返回等待时间 (秒)">
            <a-input-number v-model:value="params.back_wait_time" :min="0" :step="0.5" style="width: 100%" />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="详情页等待时间 (秒)">
            <a-input-number v-model:value="params.detail_page_wait_time" :min="0" :step="0.5" style="width: 100%" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="最大重试次数">
            <a-input-number v-model:value="params.max_detail_retries" :min="0" :max="10" style="width: 100%" />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="失败继续">
            <a-switch v-model:checked="params.continue_on_error" />
            <span style="margin-left: 8px">单个详情页失败后继续</span>
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="详情字段 (detail_fields)">
        <div v-for="(field, index) in params.detail_fields" :key="index" class="field-row">
          <a-input v-model:value="field.name" placeholder="字段名" style="width: 120px; margin-right: 8px" />
          <a-input v-model:value="field.selector" placeholder="CSS 选择器" style="flex: 1; margin-right: 8px" />
          <a-button danger size="small" @click="removeDetailField(index)">删除</a-button>
        </div>
        <a-button type="dashed" size="small" @click="addDetailField" style="margin-top: 8px">+ 添加详情字段</a-button>
      </a-form-item>
    </template>
  </a-form>
</template>

<script setup>
import { ref, computed } from 'vue';

const params = ref({
  url: '',
  fields: [],
  container_selector: '',
  next_button_selector: '',
  max_pages: 0,
  delay: 3.0,
  output_filename: 'scraped_data.json',
  enable_detail: false,
  detail_fields: [],
  detail_container_selector: '',
  detail_url_field: undefined,
  navigation_mode: 'go_back',
  back_wait_time: 2.0,
  detail_page_wait_time: 2.0,
  max_detail_retries: 2,
  continue_on_error: true,
});

const validListFields = computed(() =>
  params.value.fields.filter(f => f.name && f.selector).map(f => f.name)
);

const addField = () => {
  params.value.fields.push({ name: '', selector: '' });
};

const removeField = (index) => {
  params.value.fields.splice(index, 1);
};

const addDetailField = () => {
  params.value.detail_fields.push({ name: '', selector: '' });
};

const removeDetailField = (index) => {
  params.value.detail_fields.splice(index, 1);
};

defineExpose({
  getParams: () => {
    const fields = {};
    params.value.fields.forEach(f => {
      if (f.name && f.selector) fields[f.name] = f.selector;
    });

    const base = {
      url: params.value.url,
      fields,
      container_selector: params.value.container_selector,
      next_button_selector: params.value.next_button_selector || undefined,
      max_pages: params.value.max_pages,
      delay: params.value.delay,
      output_filename: params.value.output_filename,
    };

    if (params.value.enable_detail) {
      const detailFields = {};
      params.value.detail_fields.forEach(f => {
        if (f.name && f.selector) detailFields[f.name] = f.selector;
      });
      return {
        ...base,
        detail_fields: detailFields,
        detail_container_selector: params.value.detail_container_selector,
        detail_url_field: params.value.detail_url_field,
        detail_url_attribute: params.value.detail_url_attribute || 'href',
        navigation_mode: params.value.navigation_mode,
        back_wait_time: params.value.back_wait_time,
        detail_page_wait_time: params.value.detail_page_wait_time,
        max_detail_retries: params.value.max_detail_retries,
        continue_on_error: params.value.continue_on_error,
      };
    }

    return base;
  },
  loadParams: (data) => {
    params.value.url = data.url || '';
    params.value.container_selector = data.container_selector || '';
    params.value.next_button_selector = data.next_button_selector || '';
    params.value.max_pages = data.max_pages ?? 0;
    params.value.delay = data.delay ?? 3.0;
    params.value.output_filename = data.output_filename || 'scraped_data.json';

    // 恢复列表字段
    params.value.fields = Object.entries(data.fields || {}).map(([name, selector]) => ({
      name, selector,
    }));

    // 恢复详情页配置
    const hasDetail = data.detail_fields && Object.keys(data.detail_fields).length > 0;
    params.value.enable_detail = hasDetail;
    params.value.detail_fields = Object.entries(data.detail_fields || {}).map(([name, selector]) => ({
      name, selector,
    }));
    params.value.detail_container_selector = data.detail_container_selector || '';
    params.value.detail_url_field = data.detail_url_field;
    params.value.detail_url_attribute = data.detail_url_attribute || 'href';
    params.value.navigation_mode = data.navigation_mode || 'go_back';
    params.value.back_wait_time = data.back_wait_time ?? 2.0;
    params.value.detail_page_wait_time = data.detail_page_wait_time ?? 2.0;
    params.value.max_detail_retries = data.max_detail_retries ?? 2;
    params.value.continue_on_error = data.continue_on_error ?? true;
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
