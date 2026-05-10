<script setup lang="ts">
import { ref, onMounted, reactive, createVNode } from 'vue'
import {
  pageResources,
  createResource,
  updateResource,
  deleteResource,
  type ResourceInfo,
} from '@/api/system-service'
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

const loading = ref(false)
const dataSource = ref<ResourceInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '资源名称', dataIndex: 'resourceName', key: 'resourceName' },
  { title: '资源编码', dataIndex: 'resourceCode', key: 'resourceCode' },
  { title: '所属功能', dataIndex: 'funcCode', key: 'funcCode' },
  { title: '资源类型', dataIndex: 'resourceType', key: 'resourceType' },
  { title: '资源URL', dataIndex: 'resourceUrl', key: 'resourceUrl' },
  { title: 'HTTP方法', dataIndex: 'httpMethod', key: 'httpMethod' },
  { title: '操作', key: 'action', fixed: 'right', width: 150 },
]

// Modal State
const modalVisible = ref(false)
const modalTitle = ref('新增资源')
const confirmLoading = ref(false)
const formRef = ref<FormInstance>()
const formState = reactive<Partial<ResourceInfo>>({
  id: '',
  resourceName: '',
  resourceCode: '',
  funcCode: '',
  resourceType: 'API',
  resourceUrl: '',
  httpMethod: 'GET',
})

const rules = {
  resourceName: [{ required: true, message: '请输入资源名称' }],
  resourceCode: [{ required: true, message: '请输入资源编码' }],
  resourceType: [{ required: true, message: '请选择资源类型' }],
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageResources(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取资源列表失败')
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

// CRUD Operations
const handleAdd = () => {
  modalTitle.value = '新增资源'
  Object.assign(formState, {
    id: '',
    resourceName: '',
    resourceCode: '',
    funcCode: '',
    resourceType: 'API',
    resourceUrl: '',
    httpMethod: 'GET',
  })
  modalVisible.value = true
}

const handleEdit = (record: ResourceInfo) => {
  modalTitle.value = '编辑资源'
  Object.assign(formState, { ...record })
  modalVisible.value = true
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该资源吗？此操作不可撤销。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteResource(id)
        message.success('删除成功')
        fetchData()
      } catch (error) {
        message.error('删除失败')
      }
    },
  })
}

const handleModalOk = async () => {
  try {
    await formRef.value?.validateFields()
    confirmLoading.value = true
    
    if (formState.id) {
      await updateResource(formState.id, formState)
      message.success('更新成功')
    } else {
      await createResource(formState)
      message.success('创建成功')
    }
    
    modalVisible.value = false
    fetchData()
  } catch (error) {
    console.error('Validation/API error:', error)
  } finally {
    confirmLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="resource-management">
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="关键字">
          <a-input v-model:value="queryParams.keyword" placeholder="名称/编码" allow-clear @press-enter="onSearch" />
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
      <template #extra>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增资源
        </a-button>
      </template>
      
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
          <template v-if="column.key === 'funcCode'">
            <a-tag color="purple">{{ record.funcCode || '-' }}</a-tag>
          </template>
          <template v-if="column.key === 'resourceType'">
            <a-tag :color="record.resourceType === 'API' ? 'blue' : 'orange'">
              {{ record.resourceType }}
            </a-tag>
          </template>
          <template v-if="column.key === 'httpMethod'">
            <a-tag v-if="record.httpMethod" color="cyan">{{ record.httpMethod }}</a-tag>
            <span v-else>-</span>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Add/Edit Modal -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :confirm-loading="confirmLoading"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item label="资源名称" name="resourceName">
          <a-input v-model:value="formState.resourceName" placeholder="请输入资源名称" />
        </a-form-item>
        <a-form-item label="资源编码" name="resourceCode">
          <a-input v-model:value="formState.resourceCode" placeholder="请输入资源编码" />
        </a-form-item>
        <a-form-item label="所属功能" name="funcCode">
          <a-input v-model:value="formState.funcCode" placeholder="请输入所属功能编码" />
        </a-form-item>
        <a-form-item label="资源类型" name="resourceType">
          <a-select v-model:value="formState.resourceType">
            <a-select-option value="API">API</a-select-option>
            <a-select-option value="BUTTON">BUTTON</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="资源URL" name="resourceUrl">
          <a-input v-model:value="formState.resourceUrl" placeholder="请输入资源URL (可选)" />
        </a-form-item>
        <a-form-item label="HTTP方法" name="httpMethod">
          <a-select v-model:value="formState.httpMethod" placeholder="请选择方法 (可选)" allow-clear>
            <a-select-option value="GET">GET</a-select-option>
            <a-select-option value="POST">POST</a-select-option>
            <a-select-option value="PUT">PUT</a-select-option>
            <a-select-option value="DELETE">DELETE</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.resource-management {
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
