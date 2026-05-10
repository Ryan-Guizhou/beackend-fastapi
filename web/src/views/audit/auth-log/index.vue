<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import {
  pageAuthLogs,
  type AuthLogInfo,
} from '@/api/system-service'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'

const loading = ref(false)
const dataSource = ref<AuthLogInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '操作人', dataIndex: 'operatorName', key: 'operatorName' },
  { title: '动作类型', dataIndex: 'actionType', key: 'actionType' },
  { title: '对象类型', dataIndex: 'objectType', key: 'objectType' },
  { title: '目标名称', dataIndex: 'targetPartyName', key: 'targetPartyName' },
  { title: '授权描述', dataIndex: 'authDesc', key: 'authDesc' },
  { title: '结果', dataIndex: 'result', key: 'result' },
  { title: '客户端IP', dataIndex: 'clientIp', key: 'clientIp' },
  { title: '操作时间', dataIndex: 'operateTime', key: 'operateTime' },
]

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageAuthLogs(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取授权日志失败')
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
  <div class="auth-log-management">
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="关键字">
          <a-input v-model:value="queryParams.keyword" placeholder="操作人/目标" allow-clear @press-enter="onSearch" />
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
          <template v-if="column.key === 'result'">
            <a-tag :color="record.result === 'success' ? 'success' : 'error'">
              {{ record.result === 'success' ? '成功' : '失败' }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
.auth-log-management {
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
