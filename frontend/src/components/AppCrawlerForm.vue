<template>
  <a-form layout="vertical">
    <a-form-item label="职位关键词 (空格分隔)">
      <a-textarea
        v-model:value="params.job_keys_str"
        :rows="2"
        placeholder="如: web Web WEB 前端 全栈 可视化"
      />
    </a-form-item>
    <a-form-item label="黑名单公司 (空格分隔)">
      <a-textarea
        v-model:value="params.black_company_str"
        :rows="2"
        placeholder="如: UMU 外企德科 兴业数金 东软"
      />
    </a-form-item>
    <a-row :gutter="16">
      <a-col :span="8">
        <a-form-item label="最低薪资 MoneyMin (万/月)">
          <a-input-number v-model:value="params.money_min" :min="0" :step="0.1" :precision="1" style="width: 100%" />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="最大距离 MAX_DISTANCE (km)">
          <a-input-number v-model:value="params.max_distance" :min="0" :step="1" style="width: 100%" />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="最大抓取条数 (max_items)">
          <a-input-number v-model:value="params.max_items" :min="1" style="width: 100%" />
        </a-form-item>
      </a-col>
    </a-row>
    <a-row :gutter="16">
      <a-col :span="8">
        <a-form-item label="搜索模式 (is_search)">
          <a-switch v-model:checked="params.is_search" />
        </a-form-item>
      </a-col>
      <a-col :span="8">
        <a-form-item label="新职位列表 (is_new_job_list)">
          <a-switch v-model:checked="params.is_new_job_list" />
        </a-form-item>
      </a-col>
    </a-row>
  </a-form>
</template>

<script setup>
import { ref } from 'vue';

const params = ref({
  job_keys_str: 'web Web WEB 前端 全栈 可视化',
  black_company_str: 'UMU 外企德科 兴业数金 东软',
  money_min: 1.4,
  max_distance: 30,
  max_items: 20,
  is_search: true,
  is_new_job_list: false,
});

defineExpose({
  getParams: () => ({
    job_keys: params.value.job_keys_str.split(/\s+/).filter(Boolean),
    black_company: params.value.black_company_str.split(/\s+/).filter(Boolean),
    money_min: params.value.money_min,
    max_distance: params.value.max_distance,
    max_items: params.value.max_items,
    is_search: params.value.is_search,
    is_new_job_list: params.value.is_new_job_list,
  }),
});
</script>
