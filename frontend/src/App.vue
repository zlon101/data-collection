<template>
  <a-layout class="app-layout" style="min-height: 100vh">
    <a-tabs v-model:activeKey="currentKey" type="card" class="nav-tabs">
      <a-tab-pane key="crawler" tab="爬虫" />
      <a-tab-pane key="query" tab="查询" />
    </a-tabs>
    <a-layout-content class="content">
      <Crawler v-if="currentKey === 'crawler'" />
      <Query v-if="currentKey === 'query'" />
    </a-layout-content>
  </a-layout>
</template>

<script setup>
import { ref } from 'vue';
import Crawler from './views/Crawler.vue';
import Query from './views/Query.vue';

const currentKey = ref('crawler');
</script>

<style>
.app-layout .header {
  display: flex;
  align-items: center;
  padding: 0 24px;
    background: #001529;
}

.header .title {
  color: #fff;
  font-size: 18px;
  margin: 0;
}

.app-layout .nav-tabs {
  padding: 0 16px;
  background: #fff;
}

.app-layout .content {
  padding: 24px;
  background: #f0f2f5;
  margin: 0 16px 16px 16px;
  border-radius: 8px;
}
</style>
