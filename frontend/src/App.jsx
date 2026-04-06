import React, { useState, useMemo } from 'react';
import { Table, Input, Select, InputNumber, Space, Button, message, Checkbox } from 'antd'; // 新增 Button, message
import 'antd/dist/reset.css';
import jobData from '../data_json/merged_data_new.json';
import { excludeCompany, seenUniqueKey } from './config'


function App() {
  const [salaryFilterValue, setMinSalary] = useState('1.4');
  const [activityFilter, setActivityFilter] = useState('分钟|日');
  const [maxDistance, setMaxDistance] = useState('18');
  const [companySearch, setCompanySearch] = useState('');
  const [platform, setPlatform] = useState('');
  const [showLietou, setLieTou] = useState(true)
  // 新增：日期筛选状态
  const [minDate, setMinDate] = useState('');
  // 新增：选中行的 Key
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 100,
  });

  // 解析薪资，提取最低薪资（单位：万元）
  const parseSalary = (salaryStr) => {
    if (!salaryStr) return 0;
    let [min, max] = `${salaryStr}`.split('-').map(v => parseFloat(v));
    min = Number.isNaN(min) ? 0 : min
    max = Number.isNaN(max) ? 0 : max
    return { min, max }
  };

  // 解析距离，提取数值（单位：千米）
  const parseDistance = (distanceStr) => {
    if (!distanceStr) return 0;
    const match = distanceStr.match(/(\d+\.?\d*)/);
    return match ? parseFloat(match[1]) : 0;
  };

  // 筛选数据
  const filteredData = useMemo(() => {
    return jobData.filter(item => {

      if (item['公司'] && excludeCompany.some(black => item['公司'].includes(black))) {
        return false
      }
      if (!showLietou && item['公司'].includes('客户公司')) {
        return false
      }
      if (seenUniqueKey.includes(item.unique_key)) {
        return false
      }
      // 薪资筛选
      if (salaryFilterValue) {
        const { min: minVal, max: maxVal } = parseSalary(salaryFilterValue)
        const salary = parseSalary(item.薪资);
        if (!(salary.max >= minVal)) return false;
      }

      // 活跃度筛选（支持 | 分隔的多条件）
      if (activityFilter) {
        const patterns = activityFilter.split('|').map(p => p.trim()).filter(p => p);
        if (patterns.length > 0) {
          if (!item.活跃度) return false; // 防止 item.活跃度 为空报错
          const matched = patterns.some(pattern => item.活跃度.includes(pattern));
          if (!matched) return false;
        }
      }

      // 距离筛选
      if (maxDistance !== '' && maxDistance !== null) {
        const distance = parseDistance(item.距离);
        if (distance > maxDistance) return false;
      }

      // 公司名称搜索
      if (companySearch) {
        if (!item.公司 || !item.公司.includes(companySearch)) return false;
      }

      // 平台筛选
      if (platform && item['来源'] !== platform) {
        return false;
      }

      // 新增：日期筛选 (筛选该时间之后的数据)
      // 格式：03-02 14:19:13。字符串直接比较即可
      if (minDate) {
        if (!item['日期']) return false; // 如果没有日期，通常认为不满足筛选条件
        const a1 = minDate.includes(':') ? minDate : `${minDate} 00:00:00`
        if (item['日期'] <= a1) return false;
      }

      return true;
    });
  }, [salaryFilterValue, activityFilter, maxDistance, companySearch, platform, minDate, showLietou]); // 添加 minDate 依赖

  const handleTableChange = (newPagination, filters, sorter) => {
    setPagination(newPagination);
  };

  // 新增：保存功能
  const handleSave = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择需要保存的数据');
      return;
    }

    const dataStr = JSON.stringify(selectedRowKeys, null, 2);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(dataStr);
      return true;
    } else {
      alert('error')
    }

    // const blob = new Blob([dataStr], { type: "application/json" });
    // const url = URL.createObjectURL(blob);

    // // 创建隐藏的 a 标签触发下载
    // const link = document.createElement('a');
    // link.href = url;
    // link.download = "已经查看过的职位.json";
    // document.body.appendChild(link);
    // link.click();

    // // 清理
    // document.body.removeChild(link);
    // URL.revokeObjectURL(url);
    message.success(`已保存 ${selectedRowKeys.length} 条数据`);
  };

  // 处理复选框变化
  const onSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
    preserveSelectedRowKeys: true, // 翻页保留选中状态
  };

  const columns = [
    {
      title: '序号',
      key: 'index',
      width: 80,
      render: (text, record, index) => {
        return (pagination.current - 1) * pagination.pageSize + index + 1;
      },
    },
    {
      title: '职位',
      dataIndex: '职位',
      key: '职位',
      width: 200,
    },
    {
      title: '薪资',
      dataIndex: '薪资',
      key: '薪资',
      width: 180,
      sorter: (a, b) => parseSalary(a.薪资).min - parseSalary(b.薪资).min,
    },
    {
      title: '公司',
      dataIndex: '公司',
      key: '公司',
      width: 180,
    },
    {
      title: '距离',
      dataIndex: '距离',
      key: '距离',
      width: 160,
      sorter: (a, b) => parseDistance(a.距离) - parseDistance(b.距离),
    },
    {
      title: '活跃度',
      dataIndex: '活跃度',
      key: '活跃度',
      width: 220,
    },
    {
      title: '详细地址',
      dataIndex: '详细地址',
      key: '详细地址',
      width: 280,
    },
    {
      title: '来源',
      dataIndex: '来源',
      key: '来源',
      width: 80,
    },
    {
      title: '日期',
      dataIndex: '日期',
      key: '日期',
      width: 180,
      // 默认排序：descend (降序)
      defaultSortOrder: 'descend',
      sorter: (a, b) => {
        // 处理空值：空值视为最小字符串
        const dateA = a['日期'] || '';
        const dateB = b['日期'] || '';
        return dateA.localeCompare(dateB);
      },
    },
  ];

  const onDebug = (e) => {
    setLieTou(e.target.checked)
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space style={{ marginBottom: 16 }} wrap>
        <span>最低薪资(万元)：</span>
        <InputNumber
          placeholder="例如：1.5"
          value={salaryFilterValue}
          onChange={setMinSalary}
          min={0}
          step={0.1}
          style={{ width: 80 }}
        />

        <span>活跃度：</span>
        <Input
          placeholder='例如：分钟|今日'
          value={activityFilter}
          onChange={e => setActivityFilter(e.target.value)}
          style={{ width: 150 }}
        />

        <span>最大距离(千米)：</span>
        <InputNumber
          placeholder="例如：20"
          value={maxDistance}
          onChange={setMaxDistance}
          min={0}
          step={0.1}
          style={{ width: 80 }}
        />

        {/*
        <span>公司名称：</span>
        <Input
          placeholder="公司名称模糊搜索"
          value={companySearch}
          onChange={e => setCompanySearch(e.target.value)}
          style={{ width: 150 }}
        /> */}

        <span>平台：</span>
        <Select
          placeholder="选择平台"
          options={[{ label: '全部', value: '' }, { label: 'BOSS', value: 'boss' }, { label: '智联', value: '智联' }]}
          value={platform}
          onChange={e => setPlatform(e)}
          style={{ width: 100 }}
        />

        {/* 新增日期筛选输入 */}
        <span>起始日期：</span>
        <Input
          placeholder="例如：03-02"
          value={minDate}
          onChange={e => setMinDate(e.target.value)}
          style={{ width: 180 }}
          allowClear
        />

        <span>显示猎头 {showLietou}:</span>
        <Checkbox checked={showLietou} onChange={e => setLieTou(e.target.checked)} />

        {/* 新增保存按钮 */}
        <Button type="primary" onClick={handleSave}>
          复制选中 ({selectedRowKeys.length})
        </Button>
      </Space>

      <div>共 {filteredData.length} 条</div>
      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey={(record) => record.unique_key}
        // 新增：复选框配置
        rowSelection={rowSelection} 
        pagination={{
          ...pagination,
          total: filteredData.length,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
        onChange={handleTableChange}
        scroll={{ x: 1200 }}
      />
    </div>
  );
}

export default App;