<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import {
  pageLoginLogs,
  type LoginLogInfo,
} from '@/api/system-service'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'

const loading = ref(false)
const dataSource = ref<LoginLogInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '用户账号', dataIndex: 'userCode', key: 'userCode' },
  { title: '用户名称', dataIndex: 'userName', key: 'userName' },
  { title: '客户端IP', dataIndex: 'clientIp', key: 'clientIp' },
  { title: '浏览器', dataIndex: 'browser', key: 'browser' },
  { title: '操作系统', dataIndex: 'os', key: 'os' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '消息', dataIndex: 'msg', key: 'msg' },
  { title: '登录时间', dataIndex: 'loginTime', key: 'loginTime' },
]

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageLoginLogs(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取登录日志失败')
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  queryParams.page = 1
  fetchData()
}

const onReset = () => {
  queryParams.keyword = ''
  queryParams.page = 1
  fetchData()
}

const onTableChange = (pagination: any) => {
  queryParams.page = pagination.current
  queryParams.pageSize = pagination.pageSize
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="login-log-management">
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="关键字">
          <a-input v-model:value="queryParams.keyword" placeholder="账号/名称/IP" allow-clear @press-enter="onSearch" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="onSearch">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
            <a-button @click="onReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="{
          current: queryParams.page,
          pageSize: queryParams.pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条`
        }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'success' ? 'success' : 'error'">
              {{ record.status === 'success' ? '成功' : '失败' }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
.login-log-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.search-card {
  border-radius: 8px;
}
.table-card {
  border-radius: 8px;
}
</style>
